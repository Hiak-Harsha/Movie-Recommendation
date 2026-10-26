"""
Unit tests for Content-Based Recommender and Search.
"""
import pytest
import pandas as pd
from src.data_loader import load_raw_data, validate_and_clean_data
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender


@pytest.fixture(scope="module")
def content_engine():
    """Builds and fits a ContentRecommender for testing."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    pop_df, _, _ = compute_popularity_metrics(ratings_clean)
    catalog = build_movie_catalog(movies_clean, tags_clean, pop_df)
    
    recommender = ContentRecommender()
    recommender.fit(catalog)
    return recommender


def test_title_search_case_differences(content_engine):
    """Verify title search works regardless of casing and partial tokens."""
    res_lower = content_engine.search_movies("toy story")
    res_upper = content_engine.search_movies("TOY STORY")
    res_mixed = content_engine.search_movies("Toy Story")

    assert not res_lower.empty
    assert not res_upper.empty
    assert len(res_lower) == len(res_upper) == len(res_mixed)
    # Check top match is Toy Story
    assert 1 in res_lower["movieId"].values


def test_search_empty_and_unknown_queries(content_engine):
    """Verify search gracefully returns empty dataframe on blanks or unknown titles."""
    assert content_engine.search_movies("").empty
    assert content_engine.search_movies("   ").empty
    res = content_engine.search_movies("xyznonexistentmovie987654321")
    assert res.empty


def test_seed_movie_never_in_its_own_recommendations(content_engine):
    """Verify that the query movie is never recommended as its own similar movie."""
    # Toy Story (movieId 1)
    recs = content_engine.get_similar_movies(movie_id=1, top_n=10)
    rec_ids = [r["movieId"] for r in recs]
    assert 1 not in rec_ids
    assert len(recs) == 10


def test_recommendations_reference_valid_movie_ids(content_engine):
    """Verify all recommended movie IDs exist in the catalog."""
    valid_ids = set(content_engine.catalog_df["movieId"])
    # Inception (movieId 79132) or Toy Story (1)
    recs = content_engine.get_similar_movies(movie_id=1, top_n=15)
    for r in recs:
        assert r["movieId"] in valid_ids
        assert 0.0 <= r["content_similarity"] <= 1.0
        assert isinstance(r["reasons"], list)
        assert len(r["reasons"]) > 0


def test_genre_and_year_filters(content_engine):
    """Verify genre and year filters constrain similar movie recommendations."""
    # Toy Story (1), filter by genre 'Drama' and year range 1990-2000
    recs = content_engine.get_similar_movies(
        movie_id=1,
        top_n=10,
        genre_filter=["Drama"],
        year_range=(1990, 2000)
    )
    for r in recs:
        assert "Drama" in r["genres_list"]
        if r["release_year"] is not None:
            assert 1990 <= r["release_year"] <= 2000


def test_deterministic_content_recommendations(content_engine):
    """Verify repeated calls yield deterministic results."""
    recs_1 = content_engine.get_similar_movies(movie_id=1, top_n=5)
    recs_2 = content_engine.get_similar_movies(movie_id=1, top_n=5)
    
    ids_1 = [r["movieId"] for r in recs_1]
    ids_2 = [r["movieId"] for r in recs_2]
    assert ids_1 == ids_2
