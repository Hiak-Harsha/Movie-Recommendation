"""
CineMatch Preprocessing Module
Extracts release years, normalizes titles, builds atomic genre and tag tokens,
computes Bayesian popularity priors, and generates computed demo profiles.
"""
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from ml.config import settings

YEAR_REGEX = re.compile(r"\((\d{4})\)\s*$")
TRAILING_ARTICLE_REGEX = re.compile(r"^(.*?),\s*(The|A|An)(\s*\(.*?\))?$", re.IGNORECASE)


def parse_display_title(raw_title: str) -> Tuple[str, Optional[int]]:
    """
    Parses MovieLens title formatting into display title and 4-digit release year.
    Examples:
        'Matrix, The (1999)' -> ('The Matrix (1999)', 1999)
        'Seven (a.k.a. Se7en) (1995)' -> ('Seven (a.k.a. Se7en) (1995)', 1995)
    """
    if not isinstance(raw_title, str) or not raw_title.strip():
        return "", None

    title_str = raw_title.strip()
    year: Optional[int] = None
    year_match = YEAR_REGEX.search(title_str)
    if year_match:
        try:
            year = int(year_match.group(1))
        except ValueError:
            year = None

    article_match = TRAILING_ARTICLE_REGEX.match(title_str)
    if article_match:
        main_part = article_match.group(1).strip()
        article = article_match.group(2).strip().capitalize()
        year_part = article_match.group(3)
        year_suffix = year_part.strip() if year_part else ""
        if year_suffix:
            display_title = f"{article} {main_part} {year_suffix}"
        else:
            display_title = f"{article} {main_part}"
    else:
        display_title = title_str

    return display_title, year


def generate_search_key(text: str) -> str:
    """
    Generates a normalized, accent-stripped, article-agnostic search key.
    """
    if not isinstance(text, str):
        return ""

    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ASCII", "ignore").decode("utf-8").lower()
    cleaned = re.sub(r"[^\w\s]", " ", ascii_text)
    tokens = cleaned.split()

    if tokens and tokens[0] in {"the", "a", "an"}:
        tokens = tokens[1:]

    return " ".join(tokens)


def normalize_genres(genres_str: str) -> List[str]:
    """
    Splits genres into atomic tokens.
    Treats (no genres listed) as empty. Keeps 'Sci-Fi' -> 'sci_fi', 'Film-Noir' -> 'film_noir'.
    """
    if not isinstance(genres_str, str) or not genres_str.strip():
        return []

    raw_tokens = [g.strip() for g in genres_str.split("|")]
    tokens: List[str] = []

    for g in raw_tokens:
        if not g or g.lower() == "(no genres listed)":
            continue
        token = g.lower().replace("-", "_").replace(" ", "_")
        tokens.append(token)

    return tokens


def extract_decade_token(year: Optional[int]) -> str:
    """Returns decade token, e.g. 1994 -> 'decade_1990s'."""
    if year is None or year < 1880 or year > 2040:
        return ""
    decade = (year // 10) * 10
    return f"decade_{decade}s"


def compute_popularity_metrics(
    ratings_train: pd.DataFrame,
    percentile: int = settings.bayesian_percentile,
    fallback_m: float = settings.fallback_bayesian_m
) -> Dict[str, Any]:
    """
    Computes Bayesian weighted ratings:
        WR = (v / (v + m)) * R + (m / (v + m)) * C
    """
    if ratings_train.empty:
        return {
            "global_mean": 3.5,
            "m_threshold": fallback_m,
            "movie_stats": pd.DataFrame(columns=["movieId", "vote_count", "vote_average", "weighted_rating", "scaled_popularity"])
        }

    global_mean = float(ratings_train["rating"].mean())
    grouped = ratings_train.groupby("movieId")["rating"].agg(
        vote_count="count",
        vote_average="mean"
    ).reset_index()

    counts = grouped["vote_count"].values
    if len(counts) > 0 and len(counts[counts > 0]) > 0:
        m_threshold = float(np.percentile(counts, percentile))
        m_threshold = max(m_threshold, 3.0)
    else:
        m_threshold = fallback_m

    v = grouped["vote_count"].astype(float)
    r = grouped["vote_average"].astype(float)
    wr = (v / (v + m_threshold)) * r + (m_threshold / (v + m_threshold)) * global_mean
    grouped["weighted_rating"] = wr

    # Linear scaling to [0, 1] via (WR - 0.5) / 4.5
    scaled = np.clip((wr - 0.5) / 4.5, 0.0, 1.0)
    grouped["scaled_popularity"] = scaled

    return {
        "global_mean": global_mean,
        "m_threshold": m_threshold,
        "movie_stats": grouped
    }


def compute_demo_profiles(
    ratings_df: pd.DataFrame,
    catalog_df: pd.DataFrame,
    min_ratings: int = 50,
    n_profiles: int = 6
) -> List[Dict[str, Any]]:
    """
    Computes demo benchmark user profiles dynamically from data (top genres, decade, rating count).
    No hand-written labels (resolving defect D10).
    """
    user_counts = ratings_df.groupby("userId").size()
    eligible_users = user_counts[user_counts >= min_ratings].index.tolist()

    # Sample varied profiles (e.g. highest rating counts, medium counts)
    sorted_users = sorted(eligible_users, key=lambda u: user_counts[u], reverse=True)
    selected_uids = [sorted_users[i] for i in np.linspace(0, min(len(sorted_users) - 1, 40), n_profiles, dtype=int)]

    movie_meta = catalog_df.set_index("movieId")
    profiles = []

    for uid in selected_uids:
        u_ratings = ratings_df[ratings_df["userId"] == uid]
        high_ratings = u_ratings[u_ratings["rating"] >= 4.0]
        
        # Analyze top genres from high ratings
        genre_counter: Dict[str, int] = {}
        decade_counter: Dict[str, int] = {}
        for mid in high_ratings["movieId"]:
            if mid in movie_meta.index:
                row = movie_meta.loc[mid]
                if isinstance(row["genres_list"], list):
                    for g in row["genres_list"]:
                        genre_counter[g] = genre_counter.get(g, 0) + 1
                if pd.notna(row["year"]):
                    dec = (int(row["year"]) // 10) * 10
                    decade_counter[f"{dec}s"] = decade_counter.get(f"{dec}s", 0) + 1

        top_genres = sorted(genre_counter.keys(), key=lambda g: genre_counter[g], reverse=True)[:3]
        top_decade = max(decade_counter.keys(), key=lambda d: decade_counter[d]) if decade_counter else "Mixed"
        top_genres_str = " & ".join([g.replace("_", " ").title() for g in top_genres]) if top_genres else "General"
        computed_label = f"User #{uid} ({top_genres_str} · {top_decade} · {len(u_ratings)} ratings)"

        sample_ratings = dict(zip(u_ratings["movieId"].astype(int), u_ratings["rating"].astype(float)))

        profiles.append({
            "userId": int(uid),
            "label": computed_label,
            "rating_count": len(u_ratings),
            "top_genres": top_genres,
            "top_decade": top_decade,
            "avg_rating": round(float(u_ratings["rating"].mean()), 2),
            "ratings": sample_ratings
        })

    return profiles
