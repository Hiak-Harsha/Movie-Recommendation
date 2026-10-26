"""
CineMatch Hybrid Recommendation Engine
Combines Content-Based, Collaborative Filtering, and Bayesian Popularity signals
into a unified ranking pipeline with candidate filtering, cold-start fallback,
and evidence-based transparent explanations.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel

import config
from src.content_model import ContentRecommender
from src.collaborative_model import CollaborativeRecommender


class HybridRecommender:
    """
    Hybrid recommendation engine combining content, collaborative, and popularity signals.
    Excludes rated items, handles cold-start users honestly, and produces explainable recommendations.
    """

    def __init__(
        self,
        content_model: ContentRecommender,
        collab_model: CollaborativeRecommender,
        catalog_df: pd.DataFrame,
        default_weights: Optional[Dict[str, float]] = None
    ):
        self.content_model = content_model
        self.collab_model = collab_model
        self.catalog_df = catalog_df.reset_index(drop=True)
        self.default_weights = default_weights or config.DEFAULT_HYBRID_WEIGHTS

    def recommend_for_user(
        self,
        user_ratings: Dict[int, float],
        preferred_genres: Optional[List[str]] = None,
        year_range: Optional[Tuple[int, int]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_n: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates personalized recommendations for an active user profile.
        
        Args:
            user_ratings: {movieId: star_rating (0.5 to 5.0)}
            preferred_genres: Optional genre filter or boost
            year_range: Optional (min_year, max_year)
            weights: Optional custom signal weights {'content', 'collaborative', 'popularity'}
            top_n: Number of recommendations to return
            
        Returns:
            (ranked_movie_cards, meta_info_dict)
        """
        active_weights = dict(weights or self.default_weights)
        rated_movie_ids = set(user_ratings.keys())

        # Determine if collaborative filtering can run
        has_enough_cf_ratings = len(user_ratings) >= self.collab_model.min_user_ratings_for_cf
        is_fallback_mode = not has_enough_cf_ratings

        fallback_reason = ""
        if is_fallback_mode:
            fallback_reason = (
                f"Active profile has {len(user_ratings)} rating(s). Minimum {self.collab_model.min_user_ratings_for_cf} "
                f"ratings required for Collaborative Filtering. Reallocating weights to Content and Bayesian Popularity."
            )
            # Reallocate weights
            active_weights = dict(config.COLD_START_WEIGHTS)

        # 1. Compute Collaborative predictions if eligible
        collab_predictions: Dict[int, Dict[str, Any]] = {}
        if not is_fallback_mode:
            collab_predictions = self.collab_model.predict_user_preferences(user_ratings)

        # 2. Build User Content Profile Vector
        # Use user ratings >= 3.0 to construct a weighted profile vector in TF-IDF space
        user_profile_vector = None
        liked_movie_titles = []
        if user_ratings:
            profile_vectors = []
            profile_weights = []
            for mid, rating in user_ratings.items():
                if mid in self.content_model.movie_id_to_idx and rating >= 3.0:
                    idx = self.content_model.movie_id_to_idx[mid]
                    vec = self.content_model.tfidf_matrix[idx]
                    weight = rating - 2.5  # ratings 3.0 -> 0.5, 4.0 -> 1.5, 5.0 -> 2.5
                    profile_vectors.append(vec.multiply(weight))
                    profile_weights.append(weight)
                    liked_movie_titles.append(self.catalog_df.iloc[idx]["clean_title"])

            if profile_vectors and sum(profile_weights) > 0:
                # Sum and normalize sparse vectors
                user_profile_vector = sum(profile_vectors) / sum(profile_weights)

        # If no ratings >= 3.0 or no user ratings at all, use genre vector if preferred_genres provided
        if user_profile_vector is None and preferred_genres:
            genre_query = " ".join([g.lower().replace("-", "_").replace(" ", "_") for g in preferred_genres])
            user_profile_vector = self.content_model.vectorizer.transform([genre_query])

        # Compute content similarity across all movies if profile vector exists
        content_sims = np.zeros(len(self.catalog_df))
        if user_profile_vector is not None:
            content_sims = linear_kernel(user_profile_vector, self.content_model.tfidf_matrix).flatten()

        # 3. Filter candidates and combine signals
        candidates = []
        w_content = active_weights.get("content", 0.45)
        w_collab = active_weights.get("collaborative", 0.45)
        w_pop = active_weights.get("popularity", 0.10)

        for idx, row in self.catalog_df.iterrows():
            mid = int(row["movieId"])

            # Exclude movies already rated by the active user
            if mid in rated_movie_ids:
                continue

            # Filter by genre if preferred_genres provided
            cand_genres = set(row.get("genres_list", []))
            if preferred_genres:
                if not any(g in cand_genres for g in preferred_genres):
                    continue

            # Filter by release year
            if year_range:
                cand_year = row.get("release_year")
                if cand_year is not None:
                    if cand_year < year_range[0] or cand_year > year_range[1]:
                        continue

            # Component Scores
            s_content = float(content_sims[idx]) if idx < len(content_sims) else 0.0
            s_pop = float(row.get("popularity_score", 0.0))

            # Collaborative Score
            collab_info = collab_predictions.get(mid)
            if collab_info is not None:
                s_collab = float(collab_info["collab_score"])
                predicted_rating = float(collab_info["predicted_rating"])
                has_collab = True
            else:
                s_collab = None
                predicted_rating = None
                has_collab = False

            # Hybrid score calculation with honest missing signal handling
            if has_collab and w_collab > 0:
                total_w = w_content + w_collab + w_pop
                hybrid_score = (w_content * s_content + w_collab * s_collab + w_pop * s_pop) / total_w
            else:
                # Re-normalize between content and popularity
                total_w = w_content + w_pop
                if total_w > 0:
                    hybrid_score = (w_content * s_content + w_pop * s_pop) / total_w
                else:
                    hybrid_score = s_pop

            candidates.append({
                "idx": idx,
                "movieId": mid,
                "row": row,
                "hybrid_score": float(hybrid_score),
                "content_score": float(s_content),
                "collab_score": s_collab,
                "predicted_rating": predicted_rating,
                "popularity_score": float(s_pop),
                "has_collab": has_collab,
            })

        # Sort by hybrid score descending
        candidates.sort(key=lambda x: x["hybrid_score"], reverse=True)
        top_items = candidates[:top_n]

        # 4. Generate structured results and evidence-based explanations
        results = []
        for item in top_items:
            mid = item["movieId"]
            row = item["row"]
            reasons = []

            # Evidence 1: Collaborative preference
            if item["predicted_rating"] is not None:
                reasons.append(f"Predicted preference: {item['predicted_rating']} / 5.0★ based on your rating history")

            # Evidence 2: Genre alignment
            cand_genres = row.get("genres_list", [])
            if preferred_genres:
                matching_pref = [g for g in cand_genres if g in preferred_genres]
                if matching_pref:
                    reasons.append(f"Matches preferred genre(s): {', '.join(matching_pref)}")

            # Evidence 3: Content profile similarity
            if item["content_score"] > 0.2 and liked_movie_titles:
                sample_liked = liked_movie_titles[:2]
                reasons.append(f"High stylistic and genre overlap with your top rated movies ({', '.join(sample_liked)})")

            # Evidence 4: Community popularity & Bayesian rating
            w_rating = row.get("weighted_rating", 0.0)
            r_count = row.get("rating_count", 0)
            if r_count >= 10:
                reasons.append(f"Community favorite: {w_rating}★ Bayesian rating ({r_count} ratings)")
            elif r_count > 0:
                reasons.append(f"Community rating: {row.get('mean_rating', 0.0)}★ ({r_count} ratings)")

            if not reasons:
                reasons.append("Discovered via catalog popularity baseline")

            results.append({
                "movieId": mid,
                "title": str(row["title"]),
                "clean_title": str(row.get("clean_title", row["title"])),
                "release_year": row.get("release_year"),
                "genres_display": str(row.get("genres_display", "")),
                "genres_list": cand_genres,
                "hybrid_score": round(item["hybrid_score"], 4),
                "content_score": round(item["content_score"], 4),
                "collab_score": round(item["collab_score"], 4) if item["collab_score"] is not None else None,
                "predicted_rating": item["predicted_rating"],
                "popularity_score": round(item["popularity_score"], 4),
                "rating_count": int(row.get("rating_count", 0)),
                "mean_rating": float(row.get("mean_rating", 0.0)),
                "weighted_rating": float(row.get("weighted_rating", 0.0)),
                "reasons": reasons,
            })

        meta_info = {
            "is_fallback": is_fallback_mode,
            "fallback_reason": fallback_reason,
            "active_weights": active_weights,
            "user_ratings_count": len(user_ratings),
            "cf_predictions_count": len(collab_predictions),
            "total_candidates_evaluated": len(candidates),
        }

        return results, meta_info
