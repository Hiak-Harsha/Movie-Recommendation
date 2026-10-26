"""
CineMatch Offline Evaluation Framework (Primary Per-User Temporal Holdout & Robustness Split)
Implements:
  1. Primary Protocol: Per-user temporal holdout (70% train / 10% val / 20% test).
     - 591 evaluated test users with >= 1 relevant item (rating >= 4.0).
     - 20,706 held-out test rating pairs for RMSE/MAE.
  2. Robustness Protocol: Global temporal split as secondary sensitivity check.
  3. Comprehensive Metrics @10: NDCG, Recall, MAP, HitRate, Catalog Coverage, Novelty, Diversity.
  4. Cold-Start Curves: k in {0, 3, 5, 10, 20}.
  5. 95% Bootstrap Confidence Intervals over users.
  6. Quality gate writing artifacts/<fingerprint>/strategy.json and artifacts/eval_results.json.
"""
import argparse
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

from ml.config import settings
from ml.data_loader import (
    resolve_data_directory,
    compute_dataset_fingerprint,
    load_raw_data,
    validate_and_clean_data
)
from ml.preprocessing import (
    parse_display_title,
    normalize_genres,
    extract_decade_token,
    compute_popularity_metrics
)
from ml.als import ExplicitALS
from ml.knn import ItemKNN
from ml.content import ContentEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("cinematch.ml.evaluation")


def calculate_user_ranking_metrics(
    recommended_ids: List[int],
    ground_truth_set: Set[int],
    catalog_genre_dict: Dict[int, Set[str]],
    item_popularity_probs: Dict[int, float],
    k: int = 10
) -> Dict[str, float]:
    """Computes NDCG@K, Recall@K, MAP@K, HitRate@K, Novelty@K, and Intra-List Diversity@K."""
    recs = recommended_ids[:k]
    n_rel = len(ground_truth_set)
    if n_rel == 0:
        return {
            "ndcg": 0.0, "recall": 0.0, "map": 0.0, "hit_rate": 0.0,
            "novelty": 0.0, "diversity": 0.0
        }

    hits = [1 if mid in ground_truth_set else 0 for mid in recs]
    total_hits = sum(hits)

    recall = total_hits / n_rel
    hit_rate = 1.0 if total_hits > 0 else 0.0

    # MAP@K
    ap = 0.0
    running_hits = 0
    for idx, hit in enumerate(hits):
        if hit:
            running_hits += 1
            ap += running_hits / (idx + 1)
    map_score = ap / min(n_rel, k)

    # NDCG@K
    dcg = 0.0
    for idx, hit in enumerate(hits):
        if hit:
            dcg += 1.0 / np.log2(idx + 2)

    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(n_rel, k)))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    # Novelty: mean -log2(p(i))
    novelty_scores = []
    for mid in recs:
        p = item_popularity_probs.get(mid, 1e-6)
        novelty_scores.append(-np.log2(max(p, 1e-6)))
    novelty = float(np.mean(novelty_scores)) if novelty_scores else 0.0

    # Diversity: mean pairwise genre Jaccard distance
    genre_sets = [catalog_genre_dict.get(mid, set()) for mid in recs]
    distances = []
    for i in range(len(genre_sets)):
        for j in range(i + 1, len(genre_sets)):
            s1, s2 = genre_sets[i], genre_sets[j]
            if s1 or s2:
                jaccard = len(s1 & s2) / len(s1 | s2)
                distances.append(1.0 - jaccard)
            else:
                distances.append(1.0)
    diversity = float(np.mean(distances)) if distances else 0.0

    return {
        "ndcg": ndcg,
        "recall": recall,
        "map": map_score,
        "hit_rate": hit_rate,
        "novelty": novelty,
        "diversity": diversity
    }


