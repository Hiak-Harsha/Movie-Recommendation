"""
CineMatch Learned Blend & Re-Ranking Model
Trains an interpretable Logistic Regression ranker on validation-period ratings,
replaces fixed heuristic weights, exports signal coefficients, and implements
vectorized candidate filtering and MMR diversity re-ranking.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from ml.config import settings


FEATURE_NAMES = [
    "mf_score",
    "knn_score",
    "content_cosine",
    "popularity_score",
    "mf_percentile",
    "knn_percentile",
    "content_percentile",
    "pop_percentile",
    "log_vote_count",
    "item_age_scaled",
    "genre_overlap"
]


class LearnedBlendRanker:
    """
    Supervised ranker trained on validation pairs:
      P(relevant | user, item features) = sigmoid(w · x + b)
    Provides exact linear feature contributions: contribution_s = w_s * x_s.
    """

    def __init__(self, random_seed: int = settings.random_seed):
        self.random_seed = random_seed
        self.model = LogisticRegression(
            C=1.0,
            penalty="l2",
            solver="lbfgs",
            max_iter=300,
            random_state=random_seed
        )
        self.coefficients: Dict[str, float] = {}
        self.intercept: float = 0.0
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> "LearnedBlendRanker":
        """Fits logistic regression on validation feature matrix and binary relevance labels."""
        if len(X) < 10 or len(np.unique(y)) < 2:
            # Fallback prior coefficients if validation pairs are insufficient
            self.coefficients = {
                "mf_score": 1.25,
                "knn_score": 1.10,
                "content_cosine": 0.85,
                "popularity_score": 0.75,
                "mf_percentile": 0.30,
                "knn_percentile": 0.25,
                "content_percentile": 0.20,
                "pop_percentile": 0.15,
                "log_vote_count": 0.20,
                "item_age_scaled": -0.05,
                "genre_overlap": 0.40
            }
            self.intercept = -1.5
            self.is_fitted = True
            return self

        self.model.fit(X, y)
        coef_vals = self.model.coef_[0]
        self.coefficients = {name: float(round(coef_vals[i], 4)) for i, name in enumerate(FEATURE_NAMES)}
        self.intercept = float(round(self.model.intercept_[0], 4))
        self.is_fitted = True
        return self

    def score_candidates(
        self,
        features: np.ndarray,
        signal_mix: Optional[Dict[str, float]] = None
    ) -> Tuple[np.ndarray, List[Dict[str, float]]]:
        """
        Computes final ranking scores and per-candidate feature contributions.
        Allows interactive user steering via signal_mix multipliers:
          { 'collaborative': 1.0, 'content': 1.0, 'popularity': 1.0 }
        """
        if not self.is_fitted:
            # Default fallback score based on mean
            return np.mean(features[:, :4], axis=1), [{}] * len(features)

        weights = np.array([self.coefficients.get(name, 0.0) for name in FEATURE_NAMES], dtype=np.float32)

        # Apply interactive user steering if provided
        if signal_mix:
            collab_mult = float(signal_mix.get("collaborative", 1.0))
            content_mult = float(signal_mix.get("content", 1.0))
            pop_mult = float(signal_mix.get("popularity", 1.0))

            # indices in FEATURE_NAMES:
            # 0: mf, 1: knn, 2: content, 3: pop
            weights[0] *= collab_mult
            weights[1] *= collab_mult
            weights[2] *= content_mult
            weights[3] *= pop_mult

        logits = np.dot(features, weights) + self.intercept
        # Sigmoid probability
        scores = 1.0 / (1.0 + np.exp(-np.clip(logits, -15.0, 15.0)))

        # Compute structured contributions for each candidate
        contributions_list = []
        for i in range(len(features)):
            feat_row = features[i]
            contrib = {
                "mf": round(float(weights[0] * feat_row[0]), 3),
                "knn": round(float(weights[1] * feat_row[1]), 3),
                "content": round(float(weights[2] * feat_row[2]), 3),
                "popularity": round(float(weights[3] * feat_row[3]), 3)
            }
            contributions_list.append(contrib)

        return scores, contributions_list


def compute_mmr_reranking(
    candidate_movie_ids: List[int],
    base_scores: np.ndarray,
    candidate_genres: List[List[str]],
    top_n: int = 20,
    diversity_lambda: float = settings.default_diversity_lambda
) -> List[int]:
    """
    Maximal Marginal Relevance (MMR) re-ranking to penalize franchise and genre redundancy:
      MMR = argmax [ (1 - λ) * score(i) - λ * max_{j in S} Sim(i, j) ]
    """
    if len(candidate_movie_ids) <= top_n or diversity_lambda <= 0.0:
        return candidate_movie_ids[:top_n]

    selected_indices: List[int] = []
    unselected_indices = list(range(len(candidate_movie_ids)))

    # Select initial highest scoring candidate
    best_init = int(np.argmax(base_scores))
    selected_indices.append(best_init)
    unselected_indices.remove(best_init)

    genre_sets = [set(g) for g in candidate_genres]

    while len(selected_indices) < top_n and unselected_indices:
        best_idx = -1
        best_mmr_score = -float("inf")

        for u_idx in unselected_indices:
            relevance = base_scores[u_idx]
            u_genres = genre_sets[u_idx]

            # Compute maximum genre Jaccard similarity to already selected set S
            max_sim = 0.0
            for s_idx in selected_indices:
                s_genres = genre_sets[s_idx]
                if u_genres or s_genres:
                    jaccard = len(u_genres & s_genres) / max(len(u_genres | s_genres), 1)
                    if jaccard > max_sim:
                        max_sim = jaccard

            mmr = (1.0 - diversity_lambda) * relevance - diversity_lambda * max_sim
            if mmr > best_mmr_score:
                best_mmr_score = mmr
                best_idx = u_idx

        if best_idx >= 0:
            selected_indices.append(best_idx)
            unselected_indices.remove(best_idx)
        else:
            break

    return [candidate_movie_ids[i] for i in selected_indices]
