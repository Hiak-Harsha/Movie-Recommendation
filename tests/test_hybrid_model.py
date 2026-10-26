"""
Unit tests for Hybrid Recommender, Dynamic Weighting, Determinism, and Filters.
"""
import pytest
import numpy as np
import pandas as pd

from src.data_loader import load_raw_data, validate_and_clean_data
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender
from src.collaborative_model import CollaborativeEngine
from src.hybrid_model import HybridRecommender


@pytest.fixture(scope="module")
def full_suite():
    """Builds and trains a full hybrid pipeline fixture."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    m_clean, r_clean, t_clean, l_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    pop_df, _, _ = compute_popularity_metrics(r_clean)
    catalog = build_movie_catalog(m_clean, t_clean, pop_df, l_clean)

    content_model = ContentRecommender().fit(catalog)
    collab_engine = CollaborativeEngine().fit(r_clean)
    hybrid_model = HybridRecommender(content_model, collab_engine, catalog)

    return {
        "catalog": catalog,
        "content_model": content_model,
        "collab_engine": collab_engine,
        "hybrid_model": hybrid_model,
        "ratings": r_clean,
    }


def test_already_rated_movies_are_excluded(full_suite):
    """Verify that movies already rated by the user are strictly excluded."""
    hybrid = full_suite["hybrid_model"]
    user_ratings = {1: 5.0, 2: 4.0, 3: 3.5, 47: 5.0, 50: 4.5}
    recs, meta = hybrid.recommend_for_user(user_ratings, top_n=20)

    recommended_ids = {r["movieId"] for r in recs}
    for rated_id in user_ratings.keys():
        assert rated_id not in recommended_ids


def test_missing_signal_is_not_treated_as_zero(full_suite):
    """
    Verify that missing collaborative prediction does NOT penalize item with zero.
    Instead, weights are dynamically re-normalized over available signals.
    """
    hybrid = full_suite["hybrid_model"]
    # Cold start user with 2 ratings (no CF predictions)
    user_ratings = {1: 5.0, 2: 4.0}
    recs, meta = hybrid.recommend_for_user(user_ratings, top_n=10)

    assert meta["is_fallback"] is True
    for r in recs:
        assert r["collab_score"] is None
        # Must only have content and popularity in signals_used
        assert "collaborative" not in r["signals_used"]
        # Score must be bounded in [0, 1]
        assert 0.0 <= r["hybrid_score"] <= 1.0


def test_genre_filter_or_and_modes(full_suite):
    """Verify OR vs AND genre matching semantics."""
    hybrid = full_suite["hybrid_model"]
    user_ratings = {1: 5.0, 2: 4.0, 3: 4.0, 47: 4.0, 50: 4.0}

    # OR mode: Action OR Sci-Fi
    recs_or, _ = hybrid.recommend_for_user(
        user_ratings,
        preferred_genres=["Action", "Sci-Fi"],
        genre_match_mode="OR",
        top_n=10
    )
    for r in recs_or:
        genres = set(r["genres_list"])
        assert "Action" in genres or "Sci-Fi" in genres

    # AND mode: Action AND Sci-Fi
    recs_and, _ = hybrid.recommend_for_user(
        user_ratings,
        preferred_genres=["Action", "Sci-Fi"],
        genre_match_mode="AND",
        top_n=10
    )
    for r in recs_and:
        genres = set(r["genres_list"])
        assert "Action" in genres and "Sci-Fi" in genres


def test_year_range_filter(full_suite):
    """Verify release year range filtering."""
    hybrid = full_suite["hybrid_model"]
    user_ratings = {1: 5.0, 2: 4.0, 3: 4.0, 47: 4.0, 50: 4.0}
    recs, _ = hybrid.recommend_for_user(
        user_ratings,
        year_range=(1990, 1999),
        top_n=10
    )
    for r in recs:
        if r["release_year"] is not None:
            assert 1990 <= r["release_year"] <= 1999


def test_deterministic_hybrid_ranking(full_suite):
    """Verify identical inputs yield identical deterministic rankings."""
    hybrid = full_suite["hybrid_model"]
    user_ratings = {260: 5.0, 1196: 5.0, 1210: 4.5, 2571: 5.0, 589: 4.5}
    
    recs_1, _ = hybrid.recommend_for_user(user_ratings, top_n=8)
    recs_2, _ = hybrid.recommend_for_user(user_ratings, top_n=8)

    ids_1 = [r["movieId"] for r in recs_1]
    ids_2 = [r["movieId"] for r in recs_2]
    assert ids_1 == ids_2
