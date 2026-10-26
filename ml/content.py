"""
CineMatch Multi-Block Content Engine (Vectorized Sparse Matrix)
Implements:
  1. Multi-block feature representation: Atomic genres, release decade tokens, and atomic tags.
  2. Directional user taste vector: u = Σ (r_i - r_mean) * x_i.
  3. Precomputed top-100 content cosine neighbours for instant /similar retrieval.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from ml.config import settings
from ml.preprocessing import normalize_genres, extract_decade_token


class ContentEngine:
    """
    Multi-block TF-IDF content model.
    Encodes movies into sparse L2-normalized feature vectors and precomputes top-100 neighbours.
    """

    def __init__(
        self,
        genre_weight: float = settings.genre_weight,
        tag_weight: float = settings.tag_weight,
        top_k: int = 100
    ):
        self.genre_weight = genre_weight
        self.tag_weight = tag_weight
        self.top_k = top_k

        self.movie_ids: List[int] = []
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}

        self.tfidf_matrix: Optional[csr_matrix] = None
        self.content_idx: Optional[np.ndarray] = None  # (N_items x top_k)
        self.content_sim: Optional[np.ndarray] = None  # (N_items x top_k)

        self.is_fitted: bool = False

    def fit(self, catalog_df: pd.DataFrame, tags_df: pd.DataFrame) -> "ContentEngine":
        """Fits multi-block TF-IDF and precomputes top-100 content neighbours."""
        clean_catalog = catalog_df.drop_duplicates(subset=["movieId"]).sort_values("movieId").copy()
        self.movie_ids = clean_catalog["movieId"].astype(int).tolist()
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        n_items = len(self.movie_ids)

        # Block 1: Atomic Genres + Decade tokens
        genre_decade_corpus = []
        for _, row in clean_catalog.iterrows():
            genres = normalize_genres(str(row.get("genres", "")))
            year = row.get("year")
            decade = extract_decade_token(int(year) if pd.notna(year) else None)
            tokens = list(genres)
            if decade:
                tokens.append(decade)
            genre_decade_corpus.append(" ".join(tokens) if tokens else "unknown_genre")

        genre_vectorizer = TfidfVectorizer(
            tokenizer=lambda x: x.split(),
            preprocessor=None,
            token_pattern=None,
            binary=True,
            norm="l2"
        )
        X_genre = genre_vectorizer.fit_transform(genre_decade_corpus)

        # Block 2: Atomic Tags
        tag_corpus = [""] * n_items
        if not tags_df.empty:
            tags_clean = tags_df.dropna(subset=["movieId", "tag"]).copy()
            tags_clean["movieId"] = tags_clean["movieId"].astype(int)
            tags_clean["tag_token"] = tags_clean["tag"].astype(str).str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")

            # Filter tags appearing in >= tag_min_movies
            movie_tag_counts = tags_clean.groupby("tag_token")["movieId"].nunique()
            valid_tags = set(movie_tag_counts[movie_tag_counts >= settings.tag_min_movies].index)
            tags_clean = tags_clean[tags_clean["tag_token"].isin(valid_tags)]

            grouped_tags = tags_clean.groupby("movieId")["tag_token"].apply(lambda s: " ".join(s.unique()[:settings.tag_max_per_user_movie])).to_dict()

            for mid, tag_str in grouped_tags.items():
                if mid in self.movie_to_idx:
                    tag_corpus[self.movie_to_idx[mid]] = tag_str

        tag_vectorizer = TfidfVectorizer(
            tokenizer=lambda x: x.split(),
            preprocessor=None,
            token_pattern=None,
            sublinear_tf=True,
            min_df=1,
            norm="l2"
        )
        X_tags = tag_vectorizer.fit_transform(tag_corpus)

        # Horizontal stack with weights
        X_weighted = hstack([X_genre.multiply(self.genre_weight), X_tags.multiply(self.tag_weight)]).tocsr()

        # L2-normalize stacked matrix
        row_norms = np.sqrt(X_weighted.power(2).sum(axis=1))
        row_norms[row_norms == 0] = 1.0
        self.tfidf_matrix = (X_weighted / row_norms).tocsr()

        # Precompute top-100 neighbours
        k_capped = min(self.top_k, n_items - 1)
        self.content_idx = np.full((n_items, k_capped), -1, dtype=np.int32)
        self.content_sim = np.zeros((n_items, k_capped), dtype=np.float32)

        # Chunked dot products
        chunk_size = 500
        for start_idx in range(0, n_items, chunk_size):
            end_idx = min(start_idx + chunk_size, n_items)
            chunk = self.tfidf_matrix[start_idx:end_idx]
            sims = (chunk @ self.tfidf_matrix.T).toarray()  # (chunk, n_items)

            for i in range(end_idx - start_idx):
                item_idx = start_idx + i
                sim_row = sims[i]
                sim_row[item_idx] = 0.0  # Exclude self

                top_k_indices = np.argpartition(-sim_row, k_capped)[:k_capped]
                top_k_sorted = top_k_indices[np.argsort(-sim_row[top_k_indices])]

                self.content_idx[item_idx] = top_k_sorted
                self.content_sim[item_idx] = np.maximum(0.0, sim_row[top_k_sorted])

        self.is_fitted = True
        return self

    def get_similar_movies(self, movie_id: int, top_n: int = 20) -> List[Tuple[int, float]]:
        """Returns top-n similar movies using precomputed table in O(1) time."""
        if not self.is_fitted or movie_id not in self.movie_to_idx:
            return []

        idx = self.movie_to_idx[movie_id]
        neighs = self.content_idx[idx][:top_n]
        sims = self.content_sim[idx][:top_n]

        return [(self.idx_to_movie[n_idx], float(sims[i])) for i, n_idx in enumerate(neighs) if n_idx >= 0 and sims[i] > 0]

    def build_user_taste_vector(self, user_ratings: Dict[int, float]) -> Optional[csr_matrix]:
        """
        Builds directional user taste vector:
          u = Σ (r_i - user_mean) * x_i
        Items rated below mean push the vector away from those features.
        """
        if not self.is_fitted or not user_ratings:
            return None

        valid_items = {mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx}
        if not valid_items:
            return None

        u_mean = float(np.mean(list(valid_items.values())))
        dim = self.tfidf_matrix.shape[1]
        u_vector = np.zeros((1, dim), dtype=np.float32)

        for mid, rating in valid_items.items():
            idx = self.movie_to_idx[mid]
            weight = rating - u_mean
            if abs(weight) < 1e-4:
                weight = 0.1  # Slight positive pull if exactly at mean
            item_row = self.tfidf_matrix[idx].toarray()
            u_vector += weight * item_row

        norm = np.linalg.norm(u_vector)
        if norm > 0:
            u_vector = u_vector / norm
            return csr_matrix(u_vector)
        return None

    def predict_for_user_ratings(
        self,
        user_ratings: Dict[int, float],
        candidate_movie_ids: Optional[List[int]] = None
    ) -> Dict[int, float]:
        """Scores candidate items by cosine similarity to directional user taste vector."""
        u_vec = self.build_user_taste_vector(user_ratings)
        if u_vec is None:
            return {}

        if candidate_movie_ids is None:
            cands = [m for m in self.movie_ids if m not in user_ratings]
        else:
            cands = [m for m in candidate_movie_ids if m in self.movie_to_idx and m not in user_ratings]

        if not cands:
            return {}

        cand_indices = np.array([self.movie_to_idx[m] for m in cands], dtype=np.int32)
        X_cands = self.tfidf_matrix[cand_indices]  # (|C|, V)

        # Dot product with normalized user vector
        scores = (X_cands @ u_vec.T).toarray().ravel()
        scores_clamped = np.clip(scores, 0.0, 1.0)

        return {mid: float(scores_clamped[i]) for i, mid in enumerate(cands)}
