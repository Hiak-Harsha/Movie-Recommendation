"""
CineMatch Offline Evaluation Framework & CLI
Implements:
  - Global temporal train (70%) / validation (10%) / test (20%) split.
  - Zero-leakage training: future ratings and future tags strictly excluded.
  - Ranking metrics @ 10: Precision, Recall, NDCG, MAP, HitRate, Catalog Coverage.
  - Rating prediction metrics: RMSE and MAE on observed test pairs.
  - 95% Bootstrap Confidence Intervals across test users.
  - Quality Gate: selects model by validation NDCG@10.
  - Saves results to artifacts/eval_results.json.
"""
import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

import config
from src.data_loader import load_raw_data, validate_and_clean_data, compute_dataset_fingerprint
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender
from src.collaborative_model import ItemKNNRecommender, BiasedMFRecommender, CollaborativeEngine
from src.hybrid_model import HybridRecommender

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def calculate_ranking_metrics_single_user(
    recommended_ids: List[int],
    ground_truth_set: Set[int],
    k: int = 10
) -> Dict[str, float]:
    """
    Computes Precision@K, Recall@K, NDCG@K, MAP@K, and HitRate@K for a single user.
    """
    recs = recommended_ids[:k]
    n_rel = len(ground_truth_set)
    if n_rel == 0:
        return {"precision": 0.0, "recall": 0.0, "ndcg": 0.0, "map": 0.0, "hit_rate": 0.0}

    hits = [1 if mid in ground_truth_set else 0 for mid in recs]
    total_hits = sum(hits)

    # Precision & Recall
    precision = total_hits / k
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
            dcg += 1.0 / np.log2(idx + 2)  # idx+2 since 1-indexed: log2(1+1)=log2(2)=1

    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(n_rel, k)))
    ndcg = (dcg / idcg) if idcg > 0 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "ndcg": ndcg,
        "map": map_score,
        "hit_rate": hit_rate,
    }


def compute_bootstrap_ci(
    values: List[float],
    n_rounds: int = config.BOOTSTRAP_ROUNDS,
    seed: int = config.RANDOM_SEED
) -> Tuple[float, float, float]:
    """
    Computes mean and 95% bootstrap confidence interval (2.5% and 97.5% percentiles).
    Returns (mean, ci_lower, ci_upper).
    """
    if not values:
        return 0.0, 0.0, 0.0

    val_arr = np.array(values, dtype=np.float64)
    mean_val = float(np.mean(val_arr))
    n = len(val_arr)

    rng = np.random.RandomState(seed)
    boot_means = []
    for _ in range(n_rounds):
        sample = rng.choice(val_arr, size=n, replace=True)
        boot_means.append(np.mean(sample))

    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return round(mean_val, 4), round(ci_lower, 4), round(ci_upper, 4)


def temporal_split_data(
    ratings_df: pd.DataFrame,
    train_ratio: float = config.EVAL_TRAIN_RATIO,
    val_ratio: float = config.EVAL_VAL_RATIO
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int, int]:
    """
    Splits ratings globally by timestamp into Train, Validation, and Test sets.
    Computes exact boundary cutoff timestamps.
    """
    sorted_df = ratings_df.sort_values(by="timestamp").reset_index(drop=True)
    n = len(sorted_df)

    train_end = int(round(n * train_ratio))
    val_end = int(round(n * (train_ratio + val_ratio)))

    train_df = sorted_df.iloc[:train_end].copy()
    val_df = sorted_df.iloc[train_end:val_end].copy()
    test_df = sorted_df.iloc[val_end:].copy()

    val_cutoff_ts = int(train_df["timestamp"].max()) if not train_df.empty else 0
    test_cutoff_ts = int(val_df["timestamp"].max()) if not val_df.empty else val_cutoff_ts

    return train_df, val_df, test_df, val_cutoff_ts, test_cutoff_ts


