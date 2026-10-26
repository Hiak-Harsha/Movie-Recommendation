"""
CineMatch Hybrid Recommendation Engine
Combines Content-Based (user taste vector), Collaborative Filtering (Item-kNN / Biased MF),
and Bayesian Popularity signals using stable, pool-independent normalization,
dynamic weight re-normalization, and factual evidence-based explanations.
"""
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import pandas as pd

import config
from src.content_model import ContentRecommender
from src.collaborative_model import CollaborativeEngine


class HybridRecommender:
    """
    Hybrid recommendation engine with candidate pooling, pool-independent scoring,
    and cold-start fallback.
    """

    def __init__(
        self,
        content_model: ContentRecommender,
        collab_engine: CollaborativeEngine,
        catalog_df: pd.DataFrame,
        default_weights: Optional[Dict[str, float]] = None
    ):
        self.content_model = content_model
        self.collab_engine = collab_engine
        self.catalog_df = catalog_df.reset_index(drop=True)
        self.default_weights = default_weights or config.DEFAULT_HYBRID_WEIGHTS

    def recommend_for_user(
        self,
        user_ratings: Dict[int, float],
        preferred_genres: Optional[List[str]] = None,
        genre_match_mode: str = "OR",
        year_range: Optional[Tuple[int, int]] = None,
        weights: Optional[Dict[str, float]] = None,
        top_n: int = 10
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generates personalized hybrid recommendations for a user rating profile.
        
        Args:
            user_ratings: {movieId: star_rating (0.5 to 5.0)}
            preferred_genres: Optional list of genre names
            genre_match_mode: 'OR' (match any) or 'AND' (match all)
            year_range: Optional (min_year, max_year)
            weights: Optional custom weights {'content', 'collaborative', 'popularity'}
            top_n: Number of recommendations to return
            
        Returns:
            (ranked_movie_cards, meta_info_dict)
        """
        active_weights = dict(weights or self.default_weights)
        rated_mids = set(user_ratings.keys())
        n_ratings = len(user_ratings)

        # Evidence Level & Cold-Start Detection
        if n_ratings >= 10:
            evidence_level = "High"
        elif n_ratings >= config.MIN_USER_RATINGS_FOR_CF:
            evidence_level = "Medium"
        elif n_ratings >= 1:
            evidence_level = "Low (Cold-Start)"
        else:
            evidence_level = "Zero (Popularity Baseline)"

        has_cf = n_ratings >= config.MIN_USER_RATINGS_FOR_CF
        is_fallback_mode = not has_cf

        fallback_reason = ""
        if is_fallback_mode:
            fallback_reason = (
                f"Profile contains {n_ratings} rating(s). Minimum {config.MIN_USER_RATINGS_FOR_CF} "
                f"ratings required for Collaborative Filtering. Reallocating weights to Content and Bayesian Popularity."
            )
            active_weights = dict(config.COLD_START_WEIGHTS)

        # 1. Collaborative Signal
        collab_predictions: Dict[int, Dict[str, Any]] = {}
        if has_cf:
            collab_predictions = self.collab_engine.predict_user_preferences(user_ratings)

        # 2. Content Signal: User Taste Vector
        user_taste_vec = self.content_model.build_user_taste_vector(user_ratings)
        content_scores_arr = self.content_model.score_candidates_for_user(user_taste_vec)

        # Liked movies for explanation derivation
        liked_mids = [mid for mid, r in user_ratings.items() if r >= 3.5]
        liked_titles = [
            self.content_model.get_movie_details(m)["display_title"]
            for m in liked_mids[:3] if self.content_model.get_movie_details(m)
        ]

        # 3. Candidate Pooling & Filtering
        w_content = active_weights.get("content", 0.45)
        w_collab = active_weights.get("collaborative", 0.45)
        w_pop = active_weights.get("popularity", 0.10)

        candidates = []
        for idx, row in self.catalog_df.iterrows():
            mid = int(row["movieId"])

            # Exclude already-rated movies
            if mid in rated_mids:
                continue

            # Genre filter
            cand_genres = set(row.get("genres_list", []))
            if preferred_genres:
                pref_set = set(preferred_genres)
                if genre_match_mode.upper() == "AND":
                    if not pref_set.issubset(cand_genres):
                        continue
                else:  # OR mode
                    if not any(g in cand_genres for g in pref_set):
                        continue

            # Year filter
            if year_range:
                cand_year = row.get("release_year")
                if cand_year is not None:
                    if cand_year < year_range[0] or cand_year > year_range[1]:
                        continue

            # Component Scores (all pool-independent in [0.0, 1.0])
            s_content = float(content_scores_arr[idx])
            s_pop = float(row.get("popularity_score", 0.0))

            collab_info = collab_predictions.get(mid)
            if collab_info is not None:
                s_collab = float(collab_info["collab_score"])
                predicted_rating = float(collab_info["predicted_rating"])
                neighbor_info = collab_info.get("neighbor_info")
                has_collab_pred = True
            else:
                s_collab = None
                predicted_rating = None
                neighbor_info = None
                has_collab_pred = False

            # Dynamic Re-weighting: missing is NEVER treated as zero!
            signals_used = []
            active_term_sum = 0.0
            active_weight_sum = 0.0

            if w_content > 0:
                active_term_sum += w_content * s_content
                active_weight_sum += w_content
                signals_used.append("content")

            if has_collab_pred and w_collab > 0:
                active_term_sum += w_collab * s_collab
                active_weight_sum += w_collab
                signals_used.append("collaborative")

            if w_pop > 0:
                active_term_sum += w_pop * s_pop
                active_weight_sum += w_pop
                signals_used.append("popularity")

            if active_weight_sum > 0:
                hybrid_score = active_term_sum / active_weight_sum
            else:
                hybrid_score = s_pop

            candidates.append({
                "movieId": mid,
                "row": row,
                "hybrid_score": float(hybrid_score),
                "content_score": float(s_content),
                "collab_score": s_collab,
                "predicted_rating": predicted_rating,
                "popularity_score": float(s_pop),
                "neighbor_info": neighbor_info,
                "signals_used": signals_used,
            })

        # Deterministic tie-breaking by (-hybrid_score, movieId)
        candidates.sort(key=lambda x: (-x["hybrid_score"], x["movieId"]))
        top_candidates = candidates[:top_n]

        # 4. Evidence-based Explanations
        results = []
        for item in top_candidates:
            mid = item["movieId"]
            row = item["row"]
            reasons = []

            # Reason 1: Collaborative preference
            if item["predicted_rating"] is not None:
                reasons.append(f"Predicted rating ≈ {item['predicted_rating']}★ for your taste profile")

            # Reason 2: Liked by people who also liked X (Item-kNN evidence)
            if item["neighbor_info"] is not None:
                n_mid = item["neighbor_info"]["neighbor_movieId"]
                n_sim = item["neighbor_info"]["similarity"]
                n_co = item["neighbor_info"]["co_raters"]
                n_details = self.content_model.get_movie_details(n_mid)
                n_title = n_details["display_title"] if n_details else f"Movie #{n_mid}"
                reasons.append(f"Liked by people who also liked {n_title} (similarity {n_sim}, {n_co} co-raters)")

            # Reason 3: Genre alignment
            cand_genres = row.get("genres_list", [])
            if preferred_genres:
                matching_pref = [g for g in cand_genres if g in preferred_genres]
                if matching_pref:
                    reasons.append(f"Matches preferred genre(s): {', '.join(matching_pref)}")

            # Reason 4: Content overlap with user taste
            if item["content_score"] >= 0.25 and liked_titles:
                reasons.append(f"High stylistic overlap with movies you rated highly ({', '.join(liked_titles)})")

            # Reason 5: Community rating
            w_rating = row.get("weighted_rating", 0.0)
            r_count = row.get("rating_count", 0)
            if r_count >= 10:
                reasons.append(f"Community rating {w_rating}★ from {r_count:,} reviews (Bayesian prior)")

            if not reasons:
                reasons.append("Discovered through catalog baseline ranking.")

            results.append({
                "movieId": mid,
                "title": str(row["title"]),
                "display_title": str(row.get("display_title", row["title"])),
                "release_year": row.get("release_year"),
                "genres_display": str(row.get("genres_display", "")),
                "genres_list": cand_genres,
                "imdbId": row.get("imdbId"),
                "hybrid_score": round(item["hybrid_score"], 4),
                "content_score": round(item["content_score"], 4),
                "collab_score": round(item["collab_score"], 4) if item["collab_score"] is not None else None,
                "predicted_rating": item["predicted_rating"],
                "popularity_score": round(item["popularity_score"], 4),
                "rating_count": int(row.get("rating_count", 0)),
                "mean_rating": float(row.get("mean_rating", 0.0)),
                "weighted_rating": float(row.get("weighted_rating", 0.0)),
                "signals_used": item["signals_used"],
                "reasons": reasons,
            })

        meta_info = {
            "evidence_level": evidence_level,
            "is_fallback": is_fallback_mode,
            "fallback_reason": fallback_reason,
            "active_weights": active_weights,
            "user_ratings_count": n_ratings,
            "cf_predictions_count": len(collab_predictions),
            "total_candidates_evaluated": len(candidates),
        }

        return results, meta_info
