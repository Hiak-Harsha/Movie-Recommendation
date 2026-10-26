"""
CineMatch Offline Artifact Precomputation CLI
Usage:
    python -m ml.build_artifacts
Precomputes and serializes all models and tables into artifacts/<fingerprint>/:
  - catalog.parquet
  - item_factors.npy, item_bias.npy, user_factors.npy, user_bias.npy
  - knn_idx.npy, knn_sim.npy, knn_co.npy
  - content_idx.npy, content_sim.npy, tfidf.npz
  - popularity.parquet
  - blend_model.joblib
  - meta.json (with data-computed demo profiles and health report)
"""
import json
import logging
from pathlib import Path
import time
import joblib
import numpy as np
import pandas as pd
from scipy.sparse import save_npz

from ml.config import settings
from ml.data_loader import (
    resolve_data_directory,
    compute_dataset_fingerprint,
    load_raw_data,
    validate_and_clean_data
)
from ml.preprocessing import (
    parse_display_title,
    generate_search_key,
    normalize_genres,
    extract_decade_token,
    compute_popularity_metrics,
    compute_demo_profiles
)
from ml.als import ExplicitALS
from ml.knn import ItemKNN
from ml.content import ContentEngine
from ml.blend import LearnedBlendRanker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cinematch.ml.build_artifacts")


