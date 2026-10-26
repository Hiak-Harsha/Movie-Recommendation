"""
CineMatch Data Loader
Handles data ingestion, file resolution, schema validation, type casting,
and data health verification for the MovieLens dataset.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
import pandas as pd
import numpy as np

import config


class DataValidationError(Exception):
    """Raised when dataset files or columns fail validation checks."""
    pass


@dataclass
class DataHealthReport:
    """Detailed audit report on data integrity and cleanliness."""
    raw_movie_count: int = 0
    raw_rating_count: int = 0
    raw_tag_count: int = 0
    raw_link_count: int = 0
    
    clean_movie_count: int = 0
    clean_rating_count: int = 0
    clean_tag_count: int = 0
    clean_user_count: int = 0
    
    missing_values: Dict[str, Dict[str, int]] = field(default_factory=dict)
    duplicate_rows: Dict[str, int] = field(default_factory=dict)
    
    orphan_ratings_count: int = 0
    orphan_tags_count: int = 0
    unrated_movies_count: int = 0
    
    no_genres_count: int = 0
    duplicate_titles_count: int = 0
    
    rating_range: Tuple[float, float] = (0.0, 0.0)
    data_directory: str = ""
    issues_detected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health report to dictionary for UI and logging."""
        return {
            "data_directory": self.data_directory,
            "raw_counts": {
                "movies": self.raw_movie_count,
                "ratings": self.raw_rating_count,
                "tags": self.raw_tag_count,
                "links": self.raw_link_count,
            },
            "clean_counts": {
                "valid_movies": self.clean_movie_count,
                "valid_ratings": self.clean_rating_count,
                "valid_tags": self.clean_tag_count,
                "unique_users": self.clean_user_count,
            },
            "unrated_movies": self.unrated_movies_count,
            "orphan_ratings": self.orphan_ratings_count,
            "orphan_tags": self.orphan_tags_count,
            "no_genres_count": self.no_genres_count,
            "duplicate_titles_count": self.duplicate_titles_count,
            "rating_range": self.rating_range,
            "missing_values": self.missing_values,
            "duplicates": self.duplicate_rows,
            "issues": self.issues_detected,
        }


def resolve_data_directory(custom_path: Optional[str | Path] = None) -> Path:
    """
    Locates the directory containing required MovieLens CSV files.
    If custom_path is provided, checks that specific directory.
    Otherwise, checks candidate paths from config.
    """
    if custom_path is not None:
        candidates = [Path(custom_path)]
    else:
        candidates = list(config.DATA_CANDIDATE_PATHS)

    for path in candidates:
        if path.is_dir():
            movies_file = path / config.MOVIES_FILENAME
            ratings_file = path / config.RATINGS_FILENAME
            if movies_file.exists() and ratings_file.exists():
                return path.resolve()

    searched = [str(p) for p in candidates]
    raise FileNotFoundError(
        f"Could not locate MovieLens dataset with required files '{config.MOVIES_FILENAME}' "
        f"and '{config.RATINGS_FILENAME}'. Searched locations: {', '.join(searched)}. "
        f"Please verify your dataset directory structure."
    )


def load_raw_data(data_dir: Optional[str | Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], Path]:
    """
    Loads raw CSV files from the resolved directory without silent modifications.
    Validates required column schemas.
    """
    resolved_dir = resolve_data_directory(data_dir)

    movies_path = resolved_dir / config.MOVIES_FILENAME
    ratings_path = resolved_dir / config.RATINGS_FILENAME
    tags_path = resolved_dir / config.TAGS_FILENAME
    links_path = resolved_dir / config.LINKS_FILENAME

    if not movies_path.exists():
        raise FileNotFoundError(f"Missing required file: '{config.MOVIES_FILENAME}' in {resolved_dir}")
    if not ratings_path.exists():
        raise FileNotFoundError(f"Missing required file: '{config.RATINGS_FILENAME}' in {resolved_dir}")

    # Read movies
    try:
        movies_df = pd.read_csv(movies_path, encoding="utf-8")
    except UnicodeDecodeError:
        movies_df = pd.read_csv(movies_path, encoding="latin1")

    # Read ratings
    ratings_df = pd.read_csv(ratings_path, encoding="utf-8")

    # Read tags (optional but expected)
    if tags_path.exists():
        try:
            tags_df = pd.read_csv(tags_path, encoding="utf-8")
        except UnicodeDecodeError:
            tags_df = pd.read_csv(tags_path, encoding="latin1")
    else:
        tags_df = pd.DataFrame(columns=["userId", "movieId", "tag", "timestamp"])

    # Read links (optional)
    links_df = None
    if links_path.exists():
        links_df = pd.read_csv(links_path)

    # Validate Schema
    required_movie_cols = {"movieId", "title", "genres"}
    if not required_movie_cols.issubset(set(movies_df.columns)):
        missing = required_movie_cols - set(movies_df.columns)
        raise DataValidationError(f"'{config.MOVIES_FILENAME}' is missing required columns: {missing}")

    required_rating_cols = {"userId", "movieId", "rating", "timestamp"}
    if not required_rating_cols.issubset(set(ratings_df.columns)):
        missing = required_rating_cols - set(ratings_df.columns)
        raise DataValidationError(f"'{config.RATINGS_FILENAME}' is missing required columns: {missing}")

    if not tags_df.empty:
        required_tag_cols = {"userId", "movieId", "tag", "timestamp"}
        if not required_tag_cols.issubset(set(tags_df.columns)):
            missing = required_tag_cols - set(tags_df.columns)
            raise DataValidationError(f"'{config.TAGS_FILENAME}' is missing required columns: {missing}")

    return movies_df, ratings_df, tags_df, links_df, resolved_dir


