"""
CineMatch Content-Based Recommendation Engine
Builds sparse TF-IDF vectors from genres and tags, performs sparse cosine
similarity ranking, provides case-insensitive title search, and generates
evidence-based explanations without fabricating plot or cast details.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class ContentRecommender:
    """
    Content-based recommender using TF-IDF representation of genres and tags.
    Computes pairwise similarity on-demand to avoid large dense N x N matrices.
    """

    def __init__(self, max_features: int = 10000):
        self.max_features = max_features
        self.vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[\w-]+\b",
            stop_words="english",
            max_features=self.max_features,
            sublinear_tf=True
        )
        self.catalog_df: pd.DataFrame = pd.DataFrame()
        self.tfidf_matrix = None
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.genres_map: Dict[int, Set[str]] = {}
        self.tags_map: Dict[int, Set[str]] = {}
        self.is_fitted: bool = False

    def fit(self, catalog_df: pd.DataFrame) -> "ContentRecommender":
        """
        Fits the TF-IDF vectorizer on the movie catalog's content soup.
        Ensures movies with missing text are safely represented without crashing.
        """
        if catalog_df.empty:
            raise ValueError("Cannot fit ContentRecommender on empty catalog.")

        self.catalog_df = catalog_df.reset_index(drop=True)
        
        # Build index lookups
        self.movie_id_to_idx = {
            int(mid): idx for idx, mid in enumerate(self.catalog_df["movieId"])
        }
        self.idx_to_movie_id = {
            idx: int(mid) for idx, mid in enumerate(self.catalog_df["movieId"])
        }

        # Store parsed genres and tags sets for transparent explanations
        for _, row in self.catalog_df.iterrows():
            mid = int(row["movieId"])
            self.genres_map[mid] = set(row.get("genres_list", []))
            tags_str = str(row.get("tags_tokens", ""))
            self.tags_map[mid] = set(tags_str.split()) if tags_str else set()

        # Handle empty or blank text gracefully
        text_corpus = self.catalog_df["content_soup"].fillna("").astype(str).tolist()
        # If corpus is completely empty, provide fallback token
        if all(len(t.strip()) == 0 for t in text_corpus):
            text_corpus = ["movie" for _ in text_corpus]

        self.tfidf_matrix = self.vectorizer.fit_transform(text_corpus)
        self.is_fitted = True
        return self

    def search_movies(self, query: str, limit: int = 25) -> pd.DataFrame:
        """
        Performs case-insensitive, token-aware search for movies by title.
        Matches exact substring first, followed by token overlap.
        """
        if self.catalog_df.empty or not query or not query.strip():
            return pd.DataFrame()

        q = query.strip().lower()
        q_tokens = [tok for tok in re_tokens(q) if len(tok) > 1]

        # Calculate match scores
        results = []
        for _, row in self.catalog_df.iterrows():
            title_lower = str(row["title"]).lower()
            score = 0
            if q == title_lower:
                score = 100
            elif title_lower.startswith(q):
                score = 80
            elif q in title_lower:
                score = 60
            elif q_tokens and all(tok in title_lower for tok in q_tokens):
                score = 40
            elif q_tokens and any(tok in title_lower for tok in q_tokens):
                matching_count = sum(1 for tok in q_tokens if tok in title_lower)
                score = 10 + matching_count * 5

            if score > 0:
                results.append((score, row))

        if not results:
            return pd.DataFrame()

        # Sort by score descending, then by popularity/rating count
        results.sort(key=lambda x: (x[0], x[1].get("rating_count", 0)), reverse=True)
        top_rows = [r[1] for r in results[:limit]]
        return pd.DataFrame(top_rows).reset_index(drop=True)

    def get_movie_details(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Returns metadata dictionary for a specific movieId."""
        if movie_id not in self.movie_id_to_idx:
            return None
        idx = self.movie_id_to_idx[movie_id]
        row = self.catalog_df.iloc[idx]
        return {
            "movieId": int(row["movieId"]),
            "title": str(row["title"]),
            "clean_title": str(row.get("clean_title", row["title"])),
            "release_year": row.get("release_year"),
            "genres": row.get("genres_list", []),
            "genres_display": str(row.get("genres_display", "")),
            "rating_count": int(row.get("rating_count", 0)),
            "mean_rating": float(row.get("mean_rating", 0.0)),
            "weighted_rating": float(row.get("weighted_rating", 0.0)),
            "popularity_score": float(row.get("popularity_score", 0.0)),
            "tags": list(self.tags_map.get(movie_id, set())),
        }

    def get_similar_movies(
        self,
        movie_id: int,
        top_n: int = 10,
        genre_filter: Optional[List[str]] = None,
        year_range: Optional[Tuple[int, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top N movies with highest content cosine similarity.
        
        Requirements:
        - Excludes the query movie from its own recommendations.
        - Avoids dense N x N matrix by computing 1 x N dot product.
        - Applies optional genre and year filters before final ranking.
        - Produces evidence-based explanations (shared genres, matching tags).
        """
        if not self.is_fitted:
            raise RuntimeError("ContentRecommender must be fitted before querying.")

        if movie_id not in self.movie_id_to_idx:
            raise KeyError(f"Movie ID {movie_id} not found in catalog.")

        seed_idx = self.movie_id_to_idx[movie_id]
        seed_vector = self.tfidf_matrix[seed_idx]
        seed_genres = self.genres_map.get(movie_id, set())
        seed_tags = self.tags_map.get(movie_id, set())

        # Efficient 1 x N cosine similarity
        sim_scores = linear_kernel(seed_vector, self.tfidf_matrix).flatten()

        # Build candidates
        candidates = []
        for idx, score in enumerate(sim_scores):
            # Exclude seed movie
            if idx == seed_idx:
                continue

            mid = self.idx_to_movie_id[idx]
            row = self.catalog_df.iloc[idx]

            # Genre filter
            if genre_filter:
                candidate_genres = set(row.get("genres_list", []))
                if not any(g in candidate_genres for g in genre_filter):
                    continue

            # Year filter
            if year_range:
                cand_year = row.get("release_year")
                if cand_year is not None:
                    if cand_year < year_range[0] or cand_year > year_range[1]:
                        continue

            candidates.append((idx, mid, float(score), row))

        # Sort by similarity score descending
        candidates.sort(key=lambda x: x[2], reverse=True)
        top_candidates = candidates[:top_n]

        results = []
        for idx, mid, sim_score, row in top_candidates:
            # Generate explanation from factual evidence
            cand_genres = self.genres_map.get(mid, set())
            cand_tags = self.tags_map.get(mid, set())
            common_genres = sorted(list(seed_genres & cand_genres))
            common_tags = sorted(list(seed_tags & cand_tags))

            reasons = []
            if common_genres:
                reasons.append(f"Shared genres: {', '.join(common_genres)}")
            if common_tags:
                reasons.append(f"Matching user tags: {', '.join(common_tags[:3])}")
            if not reasons:
                reasons.append("Thematic keyword overlap in metadata")

            results.append({
                "movieId": mid,
                "title": str(row["title"]),
                "clean_title": str(row.get("clean_title", row["title"])),
                "release_year": row.get("release_year"),
                "genres_display": str(row.get("genres_display", "")),
                "genres_list": row.get("genres_list", []),
                "content_similarity": round(sim_score, 4),
                "rating_count": int(row.get("rating_count", 0)),
                "mean_rating": float(row.get("mean_rating", 0.0)),
                "weighted_rating": float(row.get("weighted_rating", 0.0)),
                "popularity_score": float(row.get("popularity_score", 0.0)),
                "reasons": reasons,
            })

        return results


def re_tokens(text: str) -> List[str]:
    """Helper to tokenize query text for search."""
    import re
    return re.findall(r"\w+", text.lower())