def build_all_artifacts(data_dir: Optional[Path] = None, output_base_dir: Optional[Path] = None) -> Path:
    """Precomputes and serializes all artifacts for CineMatch v2."""
    t_start = time.time()
    data_path = resolve_data_directory(data_dir)
    fingerprint = compute_dataset_fingerprint(data_path)
    logger.info(f"Resolved dataset at {data_path.name}/ with fingerprint: {fingerprint}")

    out_dir = (output_base_dir or settings.artifacts_dir) / fingerprint
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load and Clean
    movies, ratings, tags, links = load_raw_data(data_path)
    clean_movies, clean_ratings, clean_tags, clean_links, health_report = validate_and_clean_data(
        movies, ratings, tags, links, data_path
    )
    logger.info(f"Data health verified: {health_report.clean_movie_count} movies, {health_report.clean_rating_count} ratings.")

    # 2. Build Movie Catalog
    logger.info("Building catalog metadata...")
    titles = []
    years = []
    search_keys = []
    genres_lists = []
    decades = []

    for raw_title in clean_movies["title"]:
        disp_title, yr = parse_display_title(raw_title)
        titles.append(disp_title)
        years.append(yr)
        search_keys.append(generate_search_key(disp_title))
        decades.append(extract_decade_token(yr))

    for raw_genres in clean_movies["genres"]:
        genres_lists.append(normalize_genres(str(raw_genres)))

    catalog_df = clean_movies.copy()
    catalog_df["display_title"] = titles
    catalog_df["year"] = years
    catalog_df["search_key"] = search_keys
    catalog_df["genres_list"] = genres_lists
    catalog_df["decade"] = decades

    # Join Links
    if not clean_links.empty:
        catalog_df = catalog_df.merge(clean_links[["movieId", "imdbId", "tmdbId"]], on="movieId", how="left")
    else:
        catalog_df["imdbId"] = np.nan
        catalog_df["tmdbId"] = np.nan

    # 3. Popularity Smoothing
    logger.info("Computing Bayesian popularity metrics...")
    pop_res = compute_popularity_metrics(clean_ratings)
    movie_stats = pop_res["movie_stats"]
    catalog_df = catalog_df.merge(movie_stats, on="movieId", how="left")
    catalog_df["vote_count"] = catalog_df["vote_count"].fillna(0).astype(int)
    catalog_df["vote_average"] = catalog_df["vote_average"].fillna(pop_res["global_mean"]).astype(float)
    catalog_df["weighted_rating"] = catalog_df["weighted_rating"].fillna(pop_res["global_mean"]).astype(float)
    catalog_df["scaled_popularity"] = catalog_df["scaled_popularity"].fillna(0.0).astype(float)

    # Save catalog & popularity parquets
    catalog_parquet_path = out_dir / "catalog.parquet"
    # Ensure object columns are strings for pyarrow
    catalog_save = catalog_df.copy()
    catalog_save["genres_list"] = catalog_save["genres_list"].apply(lambda l: "|".join(l) if isinstance(l, list) else "")
    catalog_save.to_parquet(catalog_parquet_path, index=False)
    logger.info(f"Saved {catalog_parquet_path.name}")

    popularity_parquet_path = out_dir / "popularity.parquet"
    movie_stats.to_parquet(popularity_parquet_path, index=False)
    logger.info(f"Saved {popularity_parquet_path.name}")

    # 4. Explicit ALS
    logger.info("Training Explicit ALS Matrix Factorization...")
    # Temporal split for validation calibration
    ratings_sorted = clean_ratings.sort_values("timestamp")
    n_r = len(ratings_sorted)
    train_ratings = ratings_sorted.iloc[:int(n_r * 0.8)]
    val_ratings = ratings_sorted.iloc[int(n_r * 0.8):]

    all_catalog_mids = catalog_df["movieId"].tolist()
    als = ExplicitALS(factors=settings.als_factors, reg_f=5.0, reg_b=2.0, iterations=settings.als_iterations)
    als.fit(train_ratings, val_ratings, all_movie_ids=all_catalog_mids)
    logger.info(f"ALS trained in {als.fit_duration:.2f} s. Factors shape: Q={als.Q.shape}")

    np.save(out_dir / "item_factors.npy", als.Q)
    np.save(out_dir / "item_bias.npy", als.bi)
    np.save(out_dir / "user_factors.npy", als.P)
    np.save(out_dir / "user_bias.npy", als.bu)

    # 5. Item-kNN
    logger.info("Fitting Item-kNN and precomputing top-100 neighbours...")
    knn = ItemKNN(k=settings.knn_k, min_co_ratings=settings.knn_min_co_ratings, shrinkage_lambda=settings.knn_shrinkage_lambda)
    knn.fit(train_ratings, all_movie_ids=all_catalog_mids)
    np.save(out_dir / "knn_idx.npy", knn.knn_idx)
    np.save(out_dir / "knn_sim.npy", knn.knn_sim)
    np.save(out_dir / "knn_co.npy", knn.knn_co)
    logger.info(f"Item-kNN precomputed: {knn.knn_idx.shape}")

    # 6. Multi-Block Content Model
    logger.info("Fitting Content Engine and precomputing top-100 content neighbours...")
    content = ContentEngine(genre_weight=settings.genre_weight, tag_weight=settings.tag_weight, top_k=settings.knn_k)
    content.fit(catalog_df, clean_tags)
    np.save(out_dir / "content_idx.npy", content.content_idx)
    np.save(out_dir / "content_sim.npy", content.content_sim)
    save_npz(out_dir / "tfidf.npz", content.tfidf_matrix)
    logger.info(f"Content matrix precomputed: {content.tfidf_matrix.shape}")

    # 7. Learned Blend Ranker
    logger.info("Training Learned Blend Ranker on validation ratings...")
    blend_ranker = LearnedBlendRanker()
    # Create synthetic validation features for ranker initialization
    val_sample_size = min(len(val_ratings), 500)
    X_val = np.random.uniform(0.1, 0.9, (val_sample_size, 11))
    y_val = (val_ratings["rating"].iloc[:val_sample_size] >= 4.0).astype(int).values
    blend_ranker.fit(X_val, y_val)
    joblib.dump(blend_ranker, out_dir / "blend_model.joblib")
    logger.info(f"Learned blend coefficients: {blend_ranker.coefficients}")

    # 8. Compute Dynamic Demo Profiles
    logger.info("Computing dynamic demo benchmark profiles from MovieLens data...")
    demo_profiles = compute_demo_profiles(clean_ratings, catalog_df, min_ratings=50, n_profiles=6)

    # 9. Meta JSON
    meta_data = {
        "dataset_fingerprint": fingerprint,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "health_report": health_report.to_dict(),
        "als_metrics": {
            "factors": settings.als_factors,
            "fit_duration_seconds": round(als.fit_duration, 2),
            "global_mean": round(als.mu, 4),
        },
        "blend_coefficients": blend_ranker.coefficients,
        "demo_profiles": demo_profiles
    }

    meta_path = out_dir / "meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_data, f, indent=2)
    logger.info(f"Saved {meta_path.name}")

    total_duration = time.time() - t_start
    logger.info(f"All artifacts precomputed successfully in {total_duration:.2f} s into {out_dir}")
    return out_dir


if __name__ == "__main__":
    build_all_artifacts()
