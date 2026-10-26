"""
CineMatch Evaluation Module
Implements reproducible evaluation protocol with temporal/per-user train-test
splits, zero test-rating leakage, RMSE/MAE rating metrics, Precision@K, Recall@K,
catalog coverage, and side-by-side algorithm comparison.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

import config


@dataclass
class EvaluationMetrics:
    """Container for recommendation evaluation results."""
    model_name: str
    precision_at_k: float
    recall_at_k: float
    catalog_coverage: float
    rmse: Optional[float] = None
    mae: Optional[float] = None
    evaluation_users_count: int = 0
    k: int = 10

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            f"precision_at_{self.k}": round(self.precision_at_k, 4),
            f"recall_at_{self.k}": round(self.recall_at_k, 4),
            "catalog_coverage": round(self.catalog_coverage, 4),
            "rmse": round(self.rmse, 4) if self.rmse is not None else None,
            "mae": round(self.mae, 4) if self.mae is not None else None,
            "evaluation_users_count": self.evaluation_users_count,
        }


def temporal_user_split(
    ratings_df: pd.DataFrame,
    test_ratio: float = config.EVALUATION_TEST_RATIO
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs per-user temporal train/test split.
    For each user, the earliest (1 - test_ratio) ratings by timestamp go to train,
    and the remaining latest ratings go to test.
    Ensures zero leakage while maintaining user representation in train.
    """
    if ratings_df.empty:
        raise ValueError("Cannot split empty ratings DataFrame.")

    train_list = []
    test_list = []

    # Sort by timestamp
    sorted_ratings = ratings_df.sort_values(by=["userId", "timestamp"])

    for uid, group in sorted_ratings.groupby("userId"):
        n = len(group)
        if n < 5:
            # Users with very few ratings kept in train to preserve rating matrix
            train_list.append(group)
        else:
            n_test = max(1, int(n * test_ratio))
            n_train = n - n_test
            train_list.append(group.iloc[:n_train])
            test_list.append(group.iloc[n_train:])

    train_df = pd.concat(train_list, ignore_index=True)
    test_df = pd.concat(test_list, ignore_index=True)

    return train_df, test_df


def compute_rating_prediction_metrics(
    collab_model: Any,
    test_ratings: pd.DataFrame
) -> Tuple[float, float, int]:
    """
    Evaluates rating prediction accuracy (RMSE and MAE) on held-out test ratings.
    Only computes metrics for actual predictions without imputing dummy values.
    """
    errors = []
    abs_errors = []

    # Group test ratings by user
    for uid, group in test_ratings.groupby("userId"):
        user_hist = collab_model.get_existing_user_ratings(int(uid))
        if not user_hist:
            continue

        for _, row in group.iterrows():
            target_mid = int(row["movieId"])
            actual = float(row["rating"])
            pred = collab_model.predict_rating_for_item(user_hist, target_mid)
            if pred is not None:
                err = pred - actual
                errors.append(err ** 2)
                abs_errors.append(abs(err))

    if not errors:
        return 0.0, 0.0, 0

    rmse = float(np.sqrt(np.mean(errors)))
    mae = float(np.mean(abs_errors))
    return rmse, mae, len(errors)


def evaluate_ranking_models(
    hybrid_engine: Any,
    train_ratings: pd.DataFrame,
    test_ratings: pd.DataFrame,
    total_catalog_size: int,
    k: int = 10,
    relevance_threshold: float = config.RELEVANCE_RATING_THRESHOLD,
    sample_users: int = 40
) -> Dict[str, EvaluationMetrics]:
    """
    Computes Precision@K, Recall@K, and Catalog Coverage on held-out test data.
    Compares:
      1. Content-Based Only (weights: {'content': 1.0, 'collaborative': 0.0, 'popularity': 0.0})
      2. Collaborative-Only (weights: {'content': 0.0, 'collaborative': 1.0, 'popularity': 0.0})
      3. Hybrid Ranking (weights: config.DEFAULT_HYBRID_WEIGHTS)
      4. Popularity Baseline (weights: {'content': 0.0, 'collaborative': 0.0, 'popularity': 1.0})
    """
    # Find test users who have at least one relevant item (rating >= relevance_threshold) in test set
    test_relevant_by_user = {}
    for uid, group in test_ratings.groupby("userId"):
        rel_items = set(group[group["rating"] >= relevance_threshold]["movieId"].astype(int))
        if len(rel_items) >= 2:
            test_relevant_by_user[int(uid)] = rel_items

    candidate_uids = list(test_relevant_by_user.keys())
    if not candidate_uids:
        return {}

    # Sample users for deterministic fast evaluation
    rng = np.random.RandomState(config.RANDOM_STATE)
    selected_uids = rng.choice(candidate_uids, size=min(sample_users, len(candidate_uids)), replace=False).tolist()

    configurations = {
        "Popularity Baseline": {"content": 0.0, "collaborative": 0.0, "popularity": 1.0},
        "Content-Based Model": {"content": 1.0, "collaborative": 0.0, "popularity": 0.0},
        "Collaborative Filtering": {"content": 0.0, "collaborative": 1.0, "popularity": 0.0},
        "CineMatch Hybrid": config.DEFAULT_HYBRID_WEIGHTS,
    }

    results = {}

    for model_name, weights in configurations.items():
        precisions = []
        recalls = []
        all_recommended_items: Set[int] = set()

        for uid in selected_uids:
            user_train_ratings = hybrid_engine.collab_model.get_existing_user_ratings(uid)
            if not user_train_ratings:
                continue

            ground_truth = test_relevant_by_user[uid]
            if not ground_truth:
                continue

            recs, _ = hybrid_engine.recommend_for_user(
                user_ratings=user_train_ratings,
                weights=weights,
                top_n=k
            )

            rec_ids = [r["movieId"] for r in recs]
            all_recommended_items.update(rec_ids)

            hits = len(set(rec_ids) & ground_truth)
            precisions.append(hits / k)
            recalls.append(hits / len(ground_truth))

        p_at_k = float(np.mean(precisions)) if precisions else 0.0
        r_at_k = float(np.mean(recalls)) if recalls else 0.0
        coverage = float(len(all_recommended_items) / max(total_catalog_size, 1))

        results[model_name] = EvaluationMetrics(
            model_name=model_name,
            precision_at_k=p_at_k,
            recall_at_k=r_at_k,
            catalog_coverage=coverage,
            evaluation_users_count=len(precisions),
            k=k
        )

    return results
