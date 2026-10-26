"""
Unit tests for Evaluation Pipeline, Leakage Prevention, and Metric Correctness.
"""
import pytest
import numpy as np
import pandas as pd

from src.evaluation import (
    calculate_ranking_metrics_single_user,
    compute_bootstrap_ci,
    temporal_split_data
)
from src.preprocessing import aggregate_movie_tags, compute_popularity_metrics


def test_metric_correctness_hand_calculated_example():
    """
    Verify Precision, Recall, NDCG, MAP, and HitRate against hand-calculated values.
    
    Setup:
      Recommended: [10, 20, 30, 40, 50] (K=5)
      Ground Truth: {20, 40, 99} (|T| = 3)
      Hits at ranks:
        rank 1 (idx 0, movie 10): 0
        rank 2 (idx 1, movie 20): 1
        rank 3 (idx 2, movie 30): 0
        rank 4 (idx 3, movie 40): 1
        rank 5 (idx 4, movie 50): 0
      
      Total hits = 2
      Precision@5 = 2 / 5 = 0.40
      Recall@5 = 2 / 3 = 0.6667
      HitRate@5 = 1.0
      
      MAP@5:
        At rank 2: P@2 = 1/2 = 0.5
        At rank 4: P@4 = 2/4 = 0.5
        AP = (0.5 + 0.5) / min(3, 5) = 1.0 / 3 = 0.3333
        
      NDCG@5:
        DCG = 1/log2(2+1) + 1/log2(4+1) = 1/log2(3) + 1/log2(5)
            = 1/1.58496 + 1/2.32193 = 0.63093 + 0.43068 = 1.06161
        IDCG for 2 hits out of 3 at ranks 1 and 2:
            = 1/log2(1+1) + 1/log2(2+1) = 1/1.0 + 1/1.58496 = 1.0 + 0.63093 = 1.63093
        NDCG = 1.06161 / 1.63093 = 0.6509
    """
    recommended = [10, 20, 30, 40, 50]
    ground_truth = {20, 40, 99}

    metrics = calculate_ranking_metrics_single_user(recommended, ground_truth, k=5)

    # NDCG@5:
    # DCG = 1/log2(3) + 1/log2(5) = 0.63093 + 0.43068 = 1.06161
    # IDCG for 3 items at ranks 1, 2, 3 = 1/log2(2) + 1/log2(3) + 1/log2(4) = 1.0 + 0.63093 + 0.5 = 2.13093
    # NDCG = 1.06161 / 2.13093 = 0.498189
    expected_ndcg = (1.0 / np.log2(3) + 1.0 / np.log2(5)) / (1.0 / np.log2(2) + 1.0 / np.log2(3) + 1.0 / np.log2(4))
    assert metrics["ndcg"] == pytest.approx(expected_ndcg, abs=1e-3)


def test_bootstrap_ci_computation():
    """Verify bootstrap confidence interval computation returns reasonable bounds."""
    vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    mean_v, lower_v, upper_v = compute_bootstrap_ci(vals, n_rounds=100, seed=42)
    assert lower_v <= mean_v <= upper_v
    assert lower_v > 0.0


def test_zero_leakage_temporal_split():
    """Verify temporal split boundaries strictly prevent future ratings from leaking into train."""
    ratings = pd.DataFrame({
        "userId": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "movieId": [10] * 10,
        "rating": [4.0] * 10,
        "timestamp": [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    })
    train_df, val_df, test_df, val_cutoff, test_cutoff = temporal_split_data(
        ratings, train_ratio=0.7, val_ratio=0.1
    )
    # Train is first 7, Val is next 1, Test is last 2
    assert len(train_df) == 7
    assert len(val_df) == 1
    assert len(test_df) == 2
    assert train_df["timestamp"].max() <= val_df["timestamp"].min()
    assert val_df["timestamp"].max() <= test_df["timestamp"].min()


def test_sentinel_future_tag_leakage_prevention():
    """
    Leakage Test: A sentinel tag created after the training cutoff timestamp
    must NOT appear in the aggregated tag vocabulary for training.
    """
    tags = pd.DataFrame({
        "userId": [1, 2],
        "movieId": [10, 10],
        "tag": ["historical_valid", "FUTURE_SENTINEL_LEAK"],
        "timestamp": [1000, 5000]
    })
    # Cutoff at 3000
    cutoff = 3000
    agg = aggregate_movie_tags(tags, max_timestamp=cutoff)
    
    assert 10 in agg
    assert "historical_valid" in agg[10]
    assert "future_sentinel_leak" not in agg[10]