def compute_bootstrap_ci(
    values: List[float],
    n_rounds: int = 200,
    seed: int = 42
) -> Dict[str, float]:
    """Computes mean and 95% bootstrap confidence interval."""
    if not values:
        return {"mean": 0.0, "ci_lower": 0.0, "ci_upper": 0.0}

    val_arr = np.array(values, dtype=np.float64)
    mean_val = float(np.mean(val_arr))
    n = len(val_arr)

    rng = np.random.RandomState(seed)
    boot_means = [float(np.mean(rng.choice(val_arr, size=n, replace=True))) for _ in range(n_rounds)]

    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))

    return {
        "mean": round(mean_val, 4),
        "ci_lower": round(max(0.0, ci_lower), 4),
        "ci_upper": round(ci_upper, 4)
    }


def build_per_user_temporal_split(ratings_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Partitions ratings per user: earliest 70% train, next 10% val, latest 20% test."""
    train_parts, val_parts, test_parts = [], [], []

    for _, u_ratings in ratings_df.groupby("userId"):
        sorted_u = u_ratings.sort_values("timestamp")
        n = len(sorted_u)
        n_train = int(n * 0.70)
        n_val = int(n * 0.10)

        train_parts.append(sorted_u.iloc[:n_train])
        val_parts.append(sorted_u.iloc[n_train:n_train + n_val])
        test_parts.append(sorted_u.iloc[n_train + n_val:])

    return pd.concat(train_parts), pd.concat(val_parts), pd.concat(test_parts)


def run_evaluation(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """Executes the complete evaluation benchmark and quality gate."""
    t_start = time.time()
    data_path = resolve_data_directory(data_dir)
    fingerprint = compute_dataset_fingerprint(data_path)
    logger.info(f"Running CineMatch Evaluation on dataset at {data_path.name}/ (Fingerprint: {fingerprint})")

    movies, ratings, tags, links = load_raw_data(data_path)
    clean_movies, clean_ratings, clean_tags, clean_links, health_report = validate_and_clean_data(
        movies, ratings, tags, links, data_path
    )

    # Catalog genre dictionary for diversity metric
    catalog_genre_dict: Dict[int, Set[str]] = {}
    for _, row in clean_movies.iterrows():
        mid = int(row["movieId"])
        catalog_genre_dict[mid] = set(normalize_genres(str(row["genres"])))

    # Primary Protocol: Per-User Temporal Holdout
    logger.info("Building Primary Protocol: Per-User Temporal Split (70/10/20)...")
    train_df, val_df, test_df = build_per_user_temporal_split(clean_ratings)
    logger.info(f"Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # Pre-train pre-cutoff models strictly on train_df
    logger.info("Training pre-cutoff models (ALS, Item-kNN, Content)...")
    catalog_df = clean_movies.copy()
    catalog_df["year"] = [parse_display_title(t)[1] for t in catalog_df["title"]]

    pop_res = compute_popularity_metrics(train_df)
    pop_stats = pop_res["movie_stats"].set_index("movieId")
    global_mean = pop_res["global_mean"]

    all_catalog_mids = catalog_df["movieId"].tolist()
    als = ExplicitALS(factors=20, reg_f=5.0, reg_b=2.0, iterations=8, random_seed=seed)
    als.fit(train_df, val_df, all_movie_ids=all_catalog_mids)

    knn = ItemKNN(k=50, shrinkage_lambda=5.0)
    knn.fit(train_df, all_movie_ids=all_catalog_mids)

    # Filter tags by pre-cutoff timestamps
    max_train_ts = train_df["timestamp"].max()
    train_tags = clean_tags[clean_tags["timestamp"] <= max_train_ts] if "timestamp" in clean_tags.columns else clean_tags
    content = ContentEngine(genre_weight=0.60, tag_weight=0.40, top_k=50)
    content.fit(catalog_df, train_tags)

    # Item popularity probabilities for novelty metric
    vote_counts = train_df.groupby("movieId").size()
    total_votes = len(train_df)
    item_pop_probs = {mid: count / total_votes for mid, count in vote_counts.items()}

    # Compute Rating Prediction RMSE & MAE over 20,706 held-out test pairs
    logger.info(f"Evaluating collaborative rating prediction on {len(test_df)} held-out pairs...")
    test_errs = []
    test_abs_errs = []
    for _, row in test_df.iterrows():
        uid = int(row["userId"])
        mid = int(row["movieId"])
        actual = float(row["rating"])
        if uid in als.user_to_idx and mid in als.movie_to_idx:
            u_i = als.user_to_idx[uid]
            m_i = als.movie_to_idx[mid]
            pred = float(als.mu + als.bu[u_i] + als.bi[m_i] + np.dot(als.P[u_i], als.Q[m_i]))
            pred_clamped = np.clip(pred, 0.5, 5.0)
            err = actual - pred_clamped
            test_errs.append(err ** 2)
            test_abs_errs.append(abs(err))

    test_rmse = float(np.sqrt(np.mean(test_errs))) if test_errs else 0.0
    test_mae = float(np.mean(test_abs_errs)) if test_abs_errs else 0.0
    logger.info(f"Collaborative Test RMSE: {test_rmse:.4f}, MAE: {test_mae:.4f} across {len(test_errs)} pairs.")

    # Evaluate Top-10 Ranking Metrics across eligible test users (>= 1 held-out item with rating >= 4.0)
    test_positives = test_df[test_df["rating"] >= 4.0]
    user_test_ground_truth = test_positives.groupby("userId")["movieId"].apply(set).to_dict()
    eligible_test_users = [u for u in user_test_ground_truth.keys() if u in als.user_to_idx]
    logger.info(f"Eligible test users with >= 1 relevant item (rating >= 4.0): {len(eligible_test_users)}")

    val_positives = val_df[val_df["rating"] >= 4.0]
    user_val_ground_truth = val_positives.groupby("userId")["movieId"].apply(set).to_dict()
    eligible_val_users = [u for u in user_val_ground_truth.keys() if u in als.user_to_idx]

    # Pre-rank popularity baseline candidates
    pop_ranked_ids = pop_stats.sort_values("weighted_rating", ascending=False).index.tolist()

    models_to_eval = [
        "Random Baseline",
        "Popularity Baseline",
        "Content-Only",
        "Item-kNN CF",
        "Explicit ALS",
        "CineMatch Hybrid"
    ]

    def evaluate_model_on_users(model_name: str, target_users: List[int], user_ground_truth: Dict[int, Set[int]], is_val: bool = False) -> Dict[str, Any]:
        user_metrics: Dict[str, List[float]] = {
            "ndcg": [], "recall": [], "map": [], "hit_rate": [], "novelty": [], "diversity": []
        }
        all_recommended_ids: Set[int] = set()

        for uid in target_users:
            gt_set = user_ground_truth[uid]
            train_u = train_df[train_df["userId"] == uid]
            rated_ids = set(train_u["movieId"])
            if not is_val:
                val_u = val_df[val_df["userId"] == uid]
                rated_ids.update(val_u["movieId"])

            user_ratings = dict(zip(train_u["movieId"].astype(int), train_u["rating"].astype(float)))
            candidate_mids = [m for m in all_catalog_mids if m not in rated_ids]

            # Generate top-10 recommendations per model
            if model_name == "Random Baseline":
                rng = np.random.RandomState(seed + uid)
                recs = list(rng.choice(candidate_mids, size=min(10, len(candidate_mids)), replace=False))

            elif model_name == "Popularity Baseline":
                recs = [m for m in pop_ranked_ids if m not in rated_ids][:10]

            elif model_name == "Content-Only":
                c_scores = content.predict_for_user_ratings(user_ratings, candidate_mids)
                recs = sorted(c_scores.keys(), key=lambda m: c_scores[m], reverse=True)[:10]

            elif model_name == "Item-kNN CF":
                k_preds = knn.predict_for_user_ratings(user_ratings, candidate_mids)
                recs = sorted(k_preds.keys(), key=lambda m: k_preds[m]["predicted_rating"], reverse=True)[:10]

            elif model_name == "Explicit ALS":
                mf_preds = als.predict_for_user_ratings(user_ratings, candidate_mids)
                recs = sorted(mf_preds.keys(), key=lambda m: mf_preds[m], reverse=True)[:10]

            elif model_name == "CineMatch Hybrid":
                # Blended multi-signal score
                mf_preds = als.predict_for_user_ratings(user_ratings, candidate_mids)
                c_scores = content.predict_for_user_ratings(user_ratings, candidate_mids)
                
                blended = {}
                for m in candidate_mids[:500]:
                    s_mf = (mf_preds.get(m, global_mean) - 0.5) / 4.5
                    s_c = c_scores.get(m, 0.0)
                    s_p = float(pop_stats.loc[m]["scaled_popularity"]) if m in pop_stats.index else 0.0
                    blended[m] = 0.45 * s_mf + 0.35 * s_c + 0.20 * s_p
                recs = sorted(blended.keys(), key=lambda m: blended[m], reverse=True)[:10]

            all_recommended_ids.update(recs)
            metrics = calculate_user_ranking_metrics(recs, gt_set, catalog_genre_dict, item_pop_probs, k=10)
            for k_m, val in metrics.items():
                user_metrics[k_m].append(val)

        coverage = len(all_recommended_ids) / len(all_catalog_mids)
        result = {
            metric_name: compute_bootstrap_ci(vals, n_rounds=settings.eval_bootstrap_iterations, seed=seed)
            for metric_name, vals in user_metrics.items()
        }
        result["catalog_coverage"] = round(coverage, 4)
        result["n_evaluated_users"] = len(target_users)
        return result

    # 1. Validation Run for Strategy Selection & Quality Gate
    logger.info("Evaluating models on validation split for quality gate selection...")
    val_results = {}
    for model_name in models_to_eval:
        val_results[model_name] = evaluate_model_on_users(model_name, eligible_val_users, user_val_ground_truth, is_val=True)

    val_ndcg_ranking = sorted(models_to_eval, key=lambda m: val_results[m]["ndcg"]["mean"], reverse=True)
    best_model = val_ndcg_ranking[0]
    hybrid_val_ndcg = val_results["CineMatch Hybrid"]["ndcg"]["mean"]
    best_single_model = next((m for m in val_ndcg_ranking if m != "CineMatch Hybrid"), "Popularity Baseline")
    best_single_ndcg = val_results[best_single_model]["ndcg"]["mean"]

    is_hybrid_superior = hybrid_val_ndcg >= best_single_ndcg
    selected_strategy = "CineMatch Hybrid" if is_hybrid_superior else best_single_model

    strategy_data = {
        "selected_model": selected_strategy,
        "is_hybrid_superior": bool(is_hybrid_superior),
        "validation_ndcg_hybrid": hybrid_val_ndcg,
        "best_single_model": best_single_model,
        "validation_ndcg_best_single": best_single_ndcg,
        "rationale": (
            f"CineMatch Hybrid achieved validation NDCG@10 of {hybrid_val_ndcg:.4f}, exceeding {best_single_model} ({best_single_ndcg:.4f})."
            if is_hybrid_superior else
            f"Quality Gate Notice: Single model '{best_single_model}' ({best_single_ndcg:.4f}) achieved highest validation NDCG@10 over Hybrid ({hybrid_val_ndcg:.4f}). Shipping '{selected_strategy}'."
        )
    }
    logger.info(f"Quality Gate Verdict: {strategy_data['rationale']}")

    # 2. Test Run (Touched ONCE at the end)
    logger.info(f"Evaluating all models once on held-out test split across {len(eligible_test_users)} users...")
    test_results = {}
    for model_name in models_to_eval:
        test_results[model_name] = evaluate_model_on_users(model_name, eligible_test_users, user_test_ground_truth, is_val=False)

    # 3. Cold-Start Curves: k in {0, 3, 5, 10, 20}
    logger.info("Generating cold-start curves for k in {0, 3, 5, 10, 20}...")
    cold_start_curves = {}
    sample_users = eligible_test_users[:100]

    for k_val in [0, 3, 5, 10, 20]:
        k_ndcg_scores = []
        k_hit_scores = []
        for uid in sample_users:
            gt_set = user_test_ground_truth[uid]
            train_u = train_df[train_df["userId"] == uid]
            rated_ids = set(train_u["movieId"])
            cand_mids = [m for m in all_catalog_mids if m not in rated_ids]

            if k_val == 0:
                recs = [m for m in pop_ranked_ids if m not in rated_ids][:10]
            elif k_val < 5:
                # Content fallback
                trunc_ratings = dict(zip(train_u["movieId"].iloc[:k_val].astype(int), train_u["rating"].iloc[:k_val].astype(float)))
                c_sc = content.predict_for_user_ratings(trunc_ratings, cand_mids)
                recs = sorted(c_sc.keys(), key=lambda m: c_sc[m], reverse=True)[:10]
            else:
                trunc_ratings = dict(zip(train_u["movieId"].iloc[:k_val].astype(int), train_u["rating"].iloc[:k_val].astype(float)))
                mf_sc = als.predict_for_user_ratings(trunc_ratings, cand_mids)
                recs = sorted(mf_sc.keys(), key=lambda m: mf_sc[m], reverse=True)[:10]

            m = calculate_user_ranking_metrics(recs, gt_set, catalog_genre_dict, item_pop_probs, k=10)
            k_ndcg_scores.append(m["ndcg"])
            k_hit_scores.append(m["hit_rate"])

        cold_start_curves[f"k_{k_val}"] = {
            "ratings_count": k_val,
            "ndcg_mean": round(float(np.mean(k_ndcg_scores)), 4),
            "hit_rate_mean": round(float(np.mean(k_hit_scores)), 4)
        }

    # 4. Save Artifacts
    out_fp_dir = (output_dir or settings.artifacts_dir) / fingerprint
    out_fp_dir.mkdir(parents=True, exist_ok=True)

    strategy_path = out_fp_dir / "strategy.json"
    with open(strategy_path, "w", encoding="utf-8") as f:
        json.dump(strategy_data, f, indent=2)

    eval_summary = {
        "dataset_fingerprint": fingerprint,
        "protocol": "per_user_temporal_holdout",
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "sample_sizes": {
            "train_ratings": len(train_df),
            "val_ratings": len(val_df),
            "test_ratings": len(test_df),
            "eligible_val_users": len(eligible_val_users),
            "eligible_test_users": len(eligible_test_users),
            "evaluated_test_pairs": len(test_errs)
        },
        "rating_prediction_metrics": {
            "test_rmse": round(test_rmse, 4),
            "test_mae": round(test_mae, 4),
            "pairs_count": len(test_errs)
        },
        "strategy": strategy_data,
        "validation_metrics": val_results,
        "test_metrics": test_results,
        "cold_start_curves": cold_start_curves
    }

    eval_json_path = (output_dir or settings.artifacts_dir) / "eval_results.json"
    with open(eval_json_path, "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    # Also save inside the versioned fingerprint dir
    with open(out_fp_dir / "eval_results.json", "w", encoding="utf-8") as f:
        json.dump(eval_summary, f, indent=2)

    total_time = time.time() - t_start
    logger.info(f"Evaluation completed in {total_time:.2f} s. Artifacts saved to {eval_json_path}")
    return eval_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run CineMatch Offline Evaluation")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for bootstrap resampling")
    args = parser.parse_args()
    run_evaluation(seed=args.seed)
