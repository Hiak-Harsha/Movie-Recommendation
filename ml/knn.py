"""
CineMatch Item-kNN Engine (Vectorized NumPy / SciPy)
Implements Item-Item Collaborative Filtering with mean centering, significance shrinkage,
and precomputes top-100 neighbours for instant O(1) retrieval at serving time.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

from ml.config import settings


class ItemKNN:
    """
    Item-based Collaborative Filtering with mean centering and shrinkage:
      s_shrunk(i, j) = s(i, j) * n_ij / (n_ij + λ)
    Precomputes top-100 neighbours per item as compact NumPy arrays.
    """

    def __init__(
        self,
        k: int = settings.knn_k,
        min_co_ratings: int = settings.knn_min_co_ratings,
        shrinkage_lambda: float = settings.knn_shrinkage_lambda
    ):
        self.k = k
        self.min_co_ratings = min_co_ratings
        self.shrinkage_lambda = shrinkage_lambda

        self.global_mean: float = 3.5
        self.movie_ids: List[int] = []
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}
        self.user_to_idx: Dict[int, int] = {}

        self.movie_biases: Dict[int, float] = {}
        self.user_means: Dict[int, float] = {}

        # Top-100 precomputed arrays (N_items x k)
        self.knn_idx: Optional[np.ndarray] = None  # int32
        self.knn_sim: Optional[np.ndarray] = None  # float32
        self.knn_co: Optional[np.ndarray] = None   # int32

        self.is_fitted: bool = False

    def fit(self, ratings_train: pd.DataFrame, all_movie_ids: Optional[List[int]] = None) -> "ItemKNN":
        """Fits Item-kNN and precomputes top-k neighbours."""
        if ratings_train.empty:
            raise ValueError("Training ratings cannot be empty.")

        self.global_mean = float(ratings_train["rating"].mean())
        user_ids = sorted(ratings_train["userId"].unique().tolist())
        if all_movie_ids is not None:
            self.movie_ids = sorted(list(set(all_movie_ids)))
        else:
            self.movie_ids = sorted(ratings_train["movieId"].unique().tolist())

        self.user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        n_users = len(user_ids)
        n_items = len(self.movie_ids)

        # Compute user means and centered ratings
        user_mean_series = ratings_train.groupby("userId")["rating"].mean()
        self.user_means = dict(user_mean_series)
        
        # Movie biases
        movie_mean_series = ratings_train.groupby("movieId")["rating"].mean()
        for mid, m_mean in movie_mean_series.items():
            self.movie_biases[int(mid)] = float(m_mean - self.global_mean)

        u_means_mapped = ratings_train["userId"].map(user_mean_series).values
        centered_ratings = (ratings_train["rating"].values - u_means_mapped).astype(np.float32)

        u_idx = np.array([self.user_to_idx[u] for u in ratings_train["userId"]], dtype=np.int32)
        m_idx = np.array([self.movie_to_idx[m] for m in ratings_train["movieId"]], dtype=np.int32)

        # Build centered Item-User sparse matrix (N_items x N_users)
        R_item_user = csr_matrix((centered_ratings, (m_idx, u_idx)), shape=(n_items, n_users), dtype=np.float32)

        # Binary indicator matrix for co-rating counts
        ones = np.ones(len(r_vals := ratings_train["rating"]), dtype=np.float32)
        B_item_user = csr_matrix((ones, (m_idx, u_idx)), shape=(n_items, n_users), dtype=np.float32)

        # Precompute top-k neighbours
        k_capped = min(self.k, n_items - 1)
        self.knn_idx = np.full((n_items, k_capped), -1, dtype=np.int32)
        self.knn_sim = np.zeros((n_items, k_capped), dtype=np.float32)
        self.knn_co = np.zeros((n_items, k_capped), dtype=np.int32)

        # Compute cosine similarities in chunks to conserve memory
        chunk_size = 500
        for start_idx in range(0, n_items, chunk_size):
            end_idx = min(start_idx + chunk_size, n_items)
            chunk_R = R_item_user[start_idx:end_idx]
            chunk_B = B_item_user[start_idx:end_idx]

            # Cosine similarity on centered ratings
            sims = cosine_similarity(chunk_R, R_item_user, dense_output=True)  # (chunk, n_items)
            
            # Co-raters: B_chunk @ B.T
            co_matrix = (chunk_B @ B_item_user.T).toarray()  # (chunk, n_items)

            for i in range(end_idx - start_idx):
                item_idx = start_idx + i
                sim_row = sims[i]
                co_row = co_matrix[i]

                # Zero self similarity
                sim_row[item_idx] = 0.0

                # Filter min co-ratings
                valid_mask = co_row >= self.min_co_ratings
                shrunk_sim = np.zeros_like(sim_row)
                if np.any(valid_mask):
                    n_co = co_row[valid_mask]
                    shrinkage = n_co / (n_co + self.shrinkage_lambda)
                    shrunk_sim[valid_mask] = np.maximum(0.0, sim_row[valid_mask] * shrinkage)

                # Top-k selection
                if np.any(shrunk_sim > 0):
                    top_k_indices = np.argpartition(-shrunk_sim, k_capped)[:k_capped]
                    top_k_sorted = top_k_indices[np.argsort(-shrunk_sim[top_k_indices])]
                    
                    self.knn_idx[item_idx] = top_k_sorted
                    self.knn_sim[item_idx] = shrunk_sim[top_k_sorted]
                    self.knn_co[item_idx] = co_row[top_k_sorted]

        self.is_fitted = True
        return self

    def predict_for_user_ratings(
        self,
        user_ratings: Dict[int, float],
        candidate_movie_ids: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Fast kNN prediction using precomputed neighbour tables.
        Returns predicted ratings and top neighbor evidence.
        """
        if not self.is_fitted or not user_ratings:
            return {}

        u_mean = float(np.mean(list(user_ratings.values())))
        rated_idx_set = {self.movie_to_idx[mid]: r for mid, r in user_ratings.items() if mid in self.movie_to_idx}
        if not rated_idx_set:
            return {}

        if candidate_movie_ids is None:
            cands = [m for m in self.movie_ids if m not in user_ratings]
        else:
            cands = [m for m in candidate_movie_ids if m in self.movie_to_idx and m not in user_ratings]

        results = {}
        for mid in cands:
            j_idx = self.movie_to_idx[mid]
            neigh_indices = self.knn_idx[j_idx]
            neigh_sims = self.knn_sim[j_idx]
            neigh_cos = self.knn_co[j_idx]

            # Find intersection with user's rated items
            matched_indices = []
            matched_sims = []
            matched_diffs = []
            top_evidence = None

            for pos in range(len(neigh_indices)):
                n_idx = neigh_indices[pos]
                if n_idx in rated_idx_set:
                    sim = neigh_sims[pos]
                    if sim > 0:
                        matched_indices.append(n_idx)
                        matched_sims.append(sim)
                        matched_diffs.append(rated_idx_set[n_idx] - u_mean)
                        if top_evidence is None:
                            top_evidence = {
                                "movieId": self.idx_to_movie[n_idx],
                                "sim": round(float(sim), 3),
                                "coRaters": int(neigh_cos[pos])
                            }

            b_j = self.movie_biases.get(mid, 0.0)
            if matched_sims:
                weighted_dev = np.dot(matched_sims, matched_diffs) / np.sum(matched_sims)
                pred_r = float(np.clip(u_mean + b_j + weighted_dev, 0.5, 5.0))
            else:
                pred_r = float(np.clip(u_mean + b_j, 0.5, 5.0))

            knn_score = float((pred_r - 0.5) / 4.5)
            results[mid] = {
                "predicted_rating": round(pred_r, 2),
                "knn_score": round(knn_score, 4),
                "neighbor_evidence": top_evidence
            }

        return results
