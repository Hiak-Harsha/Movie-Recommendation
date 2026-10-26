"""
Unit tests for data loader and preprocessing modules.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.data_loader import (
    resolve_data_directory,
    load_raw_data,
    validate_and_clean_data,
    DataValidationError
)
from src.preprocessing import (
    extract_year_from_title,
    parse_genres,
    normalize_genres_for_text,
    clean_tag_text,
    aggregate_movie_tags,
    compute_popularity_metrics,
    build_movie_catalog
)


def test_resolve_data_directory():
    """Verify that dataset directory is located correctly."""
    data_dir = resolve_data_directory()
    assert data_dir.exists()
    assert (data_dir / "movies.csv").exists()
    assert (data_dir / "ratings.csv").exists()


def test_resolve_missing_directory_raises():
    """Verify that an invalid directory path raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        resolve_data_directory(custom_path="non_existent_folder_xyz_123")


def test_load_raw_data_and_schema():
    """Verify that real data loads with expected columns and non-empty rows."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    
    assert len(movies_raw) >= 9000
    assert len(ratings_raw) >= 100000
    assert {"movieId", "title", "genres"}.issubset(set(movies_raw.columns))
    assert {"userId", "movieId", "rating", "timestamp"}.issubset(set(ratings_raw.columns))


def test_validate_and_clean_data_integrity():
    """Verify clean data properties: no orphan ratings, proper types, health report."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )

    assert report.clean_movie_count == len(movies_clean)
    assert report.clean_rating_count == len(ratings_clean)
    assert report.orphan_ratings_count == 0  # in our real dataset, no orphans
    assert report.clean_user_count == 610

    # Ensure ratings are strictly between 0.5 and 5.0
    assert ratings_clean["rating"].min() >= 0.5
    assert ratings_clean["rating"].max() <= 5.0

    # Ensure all ratings reference valid movieIds
    movie_id_set = set(movies_clean["movieId"])
    assert set(ratings_clean["movieId"]).issubset(movie_id_set)


def test_clean_data_handles_invalid_and_duplicates():
    """Verify that duplicate rows and out-of-range ratings are sanitized."""
    # Synthetic bad data
    bad_movies = pd.DataFrame({
        "movieId": [1, 2, 2, "bad_id"],
        "title": ["Toy Story (1995)", "Jumanji (1995)", "Jumanji (1995)", "Bad"],
        "genres": ["Animation|Comedy", "Adventure", "Adventure", "None"]
    })
    bad_ratings = pd.DataFrame({
        "userId": [1, 1, 1, 2, 3],
        "movieId": [1, 1, 2, 9999, 1],  # 9999 is orphan
        "rating": [4.0, 5.0, 7.5, 3.0, 3.5],  # 7.5 is out of bounds; (1, 1) is duplicate
        "timestamp": [100, 200, 300, 400, 500]
    })
    tags_dummy = pd.DataFrame(columns=["userId", "movieId", "tag", "timestamp"])

    m_clean, r_clean, t_clean, _, report = validate_and_clean_data(bad_movies, bad_ratings, tags_dummy)

    # movieId=2 was deduplicated, 'bad_id' was dropped -> exactly 2 valid movies (1 and 2)
    assert len(m_clean) == 2
    # rating 7.5 was dropped, orphan 9999 dropped, duplicate (1, 1) kept latest (5.0)
    assert len(r_clean) == 2  # (userId=1, movieId=1) and (userId=3, movieId=1)
    assert report.orphan_ratings_count == 1
    assert any("out of bounds" in issue or "range" in issue for issue in report.issues_detected)


def test_extract_year_from_title():
    """Verify release year extraction from titles."""
    assert extract_year_from_title("Toy Story (1995)") == 1995
    assert extract_year_from_title("Dr. Strangelove (1964) ") == 1964
    assert extract_year_from_title("Movie Without Year") is None
    assert extract_year_from_title("Invalid Year (9999)") is None


def test_parse_genres():
    """Verify genre parsing ignores '(no genres listed)' and splits pipe."""
    assert parse_genres("Action|Adventure|Sci-Fi") == ["Action", "Adventure", "Sci-Fi"]
    assert parse_genres("(no genres listed)") == []
    assert parse_genres("") == []
    assert normalize_genres_for_text(["Sci-Fi", "Film-Noir"]) == "sci_fi film_noir"


def test_clean_tag_text_no_nan():
    """Verify that literal nan and empty tags are cleaned."""
    assert clean_tag_text("nan") == ""
    assert clean_tag_text("None") == ""
    assert clean_tag_text("  Mind-Bending  ") == "mind-bending"


def test_bayesian_popularity_computation():
    """Verify Bayesian smoothing reduces low-sample noise and calculates correctly."""
    ratings = pd.DataFrame({
        "userId": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "movieId": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 20, 30],
        "rating": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 1.0],
        "timestamp": [1] * 12
    })
    # Movie 10 has 10 ratings of 5.0. Movie 20 has only 1 rating of 5.0.
    # With Bayesian smoothing m=10, Movie 10 should have a much higher weighted_rating than Movie 20.
    pop_df, global_mean, m = compute_popularity_metrics(ratings, min_ratings_threshold=10)
    
    assert global_mean == pytest.approx(ratings["rating"].mean())
    score_10 = pop_df.loc[pop_df["movieId"] == 10, "weighted_rating"].values[0]
    score_20 = pop_df.loc[pop_df["movieId"] == 20, "weighted_rating"].values[0]
    assert score_10 > score_20