def run_evaluation_pipeline(
    data_dir: Optional[str | Path] = None,
    protocol: str = "temporal",
    seed: int = config.RANDOM_SEED,
    sample_users: Optional[int] = 50
) -> Dict[str, Any]:
    """
    Executes complete offline evaluation pipeline across baselines and models.
    Produces artifacts/eval_results.json with quality gate selection.
    """
    logging.info(f"Starting evaluation pipeline with protocol='{protocol}', seed={seed}")
    
    # 1. Ingest Data
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data(data_dir)
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    fingerprint = report.dataset_fingerprint

    # 2. Split Data
    train_ratings, val_ratings, test_ratings, val_cutoff, test_cutoff = temporal_split_data(
        ratings_clean,
        train_ratio=config.EVAL_TRAIN_RATIO,
        val_ratio=config.EVAL_VAL_RATIO
    )
    logging.info(f"Split sizes: Train={len(train_ratings):,}, Val={len(val_ratings):,}, Test={len(test_ratings):,}")
    logging.info(f"Cutoff timestamps: Val={val_cutoff}, Test={test_cutoff}")

    # 3. Fit Models on Train Data ONLY (Zero-Leakage)
    # Popularity stats from train ratings
    pop_train_df, global_mean, m_threshold = compute_popularity_metrics(train_ratings)
    # Tags strictly before train cutoff
    catalog_train = build_movie_catalog(
        movies_clean,
        tags_df=tags_clean,
        popularity_df=pop_train_df,
        links_df=links_clean,
        max_tag_timestamp=val_cutoff
    )

    logging.info("Fitting models on training split...")
    content_model = ContentRecommender().fit(catalog_train)
    collab_engine = CollaborativeEngine().fit(train_ratings)
    hybrid_model = HybridRecommender(content_model, collab_engine, catalog_train)

    # 4. User Eligibility and Candidate Definitions
    # Relevant item: rating >= 4.0
    def get_user_splits(eval_df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        user_data = {}
        for uid, grp in eval_df.groupby("userId"):
            uid_int = int(uid)
            train_items = set(train_ratings[train_ratings["userId"] == uid_int]["movieId"].astype(int))
            if len(train_items) < config.MIN_USER_RATINGS_EVAL:
                continue
            pos_items = set(grp[grp["rating"] >= config.RELEVANCE_RATING_THRESHOLD]["movieId"].astype(int))
            if pos_items:
                user_data[uid_int] = {
                    "train_ratings": dict(zip(
                        train_ratings[train_ratings["userId"] == uid_int]["movieId"].astype(int),
                        train_ratings[train_ratings["userId"] == uid_int]["rating"].astype(float)
                    )),
                    "pos_items": pos_items,
                    "all_eval_items": set(grp["movieId"].astype(int))
                }
        return user_data

    val_users_dict = get_user_splits(val_ratings)
    test_users_dict = get_user_splits(test_ratings)

    logging.info(f"Eligible users: Validation={len(val_users_dict)}, Test={len(test_users_dict)}")

    # Model Configurations to evaluate
    model_configs = {
        "Random Baseline": {"type": "random"},
        "Popularity Baseline": {"type": "hybrid", "weights": {"content": 0.0, "collaborative": 0.0, "popularity": 1.0}},
        "Content-Only (Taste Vector)": {"type": "hybrid", "weights": {"content": 1.0, "collaborative": 0.0, "popularity": 0.0}},
        "Item-kNN CF": {"type": "hybrid", "weights": {"content": 0.0, "collaborative": 1.0, "popularity": 0.0}},
        "CineMatch Hybrid": {"type": "hybrid", "weights": config.DEFAULT_HYBRID_WEIGHTS},
    }

    total_catalog_size = len(catalog_train)
    k = config.DEFAULT_TOP_K

    def evaluate_split(users_dict: Dict[int, Dict[str, Any]], sample_limit: Optional[int]) -> Dict[str, Any]:
        uids = list(users_dict.keys())
        if sample_limit and len(uids) > sample_limit:
            rng = np.random.RandomState(seed)
            uids = rng.choice(uids, size=sample_limit, replace=False).tolist()

        split_results = {}
        all_catalog_mids = set(catalog_train["movieId"])

        for model_name, cfg in model_configs.items():
            user_metrics = {"precision": [], "recall": [], "ndcg": [], "map": [], "hit_rate": []}
            all_recs_set: Set[int] = set()

            rng_model = np.random.RandomState(seed)

            for uid in uids:
                u_info = users_dict[uid]
                u_train = u_info["train_ratings"]
                pos_items = u_info["pos_items"]

                if cfg["type"] == "random":
                    unseen = list(all_catalog_mids - set(u_train.keys()))
                    rec_ids = rng_model.choice(unseen, size=min(k, len(unseen)), replace=False).tolist()
                else:
                    recs, _ = hybrid_model.recommend_for_user(
                        user_ratings=u_train,
                        weights=cfg["weights"],
                        top_n=k
                    )
                    rec_ids = [r["movieId"] for r in recs]

                all_recs_set.update(rec_ids)
                m_scores = calculate_ranking_metrics_single_user(rec_ids, pos_items, k=k)
                for metric_key in user_metrics.keys():
                    user_metrics[metric_key].append(m_scores[metric_key])

            coverage = len(all_recs_set) / max(total_catalog_size, 1)

            # Compute bootstrap CIs
            stats = {}
            for metric_key, vals in user_metrics.items():
                mean_v, lower_v, upper_v = compute_bootstrap_ci(vals, seed=seed)
                stats[metric_key] = {"mean": mean_v, "ci_lower": lower_v, "ci_upper": upper_v}

            stats["catalog_coverage"] = round(coverage, 4)
            stats["n_users_evaluated"] = len(uids)
            split_results[model_name] = stats

        return split_results

    logging.info("Evaluating models on Validation set for Quality Gate...")
    val_eval = evaluate_split(val_users_dict, sample_limit=sample_users)

    logging.info("Evaluating models on Test set...")
    test_eval = evaluate_split(test_users_dict, sample_limit=sample_users)

    # 5. Rating Prediction Accuracy (RMSE & MAE)
    rmse_val, mae_val, eval_pairs = compute_rating_prediction_metrics(
        collab_engine.biased_mf,
        test_ratings.head(600)
    )

    # 6. Quality Gate Decision on Validation NDCG@10
    val_ndcgs = {mname: res["ndcg"]["mean"] for mname, res in val_eval.items()}
    best_single = max(
        [(m, s) for m, s in val_ndcgs.items() if m != "CineMatch Hybrid"],
        key=lambda x: x[1]
    )
    hybrid_val_ndcg = val_ndcgs.get("CineMatch Hybrid", 0.0)

    if hybrid_val_ndcg >= best_single[1]:
        selected_model = "CineMatch Hybrid"
        quality_gate_passed = True
        gate_summary = (
            f"Quality Gate PASSED: Hybrid model (Val NDCG@10 = {hybrid_val_ndcg:.4f}) outperforms "
            f"best single baseline '{best_single[0]}' (Val NDCG@10 = {best_single[1]:.4f})."
        )
    else:
        selected_model = best_single[0]
        quality_gate_passed = False
        gate_summary = (
            f"Quality Gate NOTICE: Best single baseline '{best_single[0]}' (Val NDCG@10 = {best_single[1]:.4f}) "
            f"exceeds Hybrid (Val NDCG@10 = {hybrid_val_ndcg:.4f}). Shipping '{selected_model}'."
        )

    logging.info(gate_summary)

    # 7. Build Output Artifact Dictionary
    final_output = {
        "dataset_fingerprint": fingerprint,
        "protocol": protocol,
        "random_seed": seed,
        "split_ratios": {
            "train": config.EVAL_TRAIN_RATIO,
            "validation": config.EVAL_VAL_RATIO,
            "test": config.EVAL_TEST_RATIO
        },
        "cutoffs": {
            "val_cutoff_timestamp": val_cutoff,
            "test_cutoff_timestamp": test_cutoff
        },
        "catalog_size": total_catalog_size,
        "relevance_threshold": config.RELEVANCE_RATING_THRESHOLD,
        "bayesian_m_threshold": m_threshold,
        "rating_prediction_metrics": {
            "test_rmse": round(rmse_val, 4),
            "test_mae": round(mae_val, 4),
            "evaluated_pairs": eval_pairs
        },
        "quality_gate": {
            "selected_model": selected_model,
            "passed": quality_gate_passed,
            "summary": gate_summary
        },
        "validation_metrics": val_eval,
        "test_metrics": test_eval
    }

    # Save to artifacts/eval_results.json
    artifacts_dir = config.ARTIFACTS_DIR
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out_path = artifacts_dir / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_output, f, indent=2)

    logging.info(f"Successfully wrote evaluation results to {out_path}")
    return final_output


