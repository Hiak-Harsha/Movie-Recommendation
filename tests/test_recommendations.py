"""
Unit tests for Content-Based Recommender, Multi-Block TF-IDF, Search, and User Taste Vectors.
"""
import pytest
import numpy as np
import pandas as pd

from src.data_loader import load_raw_data, validate_and_clean_data
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender


@pytest.fixture(scope="module")
def content_suite():
    """Builds and fits a ContentRecommender on real MovieLens data."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    pop_df, _, _ = compute_popularity_metrics(ratings_clean)
    catalog = build_movie_catalog(movies_clean, tags_clean, pop_df, links_clean)
    
    recommender = ContentRecommender(genre_weight=1.0, tag_weight=0.8)
    recommender.fit(catalog)
    return {
        "recommender": recommender,
        "catalog": catalog,
        "ratings": ratings_clean
    }


def test_title_search_variants(content_suite):
    """Verify title search works across articles, casing, and accents."""
    engine = content_suite["recommender"]
    
    res_lower = engine.search_movies("the matrix")
    res_trailing = engine.search_movies("matrix, the")
    res_upper = engine.search_movies("MATRIX")
    res_plain = engine.search_movies("matrix")

    assert not res_lower.empty
    assert not res_trailing.empty
    assert not res_upper.empty
    assert not res_plain.empty

    # The Matrix (movieId 2571) should be at or near the top
    assert 2571 in res_lower["movieId"].head(3).values
    assert 2571 in res_trailing["movieId"].head(3).values
    assert 2571 in res_upper["movieId"].head(3).values


def test_title_search_accents(content_suite):
    """Verify title search works with accent-stripped queries (e.g. Amelie)."""
    engine = content_suite["recommender"]
    res = engine.search_movies("amelie")
    assert not res.empty
    # Amélie (movieId 4973)
    assert 4973 in res["movieId"].values


def test_search_empty_and_unknown(content_suite):
    """Verify search gracefully returns empty DataFrame on blanks or nonsense strings."""
    engine = content_suite["recommender"]
    assert engine.search_movies("").empty
    assert engine.search_movies("   ").empty
    assert engine.search_movies("xyznonexistentmovie987654321").empty


def test_seed_movie_never_in_recommendations(content_suite):
    """Verify that the query movie is never recommended as its own similar movie."""
    engine = content_suite["recommender"]
    recs = engine.get_similar_movies(movie_id=1, top_n=10)
    rec_ids = [r["movieId"] for r in recs]
    assert 1 not in rec_ids
    assert len(recs) == 10


def test_user_taste_vector_directional_preference(content_suite):
    """Verify user taste vector properly captures positive and negative tastes."""
    engine = content_suite["recommender"]
    
    # User who loves Star Wars (Sci-Fi, Adventure) and hates Romances
    # 260: Star Wars: Episode IV (5.0), 1196: Star Wars: Episode V (5.0)
    # 838: Emma (Romance, Comedy) (1.0)
    user_ratings = {
        260: 5.0,
        1196: 5.0,
        838: 1.0
    }
    taste_vec = engine.build_user_taste_vector(user_ratings)
    assert taste_vec is not None
    assert taste_vec.shape[1] == engine.feature_matrix.shape[1]

    scores = engine.score_candidates_for_user(taste_vec)
    assert len(scores) == len(engine.catalog_df)

    # Score for Star Wars: Episode VI (1210) should be much higher than Emma (838)
    idx_rotj = engine.movie_id_to_idx.get(1210)
    idx_emma = engine.movie_id_to_idx.get(838)
    
    if idx_rotj is not None and idx_emma is not None:
        assert scores[idx_rotj] > scores[idx_emma]


def test_genre_and_year_filters(content_suite):
    """Verify genre and year filters constrain similar movie recommendations."""
    engine = content_suite["recommender"]
    recs = engine.get_similar_movies(
        movie_id=1,  # Toy Story
        top_n=6,
        genre_filter=["Drama"],
        year_range=(1990, 2000)
    )
    for r in recs:
        assert "Drama" in r["genres_list"]
        if r["release_year"] is not None:
            assert 1990 <= r["release_year"] <= 2000


def test_deterministic_content_recommendations(content_suite):
    """Verify repeated calls yield deterministic results."""
    engine = content_suite["recommender"]
    recs_1 = engine.get_similar_movies(movie_id=2571, top_n=5)
    recs_2 = engine.get_similar_movies(movie_id=2571, top_n=5)
    assert [r["movieId"] for r in recs_1] == [r["movieId"] for r in recs_2]
