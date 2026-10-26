"""
CineMatch Preprocessing Module
Extracts display titles, release years, search keys, atomic genre & tag tokens,
decade tokens, and Bayesian popularity priors from training data.
"""
import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd
import numpy as np

import config


def extract_year_from_title(title: str) -> Optional[int]:
    """
    Extracts 4-digit release year from trailing parentheses in movie title.
    Example: 'Toy Story (1995)' -> 1995.
    Returns None if no valid year is found.
    """
    if not isinstance(title, str):
        return None
    match = re.search(r"\((\d{4})\)\s*$", title.strip())
    if match:
        year = int(match.group(1))
        if 1880 <= year <= 2035:
            return year
    # Fallback search anywhere in title
    match_anywhere = re.search(r"\((\d{4})\)", title)
    if match_anywhere:
        year = int(match_anywhere.group(1))
        if 1880 <= year <= 2035:
            return year
    return None


def parse_display_title(title: str) -> str:
    """
    Formats MovieLens titles to standard display format by moving trailing articles.
    Examples:
        'Matrix, The (1999)' -> 'The Matrix (1999)'
        'Clockwork Orange, A (1971)' -> 'A Clockwork Orange (1971)'
        'Affair to Remember, An (1957)' -> 'An Affair to Remember (1957)'
    """
    if not isinstance(title, str):
        return ""
    t = title.strip()
    match = re.search(r"^(.*?),\s*(The|A|An)\s*(\(.*\))?$", t, re.IGNORECASE)
    if match:
        main_part = match.group(1).strip()
        article = match.group(2).capitalize()
        paren = match.group(3) or ""
        paren_clean = paren.strip()
        if paren_clean:
            return f"{article} {main_part} {paren_clean}"
        return f"{article} {main_part}"
    return t


def build_search_key(title: str) -> str:
    """
    Constructs an article-agnostic, accent-stripped, lowercase search key for robust search.
    Examples:
        'The Matrix (1999)' -> 'matrix'
        'Matrix, The (1999)' -> 'matrix'
        'Amélie (2001)' -> 'amelie'
    """
    if not isinstance(title, str):
        return ""
    # Strip year in parens at the end
    t = re.sub(r"\s*\(\d{4}\)\s*$", "", title.strip()).lower()
    # Strip trailing articles ', the', ', a', ', an'
    t = re.sub(r",\s*(the|a|an)$", "", t)
    # Strip leading articles 'the ', 'a ', 'an '
    t = re.sub(r"^(the|a|an)\s+", "", t)
    # Normalize unicode accents to ascii
    t = unicodedata.normalize("NFKD", t).encode("ASCII", "ignore").decode("utf-8")
    # Replace punctuation with space
    t = re.sub(r"[^\w\s]", " ", t)
    # Collapse whitespace
    return " ".join(t.split())


def parse_genres(genres_str: str) -> List[str]:
    """
    Parses pipe-separated genre string into a list of clean genre names.
    Treats '(no genres listed)' and empty strings as an empty list.
    """
    if not isinstance(genres_str, str) or not genres_str.strip():
        return []
    parts = [g.strip() for g in genres_str.split("|")]
    valid_genres = [g for g in parts if g and g.lower() != "(no genres listed)"]
    return valid_genres


def normalize_genres_for_tokens(genres_list: List[str]) -> str:
    """
    Converts genre list into atomic feature tokens.
    Keeps compound terms atomic: 'Sci-Fi' -> 'sci_fi', 'Film-Noir' -> 'film_noir', 'IMAX' -> 'imax'.
    """
    tokens = []
    for g in genres_list:
        clean = g.strip().lower().replace("-", "_").replace(" ", "_")
        if clean:
            tokens.append(clean)
    return " ".join(tokens)


