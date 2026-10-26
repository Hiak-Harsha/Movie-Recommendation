"""
CineMatch Preprocessing Module
Extracts features, normalizes genres and tags, parses release years,
computes Bayesian popularity priors, and builds structured movie representations.
"""
import re
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

import config


def extract_year_from_title(title: str) -> Optional[int]:
    """
    Extracts 4-digit release year from parentheses in movie title, e.g. 'Toy Story (1995)' -> 1995.
    Returns None if no 4-digit year is found.
    """
    if not isinstance(title, str):
        return None
    match = re.search(r"\((\d{4})\)\s*$", title.strip())
    if match:
        year = int(match.group(1))
        # Sanity check year range for cinema history (1880 to 2030)
        if 1880 <= year <= 2030:
            return year
    # Fallback search anywhere in title
    match_fallback = re.search(r"\((\d{4})\)", title)
    if match_fallback:
        year = int(match_fallback.group(1))
        if 1880 <= year <= 2030:
            return year
    return None


def clean_title_for_display(title: str) -> str:
    """
    Returns original title with stripped whitespace.
    Preserves original title formatting and articles.
    """
    if not isinstance(title, str):
        return ""
    return title.strip()


def parse_genres(genres_str: str) -> List[str]:
    """
    Parses pipe-separated genre string into a list of clean genre names.
    Ignores '(no genres listed)' and empty strings.
    """
    if not isinstance(genres_str, str) or not genres_str.strip():
        return []
    parts = [g.strip() for g in genres_str.split("|")]
    valid_genres = [g for g in parts if g and g.lower() != "(no genres listed)"]
    return valid_genres


def normalize_genres_for_text(genres_list: List[str]) -> str:
    """
    Normalizes genre list for TF-IDF tokenization.
    Transforms compound words: 'Sci-Fi' -> 'sci_fi', 'Film-Noir' -> 'film_noir'.
    """
    normalized = []
    for g in genres_list:
        clean = g.lower().replace("-", "_").replace(" ", "_")
        normalized.append(clean)
    return " ".join(normalized)


def clean_tag_text(tag: str) -> str:
    """
    Cleans individual tag text: lowercases, strips whitespace, converts hyphens/spaces.
    Avoids producing literal 'nan' strings.
    """
    if not isinstance(tag, str):
        return ""
    tag_clean = tag.strip().lower()
    if tag_clean in ("nan", "none", "null", ""):
        return ""
    # Standardize tag
    return re.sub(r"\s+", " ", tag_clean)


def aggregate_movie_tags(
    tags_df: pd.DataFrame,
    max_timestamp: Optional[int] = None
) -> Dict[int, str]:
    """
    Aggregates user tags per movieId into a single space-separated string.
    Supports temporal cutoff to prevent test-period leakage during evaluation.
    Returns {movieId: 'tag1 tag2 ...'}. Movies without tags have empty string.
    """
    if tags_df is None or tags_df.empty:
        return {}

    df = tags_df.copy()
    if max_timestamp is not None:
        df = df[df["timestamp"] <= max_timestamp]

    if df.empty:
        return {}

    # Clean tag text
    df["clean_tag"] = df["tag"].apply(clean_tag_text)
    df = df[df["clean_tag"] != ""]

    # Deduplicate tags per movie (so repeated tags don't artificially over-inflate TF-IDF without reason)
    grouped = df.groupby("movieId")["clean_tag"].unique()
    return {int(mid): " ".join(tags) for mid, tags in grouped.items()}


