"""
CineMatch Data Loader & Validation Module
Handles dataset loading, strict schema validation, timestamp deduplication,
fingerprinting, and data health auditing without any machine-specific paths.
"""
from dataclasses import dataclass, field
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

from ml.config import settings

logger = logging.getLogger("cinematch.ml.data_loader")


class DataValidationError(Exception):
    """Custom exception raised when MovieLens dataset files or schemas fail validation."""
    pass


@dataclass
class DataHealthReport:
    """Comprehensive data health audit report (free of personal machine paths)."""
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
    
    dropped_ratings_invalid_score: int = 0
    dropped_ratings_duplicate_user_movie: int = 0
    orphan_ratings_count: int = 0
    orphan_tags_count: int = 0
    unrated_movies_count: int = 0
    
    no_genres_count: int = 0
    duplicate_titles_count: int = 0
    
    rating_range: Tuple[float, float] = (0.0, 0.0)
    rating_timestamp_range: Tuple[int, int] = (0, 0)
    tag_timestamp_range: Tuple[int, int] = (0, 0)
    sparsity_percentage: float = 0.0
    
    data_directory: str = ""
    dataset_fingerprint: str = ""
    issues_detected: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert health report to dictionary for UI and logging."""
        return {
            "data_directory": self.data_directory,
            "dataset_fingerprint": self.dataset_fingerprint,
            "counts": {
                "raw_movies": self.raw_movie_count,
                "clean_movies": self.clean_movie_count,
                "raw_ratings": self.raw_rating_count,
                "clean_ratings": self.clean_rating_count,
                "raw_tags": self.raw_tag_count,
                "clean_tags": self.clean_tag_count,
                "clean_users": self.clean_user_count,
            },
            "data_quality": {
                "missing_values": self.missing_values,
                "duplicates": self.duplicate_rows,
                "dropped_ratings_invalid": self.dropped_ratings_invalid_score,
                "dropped_ratings_duplicate_user_movie": self.dropped_ratings_duplicate_user_movie,
                "orphan_ratings": self.orphan_ratings_count,
                "orphan_tags": self.orphan_tags_count,
                "unrated_movies": self.unrated_movies_count,
                "no_genres_count": self.no_genres_count,
                "duplicate_titles_count": self.duplicate_titles_count,
            },
            "metrics": {
                "rating_range": list(self.rating_range),
                "rating_timestamp_range": list(self.rating_timestamp_range),
                "tag_timestamp_range": list(self.tag_timestamp_range),
                "sparsity_percentage": self.sparsity_percentage,
            },
            "issues": self.issues_detected,
        }


def resolve_data_directory(custom_path: Optional[Path] = None) -> Path:
    """Resolves data directory strictly without hardcoded machine paths."""
    if custom_path is not None:
        p = Path(custom_path).resolve()
        if p.exists() and p.is_dir():
            return p
        raise FileNotFoundError(f"Custom data directory does not exist: {custom_path}")

    candidates = [
        settings.data_dir,
        settings.project_root / "data",
        settings.project_root / "ml-latest-small" / "ml-latest-small",
        settings.project_root / "ml-latest-small",
    ]
    for c in candidates:
        if c.exists() and (c / settings.movies_filename).exists() and (c / settings.ratings_filename).exists():
            return c.resolve()

    raise FileNotFoundError("Could not locate MovieLens dataset directory containing movies.csv and ratings.csv.")


def compute_dataset_fingerprint(data_dir: Path) -> str:
    """Computes a deterministic MD5 hash fingerprint from file sizes and mtimes."""
    hasher = hashlib.md5()
    files_to_hash = [
        settings.movies_filename,
        settings.ratings_filename,
        settings.tags_filename,
        settings.links_filename,
    ]
    for filename in sorted(files_to_hash):
        file_path = data_dir / filename
        if file_path.exists():
            stat = file_path.stat()
            meta_str = f"{filename}:{stat.st_size}:{int(stat.st_mtime)}"
            hasher.update(meta_str.encode("utf-8"))
    return hasher.hexdigest()[:16]


def load_raw_data(data_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Loads CSV files and enforces required schemas."""
    movies_path = data_dir / settings.movies_filename
    ratings_path = data_dir / settings.ratings_filename
    tags_path = data_dir / settings.tags_filename
    links_path = data_dir / settings.links_filename

    if not movies_path.exists():
        raise DataValidationError(f"Required movies file missing: {movies_path.name}")
    if not ratings_path.exists():
        raise DataValidationError(f"Required ratings file missing: {ratings_path.name}")

    movies = pd.read_csv(movies_path)
    ratings = pd.read_csv(ratings_path)
    tags = pd.read_csv(tags_path) if tags_path.exists() else pd.DataFrame(columns=["userId", "movieId", "tag", "timestamp"])
    links = pd.read_csv(links_path) if links_path.exists() else pd.DataFrame(columns=["movieId", "imdbId", "tmdbId"])

    req_movies = {"movieId", "title", "genres"}
    if not req_movies.issubset(movies.columns):
        raise DataValidationError(f"movies.csv missing required columns: {req_movies - set(movies.columns)}")

    req_ratings = {"userId", "movieId", "rating", "timestamp"}
    if not req_ratings.issubset(ratings.columns):
        raise DataValidationError(f"ratings.csv missing required columns: {req_ratings - set(ratings.columns)}")

    return movies, ratings, tags, links