def extract_decade_token(year: Optional[int]) -> str:
    """Generates an atomic decade token for content representation, e.g. 1995 -> 'decade_1990s'."""
    if year is None:
        return ""
    decade = (year // 10) * 10
    return f"decade_{decade}s"


def clean_atomic_tag(tag: str) -> str:
    """
    Sanitizes tag text: lowercases, strips, and converts multi-word spaces to underscores.
    Prevents splitting of atomic phrases (e.g. 'mind-bending' -> 'mind_bending', 'highly quotable' -> 'highly_quotable').
    Returns empty string for null/nan tokens.
    """
    if not isinstance(tag, str):
        return ""
    clean = tag.strip().lower()
    if clean in ("nan", "none", "null", ""):
        return ""
    # Normalize accents
    clean = unicodedata.normalize("NFKD", clean).encode("ASCII", "ignore").decode("utf-8")
    # Replace hyphens and spaces with underscores to preserve multi-word tag as single atomic token
    clean = re.sub(r"[\s\-]+", "_", clean)
    clean = re.sub(r"[^\w_]", "", clean)
    return clean


def aggregate_movie_tags(
    tags_df: pd.DataFrame,
    max_timestamp: Optional[int] = None,
    min_movies: int = config.TAG_MIN_MOVIES,
    min_users: int = config.TAG_MIN_USERS
) -> Dict[int, str]:
    """
    Aggregates atomic tags per movieId.
    Supports strict timestamp cutoff (< max_timestamp) for zero-leakage evaluation.
    Filters tags appearing in fewer than min_movies or min_users.
    """
    if tags_df is None or tags_df.empty:
        return {}

    df = tags_df.copy()
    if max_timestamp is not None:
        df = df[df["timestamp"] < max_timestamp]

    if df.empty:
        return {}

    df["atomic_tag"] = df["tag"].apply(clean_atomic_tag)
    df = df[df["atomic_tag"] != ""]

    if df.empty:
        return {}

    # Filter tags by minimum distinct movies and users if specified
    if min_movies > 1 or min_users > 1:
        tag_stats = df.groupby("atomic_tag").agg(
            n_movies=("movieId", "nunique"),
            n_users=("userId", "nunique")
        )
        valid_tags = set(
            tag_stats[
                (tag_stats["n_movies"] >= min_movies) & (tag_stats["n_users"] >= min_users)
            ].index
        )
        df = df[df["atomic_tag"].isin(valid_tags)]

    if df.empty:
        return {}

    # Deduplicate atomic tags per movie
    grouped = df.groupby("movieId")["atomic_tag"].unique()
    return {int(mid): " ".join(tags) for mid, tags in grouped.items()}


def compute_popularity_metrics(
    ratings_train: pd.DataFrame,
    percentile: int = config.BAYESIAN_PERCENTILE
) -> Tuple[pd.DataFrame, float, float]:
    """
    Computes Bayesian smoothed movie rating statistics strictly from training ratings.
    Formula:
        weighted_rating = (v / (v + m)) * R + (m / (v + m)) * C
    Where:
        R = average training rating of the movie
        v = number of training ratings for the movie
        m = threshold dynamically selected at the given percentile of rating counts
        C = overall global mean training rating
    
    Returns:
        metrics_df with columns: ['movieId', 'rating_count', 'mean_rating', 'weighted_rating', 'popularity_score']
        global_mean_rating (C)
        min_threshold (m)
    """
    if ratings_train.empty:
        cols = ["movieId", "rating_count", "mean_rating", "weighted_rating", "popularity_score"]
        return pd.DataFrame(columns=cols), 0.0, float(config.FALLBACK_BAYESIAN_MIN_RATINGS)

    global_mean = float(ratings_train["rating"].mean())

    stats = ratings_train.groupby("movieId")["rating"].agg(
        rating_count="count",
        mean_rating="mean"
    ).reset_index()

    v = stats["rating_count"].astype(float)
    R = stats["mean_rating"].astype(float)

    # Compute m at the specified percentile of training rating counts
    if len(v) > 0:
        m = float(np.percentile(v, percentile))
        if m < 1.0:
            m = float(config.FALLBACK_BAYESIAN_MIN_RATINGS)
    else:
        m = float(config.FALLBACK_BAYESIAN_MIN_RATINGS)

    stats["weighted_rating"] = (v / (v + m)) * R + (m / (v + m)) * global_mean

    # Fixed-scale linear normalization to [0.0, 1.0] via (WR - 0.5) / 4.5
    # Pool-independent, avoiding shifts when candidates are filtered
    stats["popularity_score"] = ((stats["weighted_rating"] - 0.5) / 4.5).clip(0.0, 1.0)

    return stats, global_mean, m


def build_movie_catalog(
    movies_df: pd.DataFrame,
    tags_df: Optional[pd.DataFrame] = None,
    popularity_df: Optional[pd.DataFrame] = None,
    links_df: Optional[pd.DataFrame] = None,
    max_tag_timestamp: Optional[int] = None
) -> pd.DataFrame:
    """
    Enriches movies_df into a unified catalog with:
    - title (original MovieLens title)
    - display_title (e.g. 'The Matrix (1999)')
    - release_year
    - search_key (article-agnostic, accent-stripped)
    - genres_list, genres_display
    - genre_tokens (atomic compound genres)
    - decade_token
    - tags_tokens (atomic user tags)
    - imdb_id, tmdb_id (from links_df)
    - rating_count, mean_rating, weighted_rating, popularity_score (from training popularity_df)
    """
    df = movies_df.copy()

    # Title parsing
    df["display_title"] = df["title"].apply(parse_display_title)
    df["release_year"] = df["title"].apply(extract_year_from_title)
    df["search_key"] = df["title"].apply(build_search_key)

    # Genre normalization
    df["genres_list"] = df["genres"].apply(parse_genres)
    df["genres_display"] = df["genres_list"].apply(
        lambda gl: ", ".join(gl) if gl else "No genres listed"
    )
    df["genre_tokens"] = df["genres_list"].apply(normalize_genres_for_tokens)
    df["decade_token"] = df["release_year"].apply(extract_decade_token)

    # Tag aggregation with optional temporal cutoff
    movie_tags_map = aggregate_movie_tags(tags_df, max_timestamp=max_tag_timestamp) if tags_df is not None else {}
    df["tags_tokens"] = df["movieId"].map(lambda mid: movie_tags_map.get(mid, ""))

    # Links integration
    if links_df is not None and not links_df.empty:
        links_sub = links_df[["movieId", "imdbId", "tmdbId"]].copy()
        df = df.merge(links_sub, on="movieId", how="left")
    else:
        df["imdbId"] = None
        df["tmdbId"] = None

    # Popularity stats integration
    if popularity_df is not None and not popularity_df.empty:
        pop_sub = popularity_df[["movieId", "rating_count", "mean_rating", "weighted_rating", "popularity_score"]]
        df = df.merge(pop_sub, on="movieId", how="left")
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
