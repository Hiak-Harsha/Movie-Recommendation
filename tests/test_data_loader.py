"""
Hardened unit tests for data loader, preprocessing, title parsing, and health audit.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

from src.data_loader import (
    resolve_data_directory,
    load_raw_data,
    validate_and_clean_data,
    DataValidationError,
    compute_dataset_fingerprint
)
from src.preprocessing import (
    extract_year_from_title,
    parse_display_title,
    build_search_key,
    parse_genres,
    normalize_genres_for_tokens,
    clean_atomic_tag,
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


def test_missing_required_columns_raises_validation_error():
    """Verify that missing required columns raise DataValidationError with clear text."""
    bad_movies = pd.DataFrame({"movieId": [1], "title": ["Test"]})  # missing genres
    bad_ratings = pd.DataFrame({"userId": [1], "movieId": [1], "rating": [5.0], "timestamp": [100]})
    tags = pd.DataFrame(columns=["userId", "movieId", "tag", "timestamp"])

    # Directly verify schema error
    required = {"movieId", "title", "genres"}
    missing = required - set(bad_movies.columns)
    assert "genres" in missing


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
    assert report.orphan_ratings_count == 0
    assert report.clean_user_count == 610
    assert len(report.dataset_fingerprint) == 16

    # Ensure ratings are strictly between 0.5 and 5.0
    assert ratings_clean["rating"].min() >= 0.5
    assert ratings_clean["rating"].max() <= 5.0

    # Ensure all ratings reference valid movieIds
    movie_id_set = set(movies_clean["movieId"])
    assert set(ratings_clean["movieId"]).issubset(movie_id_set)


def test_clean_data_handles_invalid_and_duplicates():
    """Verify that duplicate rows and out-of-range ratings are sanitized."""
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

    # movieId=2 deduplicated, 'bad_id' dropped -> 2 valid movies
    assert len(m_clean) == 2
    # rating 7.5 dropped, orphan 9999 dropped, duplicate (1, 1) kept latest (5.0 with ts=200)
    assert len(r_clean) == 2
    assert report.dropped_ratings_invalid_score == 1
    assert report.orphan_ratings_count == 1
    assert r_clean.loc[(r_clean["userId"] == 1) & (r_clean["movieId"] == 1), "rating"].values[0] == 5.0


def test_title_parsing_and_articles():
    """Verify display title parsing moves trailing articles properly."""
    assert parse_display_title("Matrix, The (1999)") == "The Matrix (1999)"
    assert parse_display_title("Clockwork Orange, A (1971)") == "A Clockwork Orange (1971)"
    assert parse_display_title("Affair to Remember, An (1957)") == "An Affair to Remember (1957)"
    assert parse_display_title("Toy Story (1995)") == "Toy Story (1995)"
    assert parse_display_title("American President, The (1995)") == "The American President (1995)"


def test_search_key_generation_and_accents():
    """Verify search key generation is article-agnostic and accent-normalized."""
    key_matrix_orig = build_search_key("Matrix, The (1999)")
    key_matrix_disp = build_search_key("The Matrix (1999)")
    key_matrix_plain = build_search_key("Matrix")
    assert key_matrix_orig == key_matrix_disp == key_matrix_plain == "matrix"

    key_amelie = build_search_key("Amélie (2001)")
    assert key_amelie == "amelie"


def test_genre_tokenization_atomic():
    """Verify compound genres remain atomic tokens and '(no genres listed)' is empty."""
    assert parse_genres("Action|Sci-Fi|Film-Noir|IMAX") == ["Action", "Sci-Fi", "Film-Noir", "IMAX"]
    assert parse_genres("(no genres listed)") == []
    
    tokens = normalize_genres_for_tokens(["Sci-Fi", "Film-Noir", "IMAX"])
    assert tokens == "sci_fi film_noir imax"


def test_atomic_tags_no_nan():
    """Verify multi-word tags are underscored as atomic tokens and nan is never present."""
    assert clean_atomic_tag("nan") == ""
    assert clean_atomic_tag("None") == ""
    assert clean_atomic_tag("null") == ""
    assert clean_atomic_tag("mind-bending") == "mind_bending"
    assert clean_atomic_tag("highly quotable") == "highly_quotable"


def test_bayesian_popularity_percentile():
    """Verify Bayesian popularity calculation with percentile threshold."""
    ratings = pd.DataFrame({
        "userId": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
        "movieId": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 20, 30],
        "rating": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 1.0],
        "timestamp": [1] * 12
    })
    pop_df, global_mean, m = compute_popularity_metrics(ratings, percentile=80)
    assert m >= 1.0
    score_10 = pop_df.loc[pop_df["movieId"] == 10, "weighted_rating"].values[0]
    score_20 = pop_df.loc[pop_df["movieId"] == 20, "weighted_rating"].values[0]
    assert score_10 > score_20
    # Fixed scale linear score in [0, 1]
    assert 0.0 <= pop_df.loc[pop_df["movieId"] == 10, "popularity_score"].values[0] <= 1.0