def validate_and_clean_data(
    movies_df: pd.DataFrame,
    ratings_df: pd.DataFrame,
    tags_df: pd.DataFrame,
    links_df: pd.DataFrame,
    data_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, DataHealthReport]:
    """Cleans raw data and produces a verified DataHealthReport without personal paths."""
    sanitized_dir_name = data_dir.name if data_dir else "data"
    fingerprint = compute_dataset_fingerprint(data_dir) if data_dir else "mock_fingerprint"

    report = DataHealthReport(
        raw_movie_count=len(movies_df),
        raw_rating_count=len(ratings_df),
        raw_tag_count=len(tags_df),
        raw_link_count=len(links_df),
        data_directory=f"{sanitized_dir_name}/",
        dataset_fingerprint=fingerprint,
    )

    # 1. Clean Movies
    clean_movies = movies_df.dropna(subset=["movieId", "title"]).copy()
    clean_movies["movieId"] = pd.to_numeric(clean_movies["movieId"], errors="coerce")
    clean_movies = clean_movies.dropna(subset=["movieId"]).copy()
    clean_movies["movieId"] = clean_movies["movieId"].astype(np.int32)
    clean_movies = clean_movies.drop_duplicates(subset=["movieId"], keep="first")
    valid_movie_ids = set(clean_movies["movieId"])

    # 2. Clean Ratings
    clean_ratings = ratings_df.dropna(subset=["userId", "movieId", "rating"]).copy()
    clean_ratings["userId"] = pd.to_numeric(clean_ratings["userId"], errors="coerce")
    clean_ratings["movieId"] = pd.to_numeric(clean_ratings["movieId"], errors="coerce")
    clean_ratings["rating"] = pd.to_numeric(clean_ratings["rating"], errors="coerce")
    clean_ratings = clean_ratings.dropna(subset=["userId", "movieId", "rating"]).copy()

    clean_ratings["userId"] = clean_ratings["userId"].astype(np.int32)
    clean_ratings["movieId"] = clean_ratings["movieId"].astype(np.int32)
    clean_ratings["rating"] = clean_ratings["rating"].astype(np.float32)
    if "timestamp" in clean_ratings.columns:
        clean_ratings["timestamp"] = pd.to_numeric(clean_ratings["timestamp"], errors="coerce").fillna(0).astype(np.int64)

    # Filter rating scale [0.5, 5.0]
    valid_scale_mask = (clean_ratings["rating"] >= 0.5) & (clean_ratings["rating"] <= 5.0)
    report.dropped_ratings_invalid_score = int((~valid_scale_mask).sum())
    clean_ratings = clean_ratings[valid_scale_mask]

    # Filter orphan ratings
    valid_movie_mask = clean_ratings["movieId"].isin(valid_movie_ids)
    report.orphan_ratings_count = int((~valid_movie_mask).sum())
    clean_ratings = clean_ratings[valid_movie_mask]

    # Deduplicate ratings keeping latest timestamp
    if "timestamp" in clean_ratings.columns:
        clean_ratings = clean_ratings.sort_values(by="timestamp", ascending=True)
    dupe_mask = clean_ratings.duplicated(subset=["userId", "movieId"], keep="last")
    report.dropped_ratings_duplicate_user_movie = int(dupe_mask.sum())
    clean_ratings = clean_ratings[~dupe_mask]

    # 3. Clean Tags
    clean_tags = tags_df.dropna(subset=["movieId", "tag"]).copy()
    clean_tags["movieId"] = pd.to_numeric(clean_tags["movieId"], errors="coerce")
    clean_tags = clean_tags.dropna(subset=["movieId"]).copy()
    clean_tags["movieId"] = clean_tags["movieId"].astype(np.int32)
    clean_tags = clean_tags[clean_tags["movieId"].isin(valid_movie_ids)]
    clean_tags["tag"] = clean_tags["tag"].astype(str).str.strip().str.lower()
    clean_tags = clean_tags[clean_tags["tag"].str.len() > 0]
    clean_tags = clean_tags[clean_tags["tag"] != "nan"]
    if "userId" in clean_tags.columns:
        clean_tags["userId"] = pd.to_numeric(clean_tags["userId"], errors="coerce").fillna(0).astype(np.int32)
        clean_tags = clean_tags.drop_duplicates(subset=["userId", "movieId", "tag"], keep="first")
    else:
        clean_tags = clean_tags.drop_duplicates(subset=["movieId", "tag"], keep="first")

    # 4. Clean Links
    clean_links = links_df.dropna(subset=["movieId"]).copy()
    clean_links["movieId"] = pd.to_numeric(clean_links["movieId"], errors="coerce")
    clean_links = clean_links.dropna(subset=["movieId"]).copy()
    clean_links["movieId"] = clean_links["movieId"].astype(np.int32)
    clean_links = clean_links[clean_links["movieId"].isin(valid_movie_ids)]
    clean_links = clean_links.drop_duplicates(subset=["movieId"], keep="first")

    # Update Health Report
    report.clean_movie_count = len(clean_movies)
    report.clean_rating_count = len(clean_ratings)
    report.clean_tag_count = len(clean_tags)
    report.clean_user_count = int(clean_ratings["userId"].nunique())
    
    rated_movie_ids = set(clean_ratings["movieId"].unique())
    report.unrated_movies_count = len(valid_movie_ids - rated_movie_ids)
    
    no_genre_mask = clean_movies["genres"].isna() | (clean_movies["genres"].str.strip() == "") | (clean_movies["genres"] == "(no genres listed)")
    report.no_genres_count = int(no_genre_mask.sum())

    if len(clean_ratings) > 0:
        report.rating_range = (float(clean_ratings["rating"].min()), float(clean_ratings["rating"].max()))
        if "timestamp" in clean_ratings.columns:
            report.rating_timestamp_range = (int(clean_ratings["timestamp"].min()), int(clean_ratings["timestamp"].max()))
    if len(clean_tags) > 0 and "timestamp" in clean_tags.columns:
        report.tag_timestamp_range = (int(clean_tags["timestamp"].min()), int(clean_tags["timestamp"].max()))

    n_users = report.clean_user_count
    n_movies = len(rated_movie_ids)
    if n_users > 0 and n_movies > 0:
        total_possible = n_users * n_movies
        sparsity = (1.0 - (len(clean_ratings) / total_possible)) * 100.0
        report.sparsity_percentage = round(float(sparsity), 2)

    return clean_movies, clean_ratings, clean_tags, clean_links, report