def compute_rating_prediction_metrics(
    mf_model: BiasedMFRecommender,
    test_ratings: pd.DataFrame
) -> Tuple[float, float, int]:
    """Computes RMSE and MAE on observed test pairs without dummy imputations."""
    errors = []
    abs_errors = []

    for _, row in test_ratings.iterrows():
        u = int(row["userId"])
        m = int(row["movieId"])
        r = float(row["rating"])

        if u in mf_model.user_to_idx and m in mf_model.movie_to_idx:
            u_idx = mf_model.user_to_idx[u]
            i_idx = mf_model.movie_to_idx[m]
            pred = mf_model.mu + mf_model.bu[u_idx] + mf_model.bi[i_idx] + float(np.dot(mf_model.P[u_idx], mf_model.Q[i_idx]))
            pred_clamped = float(np.clip(pred, 0.5, 5.0))
            err = pred_clamped - r
            errors.append(err ** 2)
            abs_errors.append(abs(err))

    if not errors:
        return 0.0, 0.0, 0

    rmse = float(np.sqrt(np.mean(errors)))
    mae = float(np.mean(abs_errors))
    return rmse, mae, len(errors)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CineMatch Offline Evaluation CLI")
    parser.add_argument("--protocol", type=str, default="temporal", choices=["temporal", "per_user"], help="Evaluation protocol")
    parser.add_argument("--seed", type=int, default=config.RANDOM_SEED, help="Random seed for reproducibility")
    parser.add_argument("--sample_users", type=int, default=35, help="Number of test users to evaluate (default 35)")
    args = parser.parse_args()

    results = run_evaluation_pipeline(protocol=args.protocol, seed=args.seed, sample_users=args.sample_users)
    print("\n" + "=" * 60)
    print("CINEMATCH EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Selected Model: {results['quality_gate']['selected_model']}")
    print(f"Quality Gate: {results['quality_gate']['summary']}")
    print(f"Test RMSE: {results['rating_prediction_metrics']['test_rmse']} | Test MAE: {results['rating_prediction_metrics']['test_mae']}")
    print("\nTest Ranking Metrics @ 10 (with 95% Bootstrap CIs):")
    for mname, mdata in results["test_metrics"].items():
        ndcg_info = mdata["ndcg"]
        p_info = mdata["precision"]
        r_info = mdata["recall"]
        cov = mdata["catalog_coverage"] * 100
        print(f"- {mname:30s} | NDCG@10: {ndcg_info['mean']:.3f} [{ndcg_info['ci_lower']:.3f}, {ndcg_info['ci_upper']:.3f}] | Prec@10: {p_info['mean']:.3f} | Rec@10: {r_info['mean']:.3f} | Coverage: {cov:.1f}%")