def compute_popularity_metrics(
    ratings_train: pd.DataFrame,
    min_ratings_threshold: int = config.BAYESIAN_MIN_RATINGS
) -> Tuple[pd.DataFrame, float, float]:
    """
    Computes movie popularity statistics strictly from training ratings.
    Uses Bayesian smoothing (IMDb formula):
        weighted_rating = (v / (v + m)) * R + (m / (v + m)) * C
    Where:
        R = average rating of the movie
        v = number of training ratings for the movie
        m = minimum rating threshold (BAYESIAN_MIN_RATINGS)
        C = overall global mean training rating
    
    Returns:
        metrics_df with columns: ['movieId', 'rating_count', 'mean_rating', 'weighted_rating', 'popularity_score']
        global_mean_rating (C)
        min_threshold (m)
    """
    if ratings_train.empty:
        return pd.DataFrame(columns=["movieId", "rating_count", "mean_rating", "weighted_rating", "popularity_score"]), 0.0, float(min_ratings_threshold)

    # Compute global mean rating C
    global_mean = float(ratings_train["rating"].mean())
    m = float(min_ratings_threshold)

    # Group by movie
    stats = ratings_train.groupby("movieId")["rating"].agg(
        rating_count="count",
        mean_rating="mean"
    ).reset_index()

    v = stats["rating_count"].astype(float)
    R = stats["mean_rating"].astype(float)

    # Bayesian weighted rating
    stats["weighted_rating"] = (v / (v + m)) * R + (m / (v + m)) * global_mean

    # Normalize popularity_score to [0.0, 1.0] range
    # 0.5 stars -> 0.0, 5.0 stars -> 1.0
    stats["popularity_score"] = ((stats["weighted_rating"] - 0.5) / 4.5).clip(0.0, 1.0)

    return stats, global_mean, m


def build_movie_catalog(
    movies_df: pd.DataFrame,
    tags_df: Optional[pd.DataFrame] = None,
    popularity_df: Optional[pd.DataFrame] = None,
    max_tag_timestamp: Optional[int] = None
) -> pd.DataFrame:
    """
    Enriches movies_df with:
    - clean_title
    - release_year
    - genres_list (parsed python list)
    - genres_display (e.g. 'Action, Adventure' or 'No genres listed')
    - genres_tokens (normalized for TF-IDF: 'action adventure')
    - tags_tokens (aggregated tags text without nan tokens)
    - content_soup (combined normalized genres + tags text)
    - rating_count, mean_rating, weighted_rating, popularity_score (if popularity_df provided)
    """
    df = movies_df.copy()

    # Title cleaning & year extraction
    df["clean_title"] = df["title"].apply(clean_title_for_display)
    df["release_year"] = df["title"].apply(extract_year_from_title)

    # Genre parsing
    df["genres_list"] = df["genres"].apply(parse_genres)
    df["genres_display"] = df["genres_list"].apply(
        lambda gl: ", ".join(gl) if gl else "No genres listed"
    )
    df["genres_tokens"] = df["genres_list"].apply(normalize_genres_for_text)

    # Tag aggregation
    movie_tags_map = aggregate_movie_tags(tags_df, max_timestamp=max_tag_timestamp) if tags_df is not None else {}
    df["tags_tokens"] = df["movieId"].map(lambda mid: movie_tags_map.get(mid, ""))

    # Content soup (genres repeated twice for appropriate feature weighting relative to sparse tags)
    df["content_soup"] = df.apply(
        lambda row: f"{row['genres_tokens']} {row['genres_tokens']} {row['tags_tokens']}".strip(),
        axis=1
    )

    # Merge popularity metrics if available
    if popularity_df is not None and not popularity_df.empty:
        df = df.merge(
            popularity_df[["movieId", "rating_count", "mean_rating", "weighted_rating", "popularity_score"]],
            on="movieId",
            how="left"
        )
        df["rating_count"] = df["rating_count"].fillna(0).astype(int)
        df["mean_rating"] = df["mean_rating"].fillna(0.0).round(2)
        df["weighted_rating"] = df["weighted_rating"].fillna(0.0).round(2)
        df["popularity_score"] = df["popularity_score"].fillna(0.0).round(4)
    else:
        df["rating_count"] = 0
        df["mean_rating"] = 0.0
        df["weighted_rating"] = 0.0
        df["popularity_score"] = 0.0

    return df
