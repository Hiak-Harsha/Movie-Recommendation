"""
CineMatch Collaborative Filtering Engine (Pure NumPy / SciPy)
Implements:
  1. Item-kNN with mean centering, significance shrinkage, and co-rating filtering.
  2. Biased Matrix Factorization (mu + b_u + b_i + p_u @ q_i) with closed-form fold-in for new visitors.
Strictly operates on observed ratings. Unobserved ratings are never treated as zeros.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

import config


class ItemKNNRecommender:
    """
    Item-based Collaborative Filtering with mean centering and significance shrinkage.
    Computes pairwise similarities strictly from observed co-ratings.
    """

    def __init__(
        self,
        min_co_ratings: int = config.CF_MIN_CO_RATINGS,
        shrinkage_lambda: float = config.CF_SHRINKAGE_LAMBDA,
        k_neighbors: int = 40
    ):
        self.min_co_ratings = min_co_ratings
        self.shrinkage_lambda = shrinkage_lambda
        self.k_neighbors = k_neighbors

        self.global_mean: float = 3.5
        self.user_ids: List[int] = []
        self.movie_ids: List[int] = []
        self.user_to_idx: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}

        self.user_means: Dict[int, float] = {}
        self.movie_means: Dict[int, float] = {}
        self.movie_counts: Dict[int, int] = {}

        self.R_item_user: Optional[csr_matrix] = None
        self.user_history: Dict[int, Dict[int, float]] = {}
        # Top-k item neighbors: {movie_idx: [(neighbor_idx, shrunk_sim, co_count)]}
        self.item_neighbors: Dict[int, List[Tuple[int, float, int]]] = {}
        self.is_fitted: bool = False

    def fit(self, ratings_train: pd.DataFrame) -> "ItemKNNRecommender":
        """Fits Item-kNN model on training ratings only."""
        if ratings_train.empty:
            raise ValueError("Training ratings cannot be empty.")

        self.global_mean = float(ratings_train["rating"].mean())
        self.user_ids = sorted(ratings_train["userId"].unique().tolist())
        self.movie_ids = sorted(ratings_train["movieId"].unique().tolist())

        self.user_to_idx = {uid: i for i, uid in enumerate(self.user_ids)}
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        # User means and history
        for uid, group in ratings_train.groupby("userId"):
            uid_int = int(uid)
            self.user_means[uid_int] = float(group["rating"].mean())
            self.user_history[uid_int] = dict(zip(group["movieId"].astype(int), group["rating"].astype(float)))

        for mid, group in ratings_train.groupby("movieId"):
            mid_int = int(mid)
            self.movie_means[mid_int] = float(group["rating"].mean())
            self.movie_counts[mid_int] = int(len(group))

        # Vectorized construction of mean-centered rating matrix
        u_arr = ratings_train["userId"].map(self.user_to_idx).values.astype(np.int32)
        m_arr = ratings_train["movieId"].map(self.movie_to_idx).values.astype(np.int32)
        u_means_arr = ratings_train["userId"].map(self.user_means).values.astype(np.float32)
        centered_vals = ratings_train["rating"].values.astype(np.float32) - u_means_arr

        R_user_item = csr_matrix(
            (centered_vals, (u_arr, m_arr)),
            shape=(len(self.user_ids), len(self.movie_ids)),
            dtype=np.float32
        )
        self.R_item_user = R_user_item.T.tocsr()
        self.is_fitted = True
        return self

    def predict_rating_for_item(
        self,
        user_ratings: Dict[int, float],
        target_movie_id: int
    ) -> Optional[Tuple[float, Optional[Dict[str, Any]]]]:
        """
        Predicts rating for a specific target movie using visitor ratings.
        Returns (predicted_rating, top_neighbor_info) or (None, None).
        """
        if not self.is_fitted or target_movie_id not in self.movie_to_idx:
            return None

        valid_ratings = {
            mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx
        }
        if len(valid_ratings) < config.MIN_RECOGNIZED_ITEMS_FOR_CF:
            return None

        if target_movie_id in valid_ratings:
            return valid_ratings[target_movie_id], None

        user_mean = float(np.mean(list(valid_ratings.values())))
        target_idx = self.movie_to_idx[target_movie_id]
        target_vec = self.R_item_user[target_idx]

        rated_mids = list(valid_ratings.keys())
        rated_indices = [self.movie_to_idx[mid] for mid in rated_mids]
        rated_submatrix = self.R_item_user[rated_indices]

        # Vectorized cosine similarity and co-raters count
        sims = cosine_similarity(target_vec, rated_submatrix).flatten()
        target_bin = (target_vec != 0).astype(np.float32)
        rated_bin = (rated_submatrix != 0).astype(np.float32)
        co_counts = (target_bin * rated_bin.T).toarray().flatten()

        valid_mask = (co_counts >= self.min_co_ratings) & (sims > 0.0)
        if not np.any(valid_mask):
            return None

        # Shrinkage
        shrunk_sims = sims[valid_mask] * (co_counts[valid_mask] / (co_counts[valid_mask] + self.shrinkage_lambda))
        weight_sum = np.sum(shrunk_sims)
        if weight_sum < 1e-6:
            return None

        user_devs = np.array([valid_ratings[mid] - user_mean for mid in rated_mids])[valid_mask]
        predicted = user_mean + np.sum(shrunk_sims * user_devs) / weight_sum
        clamped = float(np.clip(predicted, 0.5, 5.0))

        # Best contributing neighbor
        best_idx_pos = int(np.argmax(shrunk_sims))
        best_mid = np.array(rated_mids)[valid_mask][best_idx_pos]
        best_sim = float(sims[valid_mask][best_idx_pos])
        best_co = int(co_counts[valid_mask][best_idx_pos])

        neighbor_info = {
            "neighbor_movieId": int(best_mid),
            "similarity": round(best_sim, 3),
            "co_raters": best_co
        }
        return clamped, neighbor_info


class BiasedMFRecommender:
    """
    Biased Matrix Factorization (pure NumPy / SciPy):
        r̂ = μ + b_u + b_i + p_u @ q_i
    Trained strictly on observed ratings with L2 regularization.
    Supports closed-form fold-in for new visitors:
        p_new = (Q_I^T Q_I + λ I)^(-1) Q_I^T (r_new - μ - b_i)
    """

    def __init__(
        self,
        factors: int = config.MF_FACTORS,
        reg: float = config.MF_REGULARIZATION,
        lr: float = 0.015,
        iterations: int = config.MF_ITERATIONS,
        random_seed: int = config.RANDOM_SEED
    ):
        self.factors = factors
        self.reg = reg
        self.lr = lr
        self.iterations = iterations
        self.random_seed = random_seed

        self.mu: float = 3.5
        self.user_ids: List[int] = []
        self.movie_ids: List[int] = []
        self.user_to_idx: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}

        self.bu: Optional[np.ndarray] = None
        self.bi: Optional[np.ndarray] = None
        self.P: Optional[np.ndarray] = None
        self.Q: Optional[np.ndarray] = None
        self.is_fitted: bool = False

    def fit(self, ratings_train: pd.DataFrame) -> "BiasedMFRecommender":
        """Fits Biased Matrix Factorization using stochastic gradient descent on observed ratings."""
        if ratings_train.empty:
            raise ValueError("Training ratings cannot be empty.")

        self.mu = float(ratings_train["rating"].mean())
        self.user_ids = sorted(ratings_train["userId"].unique().tolist())
        self.movie_ids = sorted(ratings_train["movieId"].unique().tolist())

        self.user_to_idx = {uid: i for i, uid in enumerate(self.user_ids)}
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        n_users = len(self.user_ids)
        n_items = len(self.movie_ids)

        rng = np.random.RandomState(self.random_seed)
        self.P = rng.normal(0, 0.08, (n_users, self.factors)).astype(np.float32)
        self.Q = rng.normal(0, 0.08, (n_items, self.factors)).astype(np.float32)
        self.bu = np.zeros(n_users, dtype=np.float32)
        self.bi = np.zeros(n_items, dtype=np.float32)

        u_indices = np.array([self.user_to_idx[u] for u in ratings_train["userId"]], dtype=np.int32)
        i_indices = np.array([self.movie_to_idx[m] for m in ratings_train["movieId"]], dtype=np.int32)
        r_vals = ratings_train["rating"].values.astype(np.float32)

        # SGD training loop
        n_samples = len(r_vals)
        indices = np.arange(n_samples)

        for _ in range(self.iterations):
            rng.shuffle(indices)
            for idx in indices:
                u = u_indices[idx]
                i = i_indices[idx]
                r = r_vals[idx]

                pred = self.mu + self.bu[u] + self.bi[i] + float(np.dot(self.P[u], self.Q[i]))
                err = r - pred

                self.bu[u] += self.lr * (err - self.reg * self.bu[u])
                self.bi[i] += self.lr * (err - self.reg * self.bi[i])

                p_curr = self.P[u].copy()
                self.P[u] += self.lr * (err * self.Q[i] - self.reg * self.P[u])
                self.Q[i] += self.lr * (err * p_curr - self.reg * self.Q[i])

        self.is_fitted = True
        return self

    def fold_in_user(
        self,
        user_ratings: Dict[int, float]
    ) -> Optional[Tuple[float, np.ndarray]]:
        """
        Solves closed-form ridge regression for a new visitor's latent vector
        against frozen item factors and biases:
            p_new = (Q_I^T Q_I + λ I)^(-1) Q_I^T (r - μ - b_i)
        """
        if not self.is_fitted or not user_ratings:
            return None

        valid_ratings = {
            mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx
        }
        if len(valid_ratings) < config.MIN_RECOGNIZED_ITEMS_FOR_CF:
            return None

        rated_indices = [self.movie_to_idx[mid] for mid in valid_ratings.keys()]
        r_actual = np.array(list(valid_ratings.values()), dtype=np.float32)

        Q_I = self.Q[rated_indices]
        b_I = self.bi[rated_indices]

        # Estimate user bias with shrinkage
        residuals = r_actual - self.mu - b_I
        b_new = float(np.sum(residuals) / (len(valid_ratings) + self.reg))

        # Solve ridge regression: (Q_I^T Q_I + λ I) p_new = Q_I^T (residuals - b_new)
        A = np.dot(Q_I.T, Q_I) + self.reg * np.eye(self.factors, dtype=np.float32)
        y = np.dot(Q_I.T, residuals - b_new)
        p_new = np.linalg.solve(A, y)

        return b_new, p_new

    def predict_for_user_ratings(
        self,
        user_ratings: Dict[int, float],
        candidate_movie_ids: Optional[List[int]] = None
    ) -> Dict[int, float]:
        """
        Predicts ratings for all candidate movies for an arbitrary user profile
        using fold-in ridge regression.
        """
        fold_res = self.fold_in_user(user_ratings)
        if fold_res is None:
            return {}

        b_new, p_new = fold_res
        rated_set = set(user_ratings.keys())

        if candidate_movie_ids is not None:
            cands = [mid for mid in candidate_movie_ids if mid in self.movie_to_idx and mid not in rated_set]
        else:
            cands = [mid for mid in self.movie_ids if mid not in rated_set]

        if not cands:
            return {}

        cand_indices = [self.movie_to_idx[mid] for mid in cands]
        Q_cands = self.Q[cand_indices]
        b_cands = self.bi[cand_indices]

        scores = self.mu + b_new + b_cands + np.dot(Q_cands, p_new)
        scores_clamped = np.clip(scores, 0.5, 5.0)

        return {mid: float(scores_clamped[idx]) for idx, mid in enumerate(cands)}


class CollaborativeEngine:
    """
    Unified Collaborative Filtering Engine managing Item-kNN and Biased MF.
    Provides fast fold-in predictions, honest cold-start handling, and neighbor explanations.
    """

    def __init__(
        self,
        primary_algorithm: str = "item_knn"
    ):
        self.primary_algorithm = primary_algorithm
        self.item_knn = ItemKNNRecommender()
        self.biased_mf = BiasedMFRecommender()
        self.is_fitted: bool = False

    def fit(self, ratings_train: pd.DataFrame) -> "CollaborativeEngine":
        """Fits both Item-kNN and Biased MF on training ratings."""
        self.item_knn.fit(ratings_train)
        self.biased_mf.fit(ratings_train)
        self.is_fitted = True
        return self

    def predict_user_preferences(
        self,
        user_ratings: Dict[int, float],
        candidate_movie_ids: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Generates collaborative filtering predictions and normalized scores.
        Enforces minimum rating history rule (>= MIN_USER_RATINGS_FOR_CF).
        """
        if not self.is_fitted:
            raise RuntimeError("CollaborativeEngine must be fitted before predicting.")

        if len(user_ratings) < config.MIN_USER_RATINGS_FOR_CF:
            return {}

        # 1. Primary scoring using Biased MF fold-in
        mf_preds = self.biased_mf.predict_for_user_ratings(user_ratings, candidate_movie_ids)
        if not mf_preds:
            return {}

        results: Dict[int, Dict[str, Any]] = {}
        for mid, pred_r in mf_preds.items():
            # Normalized score in [0.0, 1.0] via (rating - 0.5) / 4.5
            collab_score = float((pred_r - 0.5) / 4.5)
            results[mid] = {
                "predicted_rating": round(pred_r, 2),
                "collab_score": round(collab_score, 4),
                "neighbor_info": None
            }

        # 2. Add Item-kNN neighbor explanation for top ranked items
        top_mids = sorted(results.keys(), key=lambda m: results[m]["predicted_rating"], reverse=True)[:10]
        for mid in top_mids:
            knn_res = self.item_knn.predict_rating_for_item(user_ratings, mid)
            if knn_res is not None:
                _, neighbor_info = knn_res
                results[mid]["neighbor_info"] = neighbor_info

        return results

    def get_existing_user_ratings(self, user_id: int) -> Dict[int, float]:
        """Returns historical training ratings for a dataset user."""
        return dict(self.item_knn.user_history.get(user_id, {}))