def validate_and_clean_data(
    movies_raw: pd.DataFrame,
    ratings_raw: pd.DataFrame,
    tags_raw: pd.DataFrame,
    links_raw: Optional[pd.DataFrame] = None,
    data_dir_path: str = ""
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame], DataHealthReport]:
    """
    Cleans and standardizes raw DataFrames according to explicit documented rules:
    - Removes duplicate rows
    - Validates data types and ranges
    - Handles missing values without inventing attributes
    - Verifies ID integrity between ratings/tags and movies
    - Records an exhaustive DataHealthReport
    """
    report = DataHealthReport()
    report.data_directory = str(data_dir_path)
    report.raw_movie_count = len(movies_raw)
    report.raw_rating_count = len(ratings_raw)
    report.raw_tag_count = len(tags_raw)
    report.raw_link_count = len(links_raw) if links_raw is not None else 0

    # 1. Null counts audit
    report.missing_values["movies"] = {col: int(movies_raw[col].isnull().sum()) for col in movies_raw.columns}
    report.missing_values["ratings"] = {col: int(ratings_raw[col].isnull().sum()) for col in ratings_raw.columns}
    report.missing_values["tags"] = {col: int(tags_raw[col].isnull().sum()) for col in tags_raw.columns}
    if links_raw is not None:
        report.missing_values["links"] = {col: int(links_raw[col].isnull().sum()) for col in links_raw.columns}

    # 2. Duplicate audit
    report.duplicate_rows["movies_exact"] = int(movies_raw.duplicated().sum())
    report.duplicate_rows["ratings_exact"] = int(ratings_raw.duplicated().sum())
    report.duplicate_rows["tags_exact"] = int(tags_raw.duplicated().sum())

    # Check duplicate (userId, movieId) in ratings
    dup_ratings_user_movie = int(ratings_raw.duplicated(subset=["userId", "movieId"]).sum())
    report.duplicate_rows["ratings_duplicate_user_movie"] = dup_ratings_user_movie

    # --- CLEAN MOVIES ---
    movies_clean = movies_raw.copy()
    # Drop rows missing movieId or title
    movies_clean = movies_clean.dropna(subset=["movieId", "title"])
    # Cast movieId to int
    movies_clean["movieId"] = pd.to_numeric(movies_clean["movieId"], errors="coerce")
    movies_clean = movies_clean.dropna(subset=["movieId"])
    movies_clean["movieId"] = movies_clean["movieId"].astype(np.int64)
    # Deduplicate on movieId keeping first
    movies_clean = movies_clean.drop_duplicates(subset=["movieId"])
    
    # Handle missing genres: replace NaN with empty string
    movies_clean["genres"] = movies_clean["genres"].fillna("").astype(str).str.strip()
    report.no_genres_count = int((movies_clean["genres"] == "(no genres listed)").sum() + (movies_clean["genres"] == "").sum())

    # Count duplicate titles (different movieIds with same title)
    report.duplicate_titles_count = int(movies_clean.duplicated(subset=["title"]).sum())
    if report.duplicate_titles_count > 0:
        report.issues_detected.append(
            f"Detected {report.duplicate_titles_count} duplicate movie titles with distinct movieIds. "
            f"Movie IDs will be strictly used as primary keys."
        )

    valid_movie_ids: Set[int] = set(movies_clean["movieId"].unique())

    # --- CLEAN RATINGS ---
    ratings_clean = ratings_raw.copy()
    ratings_clean = ratings_clean.dropna(subset=["userId", "movieId", "rating"])
    ratings_clean["userId"] = pd.to_numeric(ratings_clean["userId"], errors="coerce")
    ratings_clean["movieId"] = pd.to_numeric(ratings_clean["movieId"], errors="coerce")
    ratings_clean["rating"] = pd.to_numeric(ratings_clean["rating"], errors="coerce")
    ratings_clean = ratings_clean.dropna(subset=["userId", "movieId", "rating"])
    
    ratings_clean["userId"] = ratings_clean["userId"].astype(np.int64)
    ratings_clean["movieId"] = ratings_clean["movieId"].astype(np.int64)
    ratings_clean["rating"] = ratings_clean["rating"].astype(np.float64)

    # Cast timestamp if present
    if "timestamp" in ratings_clean.columns:
        ratings_clean["timestamp"] = pd.to_numeric(ratings_clean["timestamp"], errors="coerce").fillna(0).astype(np.int64)
    else:
        ratings_clean["timestamp"] = 0

    # Filter rating score range (0.5 to 5.0)
    valid_rating_mask = (ratings_clean["rating"] >= 0.5) & (ratings_clean["rating"] <= 5.0)
    invalid_ratings_count = int((~valid_rating_mask).sum())
    if invalid_ratings_count > 0:
        report.issues_detected.append(f"Dropped {invalid_ratings_count} ratings outside [0.5, 5.0] range.")
        ratings_clean = ratings_clean[valid_rating_mask]

    # Deduplicate (userId, movieId), keeping the latest timestamp rating if duplicates exist
    if dup_ratings_user_movie > 0:
        report.issues_detected.append(f"Deduplicating {dup_ratings_user_movie} duplicate (userId, movieId) rating records.")
        ratings_clean = ratings_clean.sort_values(by="timestamp").drop_duplicates(subset=["userId", "movieId"], keep="last")

    # Check for orphan ratings (referencing non-existent movieId)
    orphan_ratings = ratings_clean[~ratings_clean["movieId"].isin(valid_movie_ids)]
    report.orphan_ratings_count = len(orphan_ratings)
    if report.orphan_ratings_count > 0:
        report.issues_detected.append(
            f"Dropped {report.orphan_ratings_count} ratings referencing unknown movie IDs not in movies.csv."
        )
        ratings_clean = ratings_clean[ratings_clean["movieId"].isin(valid_movie_ids)]

    # Movies with no ratings
    rated_movie_ids = set(ratings_clean["movieId"].unique())
    report.unrated_movies_count = len(valid_movie_ids - rated_movie_ids)
    if report.unrated_movies_count > 0:
        report.issues_detected.append(
            f"{report.unrated_movies_count} movies have zero ratings in ratings.csv."
        )

    # Rating statistics
    if not ratings_clean.empty:
        report.rating_range = (float(ratings_clean["rating"].min()), float(ratings_clean["rating"].max()))

    # --- CLEAN TAGS ---
    tags_clean = tags_raw.copy()
    if not tags_clean.empty:
        tags_clean = tags_clean.dropna(subset=["userId", "movieId", "tag"])
        tags_clean["userId"] = pd.to_numeric(tags_clean["userId"], errors="coerce").dropna().astype(np.int64)
        tags_clean["movieId"] = pd.to_numeric(tags_clean["movieId"], errors="coerce").dropna().astype(np.int64)
        tags_clean["tag"] = tags_clean["tag"].astype(str).str.strip()
        tags_clean = tags_clean[tags_clean["tag"] != ""]
        if "timestamp" in tags_clean.columns:
            tags_clean["timestamp"] = pd.to_numeric(tags_clean["timestamp"], errors="coerce").fillna(0).astype(np.int64)
        else:
            tags_clean["timestamp"] = 0

        # Filter orphan tags
        orphan_tags = tags_clean[~tags_clean["movieId"].isin(valid_movie_ids)]
        report.orphan_tags_count = len(orphan_tags)
        if report.orphan_tags_count > 0:
            report.issues_detected.append(f"Dropped {report.orphan_tags_count} tags referencing unknown movie IDs.")
            tags_clean = tags_clean[tags_clean["movieId"].isin(valid_movie_ids)]
    else:
        tags_clean = pd.DataFrame(columns=["userId", "movieId", "tag", "timestamp"])

    # --- CLEAN LINKS ---
    links_clean = None
    if links_raw is not None and not links_raw.empty:
        links_clean = links_raw.copy()
        links_clean["movieId"] = pd.to_numeric(links_clean["movieId"], errors="coerce").dropna().astype(np.int64)
        links_clean = links_clean[links_clean["movieId"].isin(valid_movie_ids)]
        links_clean = links_clean.drop_duplicates(subset=["movieId"])

    # Final counts
    report.clean_movie_count = len(movies_clean)
    report.clean_rating_count = len(ratings_clean)
    report.clean_tag_count = len(tags_clean)
    report.clean_user_count = int(ratings_clean["userId"].nunique())

    return movies_clean, ratings_clean, tags_clean, links_clean, report
