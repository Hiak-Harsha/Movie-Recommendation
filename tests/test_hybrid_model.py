"""
Unit tests for Hybrid Recommender, Collaborative Filtering, and Evaluation.
"""
import pytest
import pandas as pd
import numpy as np

from src.data_loader import load_raw_data, validate_and_clean_data
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender
from src.collaborative_model import CollaborativeRecommender
from src.hybrid_model import HybridRecommender
from src.evaluation import temporal_user_split, compute_rating_prediction_metrics


@pytest.fixture(scope="module")
def hybrid_suite():
    """Builds a full trained hybrid recommendation suite."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    # Split train/test
    train_ratings, test_ratings = temporal_user_split(ratings_clean, test_ratio=0.2)
    pop_df, _, _ = compute_popularity_metrics(train_ratings)
    catalog = build_movie_catalog(movies_clean, tags_clean, pop_df)

    content_model = ContentRecommender().fit(catalog)
    collab_model = CollaborativeRecommender().fit(train_ratings)
    hybrid_model = HybridRecommender(content_model, collab_model, catalog)

    return {
        "catalog": catalog,
        "content_model": content_model,
        "collab_model": collab_model,
        "hybrid_model": hybrid_model,
        "train_ratings": train_ratings,
        "test_ratings": test_ratings,
    }


def test_already_rated_movies_are_excluded(hybrid_suite):
    """Verify that movies already rated by the user are never in personalized recommendations."""
    hybrid = hybrid_suite["hybrid_model"]
    # User rates 5 movies
    user_ratings = {1: 5.0, 2: 4.0, 3: 3.5, 47: 5.0, 50: 4.5}
    recs, meta = hybrid.recommend_for_user(user_ratings, top_n=20)

    recommended_ids = {r["movieId"] for r in recs}
    for rated_id in user_ratings.keys():
        assert rated_id not in recommended_ids


def test_cold_start_fallback_trigger(hybrid_suite):
    """Verify that insufficient user history triggers the documented cold-start fallback."""
    hybrid = hybrid_suite["hybrid_model"]
    # Only 1 rating (threshold is 3)
    user_ratings = {1: 5.0}
    recs, meta = hybrid.recommend_for_user(user_ratings, top_n=10)

    assert meta["is_fallback"] is True
    assert "Minimum" in meta["fallback_reason"]
    assert meta["active_weights"]["collaborative"] == 0.0
    assert len(recs) == 10
    # Every recommendation should still have valid scores
    for r in recs:
        assert r["collab_score"] is None
        assert 0.0 <= r["hybrid_score"] <= 1.0


def test_hybrid_ranking_combines_available_scores(hybrid_suite):
    """Verify that hybrid ranking combines scores using active weights."""
    hybrid = hybrid_suite["hybrid_model"]
    # Profile with sufficient ratings to activate CF
    user_ratings = {
        1: 5.0,     # Toy Story (Animation)
        3114: 5.0,  # Toy Story 2
        4886: 4.5,  # Monsters, Inc.
        588: 4.5,   # Aladdin
        260: 5.0,   # Star Wars: Episode IV
    }
    recs, meta = hybrid.recommend_for_user(user_ratings, top_n=10)

    assert meta["is_fallback"] is False
    assert len(recs) == 10
    # Check that component scores are preserved
    for r in recs:
        assert 0.0 <= r["hybrid_score"] <= 1.0
        assert 0.0 <= r["content_score"] <= 1.0
        assert 0.0 <= r["popularity_score"] <= 1.0
        assert len(r["reasons"]) > 0


def test_filters_change_eligible_candidates(hybrid_suite):
    """Verify that genre and release year filters restrict candidate recommendations."""
    hybrid = hybrid_suite["hybrid_model"]
    user_ratings = {1: 5.0, 2: 4.0, 3: 4.0}
    recs, _ = hybrid.recommend_for_user(
        user_ratings,
        preferred_genres=["Sci-Fi"],
        year_range=(1980, 1999),
        top_n=10
    )
    for r in recs:
        assert "Sci-Fi" in r["genres_list"]
        if r["release_year"] is not None:
            assert 1980 <= r["release_year"] <= 1999


def test_evaluation_train_test_leakage_prevention(hybrid_suite):
    """Verify temporal split prevents test ratings leakage into training set."""
    train_ratings = hybrid_suite["train_ratings"]
    test_ratings = hybrid_suite["test_ratings"]

    # Verify no overlap in (userId, movieId) between train and test
    train_pairs = set(zip(train_ratings["userId"], train_ratings["movieId"]))
    test_pairs = set(zip(test_ratings["userId"], test_ratings["movieId"]))
    assert len(train_pairs & test_pairs) == 0

    # Verify temporal ordering: For each user in both, max train timestamp <= min test timestamp
    common_users = set(train_ratings["userId"]) & set(test_ratings["userId"])
    for uid in list(common_users)[:30]:
        max_train_ts = train_ratings[train_ratings["userId"] == uid]["timestamp"].max()
        min_test_ts = test_ratings[test_ratings["userId"] == uid]["timestamp"].min()
        assert max_train_ts <= min_test_ts


def test_rating_prediction_rmse_mae(hybrid_suite):
    """Verify rating prediction evaluation computes real numeric RMSE and MAE."""
    collab = hybrid_suite["collab_model"]
    test_ratings = hybrid_suite["test_ratings"]
    rmse, mae, count = compute_rating_prediction_metrics(collab, test_ratings.head(500))

    assert count > 0
    assert 0.1 <= rmse <= 2.5
    assert 0.1 <= mae <= 2.5
