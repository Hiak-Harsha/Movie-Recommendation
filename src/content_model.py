"""
CineMatch Content-Based Recommendation Engine
Builds multi-block feature matrices (atomic genres + decade block + atomic tag block),
performs sparse cosine similarity ranking, calculates user taste vectors with
mean-centered rating weights, provides article-agnostic title search, and generates
evidence-based explanations.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from src.preprocessing import build_search_key


class ContentRecommender:
    """
    Content-based recommender using multi-block TF-IDF representation.
    Blocks:
      1. Genre & Decade block (atomic genre tokens + decade token)
      2. Tag block (atomic user tags with sublinear TF)
    Rows are L2-normalized. Pairwise similarities computed via sparse matrix-vector dot products.
    """

    def __init__(
        self,
        genre_weight: float = 1.0,
        tag_weight: float = 0.8,
        min_tag_df: int = 1
    ):
        self.genre_weight = genre_weight
        self.tag_weight = tag_weight
        self.min_tag_df = min_tag_df

        self.genre_vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[\w_]+\b",
            binary=True,
            norm=None
        )
        self.tag_vectorizer = TfidfVectorizer(
            token_pattern=r"(?u)\b[\w_]+\b",
            sublinear_tf=True,
            min_df=self.min_tag_df,
            max_df=0.85,
            norm=None
        )

        self.catalog_df: pd.DataFrame = pd.DataFrame()
        self.feature_matrix: Optional[csr_matrix] = None
        self.movie_id_to_idx: Dict[int, int] = {}
        self.idx_to_movie_id: Dict[int, int] = {}
        self.genres_map: Dict[int, Set[str]] = {}
        self.tags_map: Dict[int, Set[str]] = {}
        self.search_index: Dict[str, List[int]] = {}
        self.is_fitted: bool = False

    def fit(self, catalog_df: pd.DataFrame) -> "ContentRecommender":
        """
        Fits multi-block TF-IDF representations on the movie catalog.
        Combines weighted genre/decade block with tag block and L2-normalizes rows.
        """
        if catalog_df.empty:
            raise ValueError("Cannot fit ContentRecommender on empty catalog.")

        self.catalog_df = catalog_df.reset_index(drop=True)
        n_movies = len(self.catalog_df)

        self.movie_id_to_idx = {
            int(mid): idx for idx, mid in enumerate(self.catalog_df["movieId"])
        }
        self.idx_to_movie_id = {
            idx: int(mid) for idx, mid in enumerate(self.catalog_df["movieId"])
        }

        # Build genre and tag lookups for explanations
        for _, row in self.catalog_df.iterrows():
            mid = int(row["movieId"])
            self.genres_map[mid] = set(row.get("genres_list", []))
            tags_str = str(row.get("tags_tokens", ""))
            self.tags_map[mid] = set(tags_str.split()) if tags_str else set()

        # 1. Genre & Decade Block
        genre_decade_corpus = [
            f"{row.get('genre_tokens', '')} {row.get('decade_token', '')}".strip()
            for _, row in self.catalog_df.iterrows()
        ]
        # Fallback if empty
        if all(len(t) == 0 for t in genre_decade_corpus):
            genre_decade_corpus = ["unknown" for _ in range(n_movies)]
        
        X_genre = self.genre_vectorizer.fit_transform(genre_decade_corpus)
        X_genre = X_genre.astype(np.float32).multiply(self.genre_weight)

        # 2. Tag Block
        tag_corpus = [
            str(row.get("tags_tokens", "")).strip()
            for _, row in self.catalog_df.iterrows()
        ]
        has_tags = any(len(t) > 0 for t in tag_corpus)
        if has_tags:
            X_tag = self.tag_vectorizer.fit_transform(tag_corpus)
            X_tag = X_tag.astype(np.float32).multiply(self.tag_weight)
            X_combined = hstack([X_genre, X_tag]).tocsr()
        else:
            X_combined = X_genre.tocsr()

        # L2-normalize rows of sparse matrix
        self.feature_matrix = normalize(X_combined, norm="l2", axis=1)

        # Build search index
        self.search_index = {}
        for idx, row in self.catalog_df.iterrows():
            s_key = str(row.get("search_key", ""))
            if s_key not in self.search_index:
                self.search_index[s_key] = []
            self.search_index[s_key].append(idx)

        self.is_fitted = True
        return self

    def search_movies(self, query: str, limit: int = 25) -> pd.DataFrame:
        """
        Performs article-agnostic, accent-stripped, case-insensitive title search.
        Matches exact search keys, prefix matches, and token intersections.
        """
        if self.catalog_df.empty or not query or not query.strip():
            return pd.DataFrame()

        q_key = build_search_key(query)
        q_tokens = set(q_key.split())

        scored_results = []
        for idx, row in self.catalog_df.iterrows():
            s_key = row["search_key"]
            s_tokens = set(s_key.split())
            score = 0

            if q_key == s_key:
                score = 100
            elif s_key.startswith(q_key) and len(q_key) > 2:
                score = 80
            elif q_key in s_key:
                score = 65
            elif q_tokens and q_tokens.issubset(s_tokens):
                score = 50
            elif q_tokens and any(t in s_tokens for t in q_tokens):
                overlap = len(q_tokens & s_tokens)
                score = 20 + overlap * 5

            if score > 0:
                scored_results.append((score, int(row.get("rating_count", 0)), row))

        if not scored_results:
            return pd.DataFrame()

        # Sort by relevance score, then rating count
        scored_results.sort(key=lambda x: (x[0], x[1]), reverse=True)
        top_rows = [r[2] for r in scored_results[:limit]]
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
            "display_title": str(row.get("display_title", row["title"])),
            "release_year": row.get("release_year"),
            "genres": row.get("genres_list", []),
            "genres_display": str(row.get("genres_display", "")),
            "imdbId": row.get("imdbId"),
            "tmdbId": row.get("tmdbId"),
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
        Retrieves top N similar movies using sparse cosine similarity.
        
        Requirements:
        - Excludes seed movie.
        - Identifies all-zero feature vectors with content_score = None and note.
        - Applies genre and year filters before final ranking.
        - Factual explanations: shared genres, shared atomic tags.
        """
        if not self.is_fitted:
            raise RuntimeError("ContentRecommender must be fitted before querying.")

        if movie_id not in self.movie_id_to_idx:
            raise KeyError(f"Movie ID {movie_id} not found in catalog.")

        seed_idx = self.movie_id_to_idx[movie_id]
        seed_vec = self.feature_matrix[seed_idx]
        seed_norm = seed_vec.nnz

        seed_genres = self.genres_map.get(movie_id, set())
        seed_tags = self.tags_map.get(movie_id, set())

        # If seed movie has no features
        if seed_norm == 0:
            return []

        # Sparse dot product: (1 x D) @ (D x N) -> 1 x N
        sim_scores = (self.feature_matrix * seed_vec.T).toarray().flatten()

        candidates = []
        for idx, score in enumerate(sim_scores):
            if idx == seed_idx:
                continue

            row = self.catalog_df.iloc[idx]
            mid = self.idx_to_movie_id[idx]

            # Genre filter (OR semantics by default)
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

            cand_vec = self.feature_matrix[idx]
            if cand_vec.nnz == 0:
                final_score = None
            else:
                final_score = float(np.clip(score, 0.0, 1.0))

            candidates.append((idx, mid, final_score, row))

        # Sort by similarity score descending (None values at the end)
        candidates.sort(key=lambda x: (x[2] is not None, x[2] if x[2] is not None else -1), reverse=True)
        top_candidates = candidates[:top_n]

        results = []
        for idx, mid, sim_score, row in top_candidates:
            cand_genres = self.genres_map.get(mid, set())
            cand_tags = self.tags_map.get(mid, set())
            common_genres = sorted(list(seed_genres & cand_genres))
            common_tags = sorted(list(seed_tags & cand_tags))

            reasons = []
            if sim_score is None:
                reasons.append("Insufficient metadata to compute similarity.")
            else:
                if common_genres:
                    reasons.append(f"Shared genres: {', '.join(common_genres)}")
                if common_tags:
                    display_tags = [t.replace('_', ' ') for t in common_tags[:3]]
                    reasons.append(f"Shared tags: {', '.join(display_tags)}")
                if not reasons:
                    reasons.append("Stylistic overlap in decade and genre classification.")

            results.append({
                "movieId": mid,
                "title": str(row["title"]),
                "display_title": str(row.get("display_title", row["title"])),
                "release_year": row.get("release_year"),
                "genres_display": str(row.get("genres_display", "")),
                "genres_list": row.get("genres_list", []),
                "imdbId": row.get("imdbId"),
                "content_similarity": round(sim_score, 4) if sim_score is not None else None,
                "rating_count": int(row.get("rating_count", 0)),
                "mean_rating": float(row.get("mean_rating", 0.0)),
                "weighted_rating": float(row.get("weighted_rating", 0.0)),
                "popularity_score": float(row.get("popularity_score", 0.0)),
                "reasons": reasons,
            })

        return results

    def build_user_taste_vector(
        self,
        user_ratings: Dict[int, float],
        global_mean: float = 3.5
    ) -> Optional[np.ndarray]:
        """
        Constructs a user taste vector from ratings:
            u = Σ w_i * x_i   where   w_i = r_i - user_mean
        (Falls back to r_i - global_mean if user has only 1 rating).
        Normalizes u with L2 norm. Items rated below user mean push vector away.
        """
        if not user_ratings or not self.is_fitted:
            return None

        valid_ratings = {
            mid: r for mid, r in user_ratings.items() if mid in self.movie_id_to_idx
        }
        if not valid_ratings:
            return None

        if len(valid_ratings) > 1:
            u_mean = float(np.mean(list(valid_ratings.values())))
        else:
            u_mean = float(global_mean)

        taste_vec = np.zeros((1, self.feature_matrix.shape[1]), dtype=np.float32)
        total_weight = 0.0

        for mid, rating in valid_ratings.items():
            idx = self.movie_id_to_idx[mid]
            vec = self.feature_matrix[idx].toarray()
            w = rating - u_mean
            taste_vec += w * vec
            total_weight += abs(w)

        norm = np.linalg.norm(taste_vec)
        if norm < 1e-6:
            # If all ratings were exactly the mean
            # Uniform positive sum of vectors
            for mid in valid_ratings.keys():
                idx = self.movie_id_to_idx[mid]
                taste_vec += self.feature_matrix[idx].toarray()
            norm = np.linalg.norm(taste_vec)
            if norm < 1e-6:
                return None

        return taste_vec / norm

    def score_candidates_for_user(
        self,
        user_taste_vector: np.ndarray,
        candidate_indices: Optional[List[int]] = None
    ) -> np.ndarray:
        """
        Scores candidate movies by cosine similarity against user taste vector.
        Returns 1D array of scores in [0.0, 1.0].
        """
        if user_taste_vector is None:
            return np.zeros(len(self.catalog_df), dtype=np.float32)

        # Vectorized sparse dot product
        # user_taste_vector is (1 x D), feature_matrix is (N x D)
        scores = (self.feature_matrix * user_taste_vector.T).flatten()
        # Clip negative similarities to 0.0
        return np.clip(scores, 0.0, 1.0)
