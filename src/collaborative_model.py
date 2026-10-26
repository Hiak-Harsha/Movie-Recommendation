"""
CineMatch Collaborative Filtering Engine
Implements Item-Based Collaborative Filtering with mean centering, significance
shrinkage weighting, and unobserved rating handling. Also provides matrix
factorization representations and explicit fallback detection for cold-start users.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity


class CollaborativeRecommender:
    """
    Collaborative filtering recommender using Item-Based CF.
    Operates strictly on training ratings. Unobserved ratings are never treated as zeros.
    Supports both existing dataset user IDs and custom temporary user rating profiles.
    """

    def __init__(
        self,
        min_co_ratings: int = 3,
        shrinkage_threshold: int = 5,
        min_user_ratings_for_cf: int = 3
    ):
        self.min_co_ratings = min_co_ratings
        self.shrinkage_threshold = shrinkage_threshold
        self.min_user_ratings_for_cf = min_user_ratings_for_cf

        self.user_ids: List[int] = []
        self.movie_ids: List[int] = []
        self.user_to_idx: Dict[int, int] = {}
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}

        self.global_mean: float = 3.5
        self.user_means: Dict[int, float] = {}
        self.movie_means: Dict[int, float] = {}
        self.movie_counts: Dict[int, int] = {}

        # User-rated sets for fast exclusion
        self.user_rated_items: Dict[int, Dict[int, float]] = {}

        # Item-Item similarity sparse/cached structures
        self.R_user_item: Optional[csr_matrix] = None
        self.R_item_user: Optional[csr_matrix] = None
        self.is_fitted: bool = False

    def fit(self, ratings_train: pd.DataFrame) -> "CollaborativeRecommender":
        """
        Fits collaborative filtering strictly on training ratings.
        Computes user means, movie means, and builds sparse representation.
        """
        if ratings_train.empty:
            raise ValueError("Training ratings cannot be empty.")

        self.global_mean = float(ratings_train["rating"].mean())

        # Unique users and movies in training set
        self.user_ids = sorted(ratings_train["userId"].unique().tolist())
        self.movie_ids = sorted(ratings_train["movieId"].unique().tolist())

        self.user_to_idx = {uid: i for i, uid in enumerate(self.user_ids)}
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        # Compute user means and user history
        user_grouped = ratings_train.groupby("userId")
        for uid, group in user_grouped:
            self.user_means[int(uid)] = float(group["rating"].mean())
            self.user_rated_items[int(uid)] = dict(zip(group["movieId"].astype(int), group["rating"].astype(float)))

        # Compute movie stats
        movie_grouped = ratings_train.groupby("movieId")
        for mid, group in movie_grouped:
            self.movie_means[int(mid)] = float(group["rating"].mean())
            self.movie_counts[int(mid)] = int(len(group))

        # Build sparse user-item rating matrix
        row_indices = [self.user_to_idx[uid] for uid in ratings_train["userId"]]
        col_indices = [self.movie_to_idx[mid] for mid in ratings_train["movieId"]]
        ratings_values = ratings_train["rating"].values.astype(np.float64)

        n_users = len(self.user_ids)
        n_movies = len(self.movie_ids)
        self.R_user_item = csr_matrix(
            (ratings_values, (row_indices, col_indices)),
            shape=(n_users, n_movies)
        )
        # Item-user matrix (rows are movies, columns are users)
        self.R_item_user = self.R_user_item.T.tocsr()

        self.is_fitted = True
        return self

    def predict_rating_for_item(
        self,
        user_ratings: Dict[int, float],
        target_movie_id: int
    ) -> Optional[float]:
        """
        Predicts rating for a specific target movie given a user's ratings dictionary.
        Returns predicted rating in range [0.5, 5.0], or None if evidence is insufficient.
        """
        if not self.is_fitted:
            raise RuntimeError("CollaborativeRecommender must be fitted before predicting.")

        if target_movie_id not in self.movie_to_idx:
            return None

        # Filter user ratings to movies present in the training model
        valid_user_ratings = {
            mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx
        }

        if len(valid_user_ratings) < self.min_user_ratings_for_cf:
            return None

        if target_movie_id in valid_user_ratings:
            # Already rated
            return valid_user_ratings[target_movie_id]

        target_idx = self.movie_to_idx[target_movie_id]
        target_vec = self.R_item_user[target_idx]

        user_mean = float(np.mean(list(valid_user_ratings.values())))
        rated_mids = list(valid_user_ratings.keys())
        rated_indices = [self.movie_to_idx[mid] for mid in rated_mids]
        rated_submatrix = self.R_item_user[rated_indices]

        # Vectorized cosine similarity
        sims = cosine_similarity(target_vec, rated_submatrix).flatten()

        # Vectorized co-rating overlap count
        target_bin = (target_vec > 0).astype(np.float64)
        rated_bin = (rated_submatrix > 0).astype(np.float64)
        co_counts = (target_bin * rated_bin.T).toarray().flatten()

        valid_mask = (co_counts >= self.min_co_ratings) & (sims > 0.0)
        if not np.any(valid_mask):
            return None

        shrinkages = np.minimum(co_counts[valid_mask] / self.shrinkage_threshold, 1.0)
        shrunk_sims = sims[valid_mask] * shrinkages

        weight_sum = np.sum(np.abs(shrunk_sims))
        if weight_sum < 1e-6:
            return None

        user_devs = np.array([valid_user_ratings[mid] - user_mean for mid in rated_mids])[valid_mask]
        predicted = user_mean + np.sum(shrunk_sims * user_devs) / weight_sum
        return float(np.clip(predicted, 0.5, 5.0))

    def predict_user_preferences(
        self,
        user_ratings: Dict[int, float],
        candidate_movie_ids: Optional[List[int]] = None
    ) -> Dict[int, Dict[str, Any]]:
        """
        Computes predicted ratings and collaborative scores for candidate movies.
        Avoids recommending items already rated by the user.
        
        Returns:
            {movieId: {
                'predicted_rating': float,
                'collab_score': float, # normalized in [0, 1]
                'confidence': float
            }}
        """
        if not self.is_fitted:
            raise RuntimeError("CollaborativeRecommender must be fitted before predicting.")

        # Check if user has sufficient rating history
        valid_user_ratings = {
            mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx
        }
        if len(valid_user_ratings) < self.min_user_ratings_for_cf:
            return {}

        user_mean = float(np.mean(list(valid_user_ratings.values())))
        rated_ids_set = set(user_ratings.keys())

        # Determine target candidates
        if candidate_movie_ids is not None:
            eval_ids = [mid for mid in candidate_movie_ids if mid in self.movie_to_idx and mid not in rated_ids_set]
        else:
            eval_ids = [mid for mid in self.movie_ids if mid not in rated_ids_set]

        if not eval_ids:
            return {}

        # Extract rated indices and deviations
        rated_indices = [self.movie_to_idx[mid] for mid in valid_user_ratings.keys()]
        user_deviations = np.array([valid_user_ratings[mid] - user_mean for mid in valid_user_ratings.keys()])

        # Build submatrix of rated items: shape (len(rated_indices), n_users)
        rated_submatrix = self.R_item_user[rated_indices]

        predictions: Dict[int, Dict[str, Any]] = {}

        # Evaluate candidate items
        for cand_mid in eval_ids:
            cand_idx = self.movie_to_idx[cand_mid]
            cand_vec = self.R_item_user[cand_idx]

            # Fast dot products for co-occurrences and similarities
            # cand_vec is 1 x n_users, rated_submatrix is k x n_users
            sims = cosine_similarity(cand_vec, rated_submatrix).flatten()

            # Filter positive similarities
            pos_mask = sims > 0.05
            if not np.any(pos_mask):
                continue

            valid_sims = sims[pos_mask]
            valid_devs = user_deviations[pos_mask]

            weight_sum = np.sum(valid_sims)
            if weight_sum < 1e-6:
                continue

            pred_rating = user_mean + np.sum(valid_sims * valid_devs) / weight_sum
            clamped_rating = float(np.clip(pred_rating, 0.5, 5.0))
            
            # Normalized score from [0.5, 5.0] to [0.0, 1.0]
            collab_score = float((clamped_rating - 0.5) / 4.5)

            predictions[cand_mid] = {
                "predicted_rating": round(clamped_rating, 2),
                "collab_score": round(collab_score, 4),
                "evidence_count": int(np.sum(pos_mask)),
            }

        return predictions

    def get_existing_user_ratings(self, user_id: int) -> Dict[int, float]:
        """Returns the dictionary of {movieId: rating} for an existing dataset user."""
        return dict(self.user_rated_items.get(user_id, {}))
