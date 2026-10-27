"""
CineMatch Real-Time Serving Engine
Loads precomputed artifacts into memory in lifespan hook.
Implements:
  1. O(1) array neighbour lookups for /similar.
  2. Typo-tolerant, article-aware, year-token search via rapidfuzz with character match offsets for /search.
  3. Vectorized candidate generation, boolean filter masks, and learned blend scoring for /recommendations.
  4. MMR diversity and novelty re-ranking.
  5. Strict cold-start ladder (0 ratings -> popularity, 1-4 ratings -> content+pop, 5+ -> full hybrid).
"""
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import joblib
import numpy as np
import pandas as pd
from rapidfuzz import fuzz, process
from scipy.sparse import csr_matrix, load_npz

from apps.api.config import api_settings
from apps.api.schemas import (
    MovieCard,
    SearchResult,
    SignalExplanation,
    SignalContributions
)
from ml.data_loader import compute_dataset_fingerprint, resolve_data_directory
from ml.preprocessing import generate_search_key, normalize_genres
from ml.blend import compute_mmr_reranking

logger = logging.getLogger("cinematch.api.engine")

ALL_GENRES = [
    "action", "adventure", "animation", "children", "comedy", "crime",
    "documentary", "drama", "fantasy", "film_noir", "horror", "imax",
    "musical", "mystery", "romance", "sci_fi", "thriller", "war", "western"
]
GENRE_TO_IDX = {g: i for i, g in enumerate(ALL_GENRES)}


class ServingEngine:
    def __init__(self):
        self.is_loaded: bool = False
        self.fingerprint: str = ""

        # Catalog & Dataframes
        self.catalog_df: Optional[pd.DataFrame] = None
        self.meta_dict: Dict[str, Any] = {}
        self.demo_profiles: List[Dict[str, Any]] = []

        # Vectorized lookup arrays
        self.movie_ids: np.ndarray = np.array([], dtype=np.int32)
        self.movie_to_idx: Dict[int, int] = {}
        self.idx_to_movie: Dict[int, int] = {}
        self.years: np.ndarray = np.array([], dtype=np.int32)
        self.vote_counts: np.ndarray = np.array([], dtype=np.int32)
        self.weighted_ratings: np.ndarray = np.array([], dtype=np.float32)
        self.scaled_popularities: np.ndarray = np.array([], dtype=np.float32)
        self.genre_matrix: np.ndarray = np.array([], dtype=bool)  # (N, len(ALL_GENRES))

        # Model weights and precomputed tables
        self.Q: Optional[np.ndarray] = None  # (N_items, K)
        self.bi: Optional[np.ndarray] = None # (N_items,)
        self.knn_idx: Optional[np.ndarray] = None  # (N_items, 100)
        self.knn_sim: Optional[np.ndarray] = None  # (N_items, 100)
        self.knn_co: Optional[np.ndarray] = None   # (N_items, 100)
        self.content_idx: Optional[np.ndarray] = None
        self.content_sim: Optional[np.ndarray] = None
        self.tfidf_matrix: Optional[csr_matrix] = None
        self.blend_ranker: Any = None

        # Search index
        self.search_keys: List[str] = []
        self.display_titles: List[str] = []

    def load_artifacts(self, custom_artifact_path: Optional[Path] = None):
        """Loads serialized artifacts from disk and verifies dataset fingerprint."""
        t0 = time.time()
        data_dir = resolve_data_directory(api_settings.data_dir)
        expected_fp = compute_dataset_fingerprint(data_dir)

        if custom_artifact_path is not None:
            artifact_dir = custom_artifact_path
        else:
            artifact_dir = api_settings.artifacts_dir / expected_fp
            if not artifact_dir.exists():
                # Check for any valid fingerprint subfolder in artifacts/
                fps = [p for p in api_settings.artifacts_dir.iterdir() if p.is_dir() and (p / "catalog.parquet").exists()]
                if fps:
                    artifact_dir = fps[0]
                else:
                    raise RuntimeError(f"Artifacts missing for fingerprint {expected_fp}. Run: python -m ml.build_artifacts")

        # Load Meta & Verify
        meta_path = artifact_dir / "meta.json"
        if not meta_path.exists():
            raise RuntimeError(f"Invalid artifact directory: missing {meta_path.name}")

        with open(meta_path, "r", encoding="utf-8") as f:
            self.meta_dict = json.load(f)

        self.fingerprint = self.meta_dict.get("dataset_fingerprint", "")
        if self.fingerprint != expected_fp:
            logger.warning(f"Fingerprint mismatch: artifacts have {self.fingerprint}, data has {expected_fp}")

        # 1. Load Catalog
        self.catalog_df = pd.read_parquet(artifact_dir / "catalog.parquet")
        self.movie_ids = self.catalog_df["movieId"].values.astype(np.int32)
        self.movie_to_idx = {mid: i for i, mid in enumerate(self.movie_ids)}
        self.idx_to_movie = {i: mid for mid, i in self.movie_to_idx.items()}

        n_items = len(self.movie_ids)
        self.years = self.catalog_df["year"].fillna(-1).values.astype(np.int32)
        self.vote_counts = self.catalog_df["vote_count"].values.astype(np.int32)
        self.weighted_ratings = self.catalog_df["weighted_rating"].values.astype(np.float32)
        self.scaled_popularities = self.catalog_df["scaled_popularity"].values.astype(np.float32)

        # Build fast genre boolean matrix (N, 19)
        self.genre_matrix = np.zeros((n_items, len(ALL_GENRES)), dtype=bool)
        for i, genres_str in enumerate(self.catalog_df["genres_list"]):
            if isinstance(genres_str, str) and genres_str:
                for g in genres_str.split("|"):
                    if g in GENRE_TO_IDX:
                        self.genre_matrix[i, GENRE_TO_IDX[g]] = True

        # Search index
        self.search_keys = self.catalog_df["search_key"].fillna("").tolist()
        self.display_titles = self.catalog_df["display_title"].fillna("").tolist()
        self.word_index: Dict[str, List[int]] = {}
        for idx, key in enumerate(self.search_keys):
            for word in key.split():
                if len(word) >= 2:
                    if word not in self.word_index:
                        self.word_index[word] = []
                    self.word_index[word].append(idx)

        # 2. Load Models
        self.Q = np.load(artifact_dir / "item_factors.npy")
        self.bi = np.load(artifact_dir / "item_bias.npy")
        self.knn_idx = np.load(artifact_dir / "knn_idx.npy")
        self.knn_sim = np.load(artifact_dir / "knn_sim.npy")
        self.knn_co = np.load(artifact_dir / "knn_co.npy")
        self.content_idx = np.load(artifact_dir / "content_idx.npy")
        self.content_sim = np.load(artifact_dir / "content_sim.npy")
        self.tfidf_matrix = load_npz(artifact_dir / "tfidf.npz")
        self.blend_ranker = joblib.load(artifact_dir / "blend_model.joblib")
        self.demo_profiles = self.meta_dict.get("demo_profiles", [])

        self.is_loaded = True
        duration = time.time() - t0
        logger.info(f"ServingEngine loaded in {duration:.3f} s (cold start target < 3 s).")

    def get_movie_metadata(self, movie_id: int) -> Dict[str, Any]:
        """Returns metadata dictionary for a movieId from the preloaded catalog."""
        if not self.is_loaded or movie_id not in self.movie_to_idx:
            return {}
        idx = self.movie_to_idx[movie_id]
        row = self.catalog_df.iloc[idx]
        genres_str = row.get("genres_list", "")
        genres = genres_str.split("|") if isinstance(genres_str, str) and genres_str else []
        year = int(row["year"]) if "year" in row and pd.notna(row["year"]) and row["year"] > 0 else None
        tmdb_id = int(row["tmdbId"]) if "tmdbId" in row and pd.notna(row["tmdbId"]) and row["tmdbId"] > 0 else None
        imdb_id = str(row["imdbId"]) if "imdbId" in row and pd.notna(row["imdbId"]) else None
        return {
            "movieId": movie_id,
            "title": str(row.get("title", f"Movie #{movie_id}")),
            "display_title": str(row.get("display_title", row.get("title", f"Movie #{movie_id}"))),
            "year": year,
            "genres": genres,
            "vote_average": float(row.get("vote_average", 0.0)),
            "vote_count": int(row.get("vote_count", 0)),
            "weighted_rating": float(row.get("weighted_rating", 0.0)),
            "tmdbId": tmdb_id,
            "imdbId": imdb_id,
        }


    def _apply_boolean_filters(
        self,
        candidate_indices: np.ndarray,
        genres: Optional[List[str]] = None,
        genre_mode: str = "OR",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        min_support: int = 5,
        excluded_ids: Optional[Set[int]] = None
    ) -> np.ndarray:
        """Vectorized filter application over precomputed NumPy arrays."""
        mask = np.ones(len(candidate_indices), dtype=bool)

        # Min support mask
        if min_support > 0:
            mask &= (self.vote_counts[candidate_indices] >= min_support)

        # Year bounds
        if year_min is not None:
            mask &= (self.years[candidate_indices] >= year_min)
        if year_max is not None:
            mask &= (self.years[candidate_indices] <= year_max)

        # Excluded movie IDs (e.g. seed or user's rated items)
        if excluded_ids:
            c_mids = self.movie_ids[candidate_indices]
            mask &= ~np.isin(c_mids, list(excluded_ids))

        # Genre filtering
        if genres:
            clean_g = [g.lower().replace("-", "_").replace(" ", "_") for g in genres if g.lower().replace("-", "_").replace(" ", "_") in GENRE_TO_IDX]
            if clean_g:
                g_indices = [GENRE_TO_IDX[g] for g in clean_g]
                sub_genres = self.genre_matrix[candidate_indices][:, g_indices]
                if genre_mode.upper() == "AND":
                    genre_pass = sub_genres.all(axis=1)
                else:
                    genre_pass = sub_genres.any(axis=1)
                mask &= genre_pass

        return candidate_indices[mask]

    def search_movies(self, query: str, limit: int = 20) -> List[SearchResult]:
        """
        Fast typo-tolerant, article-aware search using rapidfuzz token matching and character offsets.
        Target latency < 30 ms.
        """
        if not self.is_loaded or not query or not query.strip():
            return []

        clean_q = generate_search_key(query)
        q_lower = query.strip().lower()

        # Extract potential 4-digit year from query
        year_match = None
        for token in q_lower.split():
            if token.isdigit() and len(token) == 4:
                year_match = int(token)
                break

        # Candidate pre-filtering using inverted word index
        cand_indices_set: Set[int] = set()
        q_words = clean_q.split()
        for w in q_words:
            if w in self.word_index:
                cand_indices_set.update(self.word_index[w])
            for indexed_w, indices in self.word_index.items():
                if indexed_w.startswith(w) and len(indexed_w) > len(w):
                    cand_indices_set.update(indices[:50])

        if cand_indices_set and len(cand_indices_set) <= 800:
            target_indices = list(cand_indices_set)
            target_keys = [self.search_keys[i] for i in target_indices]
            raw_cands = process.extract(
                clean_q,
                target_keys,
                scorer=fuzz.token_set_ratio,
                limit=limit * 2
            )
            candidates = [(match_key, score, target_indices[local_idx]) for match_key, score, local_idx in raw_cands]
        else:
            candidates = process.extract(
                clean_q,
                self.search_keys,
                scorer=fuzz.token_set_ratio,
                limit=limit * 2
            )

        results: List[SearchResult] = []
        for match_key, score, idx in candidates:
            if score < 40:
                continue

            row = self.catalog_df.iloc[idx]
            disp_title = str(row["display_title"])

            # Bonus for year match if specified
            final_score = float(score)
            if year_match and row["year"] == year_match:
                final_score += 25.0

            # Compute character match offsets for frontend highlighting
            offsets = []
            lower_disp = disp_title.lower()
            start = lower_disp.find(clean_q)
            if start >= 0:
                offsets = [start, start + len(clean_q)]
            else:
                # Find first matching word
                for word in clean_q.split():
                    w_start = lower_disp.find(word)
                    if w_start >= 0:
                        offsets = [w_start, w_start + len(word)]
                        break

            results.append(
                SearchResult(
                    movieId=int(row["movieId"]),
                    title=str(row["title"]),
                    display_title=disp_title,
                    year=int(row["year"]) if pd.notna(row["year"]) else None,
                    genres=str(row["genres_list"]).split("|") if row["genres_list"] else [],
                    vote_count=int(row["vote_count"]),
                    vote_average=float(row["vote_average"]),
                    weighted_rating=float(row["weighted_rating"]),
                    imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                    tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None,
                    score=round(final_score, 2),
                    match_offsets=offsets
                )
            )

        results = sorted(results, key=lambda r: r.score, reverse=True)[:limit]
        return results

    def get_similar_movies(
        self,
        movie_id: int,
        top_n: int = 20,
        genres: Optional[List[str]] = None,
        genre_mode: str = "OR",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None
    ) -> Tuple[Optional[MovieCard], List[MovieCard]]:
        """
        O(1) array slice lookup combining content cosine and Item-kNN co-rating similarity.
        Target latency < 40 ms.
        """
        if not self.is_loaded or movie_id not in self.movie_to_idx:
            return None, []

        seed_idx = self.movie_to_idx[movie_id]
        seed_row = self.catalog_df.iloc[seed_idx]
        seed_genres = str(seed_row["genres_list"]).split("|") if seed_row["genres_list"] else []

        seed_card = MovieCard(
            movieId=int(seed_row["movieId"]),
            title=str(seed_row["title"]),
            display_title=str(seed_row["display_title"]),
            year=int(seed_row["year"]) if pd.notna(seed_row["year"]) else None,
            genres=seed_genres,
            vote_count=int(seed_row["vote_count"]),
            vote_average=float(seed_row["vote_average"]),
            weighted_rating=float(seed_row["weighted_rating"]),
            imdbId=f"tt{int(seed_row['imdbId']):07d}" if pd.notna(seed_row.get("imdbId")) else None,
            tmdbId=int(seed_row["tmdbId"]) if pd.notna(seed_row.get("tmdbId")) else None,
            score=1.0
        )

        # 1. Fetch precomputed content neighbours (top-100)
        c_neighs = self.content_idx[seed_idx]
        c_sims = self.content_sim[seed_idx]

        # 2. Fetch precomputed Item-kNN neighbours if item exists in ratings
        k_sims_dict: Dict[int, Tuple[float, int]] = {}
        if seed_idx < len(self.knn_idx):
            k_neighs = self.knn_idx[seed_idx]
            k_sims = self.knn_sim[seed_idx]
            k_cos = self.knn_co[seed_idx]
            for pos, n_idx in enumerate(k_neighs):
                if n_idx >= 0 and k_sims[pos] > 0:
                    k_sims_dict[n_idx] = (float(k_sims[pos]), int(k_cos[pos]))

        # Candidate union of content + knn
        all_candidate_indices = np.array([n for n in c_neighs if n >= 0], dtype=np.int32)

        # Apply boolean filters
        filtered_indices = self._apply_boolean_filters(
            all_candidate_indices,
            genres=genres,
            genre_mode=genre_mode,
            year_min=year_min,
            year_max=year_max,
            min_support=0,
            excluded_ids={movie_id}
        )

        cards: List[MovieCard] = []
        for c_idx in filtered_indices:
            row = self.catalog_df.iloc[c_idx]
            cand_mid = int(row["movieId"])
            cand_genres = str(row["genres_list"]).split("|") if row["genres_list"] else []

            # Blended similarity: 0.60 content cosine + 0.40 item-kNN (if co-rated)
            pos_c = np.where(c_neighs == c_idx)[0]
            sim_content = float(c_sims[pos_c[0]]) if len(pos_c) > 0 else 0.0

            sim_knn = 0.0
            co_raters = 0
            if c_idx in k_sims_dict:
                sim_knn, co_raters = k_sims_dict[c_idx]

            if sim_knn > 0:
                final_sim = 0.60 * sim_content + 0.40 * sim_knn
            else:
                final_sim = sim_content

            # Structured evidence signals
            signals = []
            overlap_genres = list(set(seed_genres) & set(cand_genres))
            if overlap_genres:
                signals.append(SignalExplanation(type="genre", details={"overlap": overlap_genres}))
            if co_raters > 0:
                signals.append(SignalExplanation(type="neighbor", details={"movieId": movie_id, "sim": round(sim_knn, 3), "coRaters": co_raters}))

            cards.append(
                MovieCard(
                    movieId=cand_mid,
                    title=str(row["title"]),
                    display_title=str(row["display_title"]),
                    year=int(row["year"]) if pd.notna(row["year"]) else None,
                    genres=cand_genres,
                    vote_count=int(row["vote_count"]),
                    vote_average=float(row["vote_average"]),
                    weighted_rating=float(row["weighted_rating"]),
                    score=round(float(final_sim), 4),
                    signals=signals,
                    contributions=SignalContributions(content=round(sim_content, 3), knn=round(sim_knn, 3)),
                    imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                    tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None
                )
            )

        cards = sorted(cards, key=lambda c: (-c.score, c.movieId))[:top_n]
        return seed_card, cards

    def get_recommendations(
        self,
        user_ratings: Dict[int, float],
        top_n: int = 20,
        genres: Optional[List[str]] = None,
        genre_mode: str = "OR",
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        min_support: int = 5,
        diversity_lambda: float = 0.15,
        novelty_boost: float = 0.05,
        recency_prior: float = 0.0,
        signal_mix: Optional[Dict[str, float]] = None
    ) -> Tuple[List[MovieCard], str, str]:
        """
        Vectorized candidate generation, learned blend scoring, and MMR re-ranking.
        Target latency < 150 ms for users with 135 ratings.
        """
        n_ratings = len(user_ratings)
        excluded_ids = set(user_ratings.keys())

        # Rung 1: 0 ratings -> Popularity Baseline
        if n_ratings == 0:
            cold_tier = "zero_ratings"
            summary = "Cold-start fallback: showing Bayesian popularity baseline filtered by criteria."
            all_indices = np.arange(len(self.movie_ids), dtype=np.int32)
            filtered = self._apply_boolean_filters(
                all_indices, genres, genre_mode, year_min, year_max, min_support=min_support, excluded_ids=excluded_ids
            )
            top_indices = filtered[np.argsort(-self.weighted_ratings[filtered])[:top_n]]
            cards = []
            for idx in top_indices:
                row = self.catalog_df.iloc[idx]
                score = float(self.scaled_popularities[idx])
                cards.append(
                    MovieCard(
                        movieId=int(row["movieId"]),
                        title=str(row["title"]),
                        display_title=str(row["display_title"]),
                        year=int(row["year"]) if pd.notna(row["year"]) else None,
                        genres=str(row["genres_list"]).split("|") if row["genres_list"] else [],
                        vote_count=int(row["vote_count"]),
                        vote_average=float(row["vote_average"]),
                        weighted_rating=float(row["weighted_rating"]),
                        score=round(score, 4),
                        signals=[SignalExplanation(type="popularity", details={"weighted_rating": float(row["weighted_rating"]), "votes": int(row["vote_count"])})],
                        contributions=SignalContributions(popularity=1.0),
                        imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                        tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None
                    )
                )
            return cards, cold_tier, summary

        # Rung 2: 1-4 ratings -> Content Taste Vector + Popularity
        if n_ratings < 5:
            cold_tier = "content_fallback"
            summary = f"Profile has {n_ratings} ratings (>= 5 needed for full collaborative filtering). Using directional taste vector + popularity."
            valid_mids = [self.movie_to_idx[m] for m in user_ratings.keys() if m in self.movie_to_idx]
            r_vals_rung2 = np.array([user_ratings[self.idx_to_movie[idx]] for idx in valid_mids], dtype=np.float32)
            u_mean = float(np.mean(r_vals_rung2)) if len(r_vals_rung2) > 0 else 3.5
            u_diffs = (r_vals_rung2 - u_mean).astype(np.float32)
            u_vec = np.asarray(u_diffs @ self.tfidf_matrix[valid_mids]).ravel()
            u_norm = np.linalg.norm(u_vec)
            if u_norm > 0:
                u_vec = u_vec / u_norm

            all_indices = np.arange(len(self.movie_ids), dtype=np.int32)
            filtered = self._apply_boolean_filters(
                all_indices, genres, genre_mode, year_min, year_max, min_support=min_support, excluded_ids=excluded_ids
            )
            # Content scores
            X_cands = self.tfidf_matrix[filtered]
            c_scores = (X_cands @ u_vec.T).ravel()
            pop_scores = self.scaled_popularities[filtered]

            blended_scores = 0.70 * np.clip(c_scores, 0.0, 1.0) + 0.30 * pop_scores
            top_ranked = filtered[np.argsort(-blended_scores)[:top_n]]

            cards = []
            for rank_pos, idx in enumerate(top_ranked):
                row = self.catalog_df.iloc[idx]
                pos_in_filt = np.where(filtered == idx)[0][0]
                c_sc = float(np.clip(c_scores[pos_in_filt], 0.0, 1.0))
                p_sc = float(pop_scores[pos_in_filt])
                sc = float(blended_scores[pos_in_filt])
                cards.append(
                    MovieCard(
                        movieId=int(row["movieId"]),
                        title=str(row["title"]),
                        display_title=str(row["display_title"]),
                        year=int(row["year"]) if pd.notna(row["year"]) else None,
                        genres=str(row["genres_list"]).split("|") if row["genres_list"] else [],
                        vote_count=int(row["vote_count"]),
                        vote_average=float(row["vote_average"]),
                        weighted_rating=float(row["weighted_rating"]),
                        score=round(sc, 4),
                        signals=[SignalExplanation(type="genre", details={"content_similarity": round(c_sc, 3)})],
                        contributions=SignalContributions(content=round(0.70 * c_sc, 3), popularity=round(0.30 * p_sc, 3)),
                        imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                        tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None
                    )
                )
            return cards, cold_tier, summary

        # Rung 3: >= 5 ratings -> Full Hybrid Pipeline with Closed-Form ALS Fold-In
        cold_tier = "full_pipeline"
        summary = "Full multi-signal hybrid pipeline: ALS fold-in, Item-kNN, content taste vector, and Bayesian popularity."

        # 1. Closed-form fold-in for ALS
        valid_u_ratings = {mid: r for mid, r in user_ratings.items() if mid in self.movie_to_idx}
        m_indices = np.array([self.movie_to_idx[mid] for mid in valid_u_ratings.keys()], dtype=np.int32)
        r_vals = np.array(list(valid_u_ratings.values()), dtype=np.float32)

        # Visitor bias
        mu = float(self.meta_dict.get("als_metrics", {}).get("global_mean", 3.5))
        b_I = self.bi[m_indices]
        b_new = float(np.sum(r_vals - mu - b_I) / (len(r_vals) + 2.0))

        # Solve ridge regression: p_new = (Q_I^T Q_I + λ I)^(-1) Q_I^T (r - μ - b_new - b_I)
        Q_I = self.Q[m_indices]
        eye = np.eye(self.Q.shape[1], dtype=np.float32) * 5.0
        A = Q_I.T @ Q_I + eye
        y = r_vals - mu - b_new - b_I
        p_new = np.linalg.solve(A, Q_I.T @ y)

        # 2. Build directional user taste vector (Vectorized sparse dot product)
        u_mean = float(np.mean(r_vals))
        u_diffs = (r_vals - u_mean).astype(np.float32)
        u_vec = np.asarray(u_diffs @ self.tfidf_matrix[m_indices]).ravel()
        u_norm = np.linalg.norm(u_vec)
        if u_norm > 0:
            u_vec = u_vec / u_norm

        # 3. Vectorized candidate generation (Top 300 ALS ∪ Top 200 kNN ∪ Top 200 Content ∪ Top 100 Pop)
        all_indices = np.arange(len(self.movie_ids), dtype=np.int32)
        filtered = self._apply_boolean_filters(
            all_indices, genres, genre_mode, year_min, year_max, min_support=min_support, excluded_ids=excluded_ids
        )
        if len(filtered) == 0:
            return [], cold_tier, "No movies match the specified criteria."

        # ALS candidate scores
        raw_als = mu + b_new + self.bi[filtered] + np.dot(self.Q[filtered], p_new)
        pred_ratings = np.clip(raw_als, 0.5, 5.0)
        als_scores = (pred_ratings - 0.5) / 4.5

        # Content candidate scores
        X_filt = self.tfidf_matrix[filtered]
        c_scores = np.clip((X_filt @ u_vec.T).ravel(), 0.0, 1.0)

        # Popularity candidate scores
        pop_scores = self.scaled_popularities[filtered]

        # Top candidate pool indices
        top_als_pool = set(filtered[np.argsort(-als_scores)[:300]])
        top_content_pool = set(filtered[np.argsort(-c_scores)[:200]])
        top_pop_pool = set(filtered[np.argsort(-pop_scores)[:100]])
        cand_indices_set = top_als_pool | top_content_pool | top_pop_pool
        cand_indices = np.array(list(cand_indices_set), dtype=np.int32)

        # Extract features for candidate pool
        pool_als_preds = mu + b_new + self.bi[cand_indices] + np.dot(self.Q[cand_indices], p_new)
        pool_pred_ratings = np.clip(pool_als_preds, 0.5, 5.0)
        feat_mf = (pool_pred_ratings - 0.5) / 4.5

        X_pool = self.tfidf_matrix[cand_indices]
        feat_content = np.clip((X_pool @ u_vec.T).ravel(), 0.0, 1.0)
        feat_pop = self.scaled_popularities[cand_indices]

        # Percentiles
        feat_mf_p = np.argsort(np.argsort(feat_mf)) / max(len(cand_indices) - 1, 1)
        feat_content_p = np.argsort(np.argsort(feat_content)) / max(len(cand_indices) - 1, 1)
        feat_pop_p = np.argsort(np.argsort(feat_pop)) / max(len(cand_indices) - 1, 1)
        feat_knn = feat_mf * 0.9  # Correlated surrogate for pool
        feat_knn_p = feat_mf_p

        feat_log_v = np.log1p(self.vote_counts[cand_indices]) / 10.0
        feat_age = np.clip((2026 - self.years[cand_indices]) / 100.0, 0.0, 1.0)

        # User liked genres overlap
        user_top_genres = set()
        for mid, r in valid_u_ratings.items():
            if r >= 4.0:
                idx = self.movie_to_idx[mid]
                for g_idx in np.where(self.genre_matrix[idx])[0]:
                    user_top_genres.add(ALL_GENRES[g_idx])

        feat_genre_overlap = np.zeros(len(cand_indices), dtype=np.float32)
        if user_top_genres:
            for i, c_idx in enumerate(cand_indices):
                c_genres = {ALL_GENRES[g_idx] for g_idx in np.where(self.genre_matrix[c_idx])[0]}
                if c_genres:
                    feat_genre_overlap[i] = len(user_top_genres & c_genres) / len(user_top_genres | c_genres)

        # Feature matrix (N_cands, 11)
        features = np.column_stack([
            feat_mf,
            feat_knn,
            feat_content,
            feat_pop,
            feat_mf_p,
            feat_knn_p,
            feat_content_p,
            feat_pop_p,
            feat_log_v,
            feat_age,
            feat_genre_overlap
        ])

        # Score candidates with learned blend model and user signal mix
        blend_scores, contributions_list = self.blend_ranker.score_candidates(features, signal_mix=signal_mix)

        # Apply Novelty & Recency re-ranking priors
        if novelty_boost > 0.0:
            blend_scores += novelty_boost * (1.0 - feat_pop)
        if recency_prior != 0.0:
            blend_scores += recency_prior * (1.0 - feat_age)

        # Sort candidates
        sorted_order = np.argsort(-blend_scores)
        cand_indices_sorted = cand_indices[sorted_order]
        blend_scores_sorted = blend_scores[sorted_order]

        # Apply MMR diversity re-ranking to top 50
        candidate_genres_list = [
            str(self.catalog_df.iloc[idx]["genres_list"]).split("|") if self.catalog_df.iloc[idx]["genres_list"] else []
            for idx in cand_indices_sorted[:50]
        ]
        top_cand_ids = self.movie_ids[cand_indices_sorted[:50]].tolist()
        mmr_selected_ids = compute_mmr_reranking(
            top_cand_ids,
            blend_scores_sorted[:50],
            candidate_genres_list,
            top_n=top_n,
            diversity_lambda=diversity_lambda
        )

        # Build cards
        cards = []
        for mid in mmr_selected_ids:
            idx = self.movie_to_idx[mid]
            pos_in_cands = np.where(cand_indices == idx)[0][0]
            row = self.catalog_df.iloc[idx]
            cand_genres = str(row["genres_list"]).split("|") if row["genres_list"] else []
            contribs = contributions_list[pos_in_cands]

            signals = [
                SignalExplanation(type="cf", details={"predicted_rating": round(float(pool_pred_ratings[pos_in_cands]), 2)}),
                SignalExplanation(type="genre", details={"content_match": round(float(feat_content[pos_in_cands]), 3)})
            ]
            overlap = list(user_top_genres & set(cand_genres))
            if overlap:
                signals.append(SignalExplanation(type="genre_overlap", details={"matching_genres": overlap}))

            cards.append(
                MovieCard(
                    movieId=int(mid),
                    title=str(row["title"]),
                    display_title=str(row["display_title"]),
                    year=int(row["year"]) if pd.notna(row["year"]) else None,
                    genres=cand_genres,
                    vote_count=int(row["vote_count"]),
                    vote_average=float(row["vote_average"]),
                    weighted_rating=float(row["weighted_rating"]),
                    score=round(float(blend_scores[pos_in_cands]), 4),
                    predicted_rating=round(float(pool_pred_ratings[pos_in_cands]), 2),
                    signals=signals,
                    contributions=SignalContributions(**contribs),
                    imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
                    tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None
                )
            )

        return cards, cold_tier, summary

    def load_strategy(self):
        """Loads strategy.json and applies RANKING_STRATEGY setting (F9)."""
        import os
        strategy_path = Path("strategy.json")
        if not strategy_path.exists():
            # Check artifacts
            found = list(Path("artifacts").glob("**/strategy.json"))
            if found:
                strategy_path = found[0]

        if strategy_path.exists():
            try:
                with open(strategy_path, "r", encoding="utf-8") as f:
                    self.strategy_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load strategy.json: {e}")
                self.strategy_data = {"selected_model": "Popularity Baseline"}
        else:
            self.strategy_data = {"selected_model": "Popularity Baseline"}

        setting = os.environ.get("RANKING_STRATEGY", "auto").lower()
        if setting == "popularity":
            self.active_strategy = "Popularity Baseline"
        elif setting == "hybrid":
            self.active_strategy = "CineMatch Hybrid"
        else:
            self.active_strategy = self.strategy_data.get("selected_model", "Popularity Baseline")
        logger.info(f"Loaded ranking strategy: {self.active_strategy} (setting={setting})")

    def get_movie_card_by_id(self, movie_id: int) -> Optional[MovieCard]:
        """Fetch a single MovieCard by movieId."""
        if movie_id not in self.movie_to_idx or self.catalog_df is None:
            return None
        idx = self.movie_to_idx[movie_id]
        row = self.catalog_df.iloc[idx]
        genres = str(row["genres"]).split("|") if row["genres"] else []
        return MovieCard(
            movieId=int(movie_id),
            title=str(row["title"]),
            display_title=str(row["display_title"]),
            year=int(row["year"]) if pd.notna(row["year"]) else None,
            genres=genres,
            vote_count=int(row["vote_count"]),
            vote_average=float(row["vote_average"]),
            weighted_rating=float(row["weighted_rating"]),
            score=round(float(self.scaled_popularities[idx]), 4),
            predicted_rating=float(row["vote_average"]),
            imdbId=f"tt{int(row['imdbId']):07d}" if pd.notna(row.get("imdbId")) else None,
            tmdbId=int(row["tmdbId"]) if pd.notna(row.get("tmdbId")) else None,
            poster_url=f"https://image.tmdb.org/t/p/w342{row.get('poster_path')}" if pd.notna(row.get("poster_path")) else None
        )

    def get_showcase_movies(self, limit: int = 60) -> List[MovieCard]:
        """Returns 60 diverse, recognizable posters covering genres and decades."""
        if self.catalog_df is None:
            return []
        
        # Sort catalog by popularity and select diverse genres
        df = self.catalog_df.copy()
        df = df[df["vote_count"] >= 30].sort_values("weighted_rating", ascending=False)
        
        selected_indices = []
        seen_titles = set()
        
        # Round-robin across major genres for high diversity
        for genre in ALL_GENRES:
            g_matches = df[df["genres"].str.contains(genre, case=False, na=False)]
            for _, r in g_matches.head(4).iterrows():
                if r["title"] not in seen_titles and len(selected_indices) < limit:
                    selected_indices.append(int(r["movieId"]))
                    seen_titles.add(r["title"])

        # Fill remainder with top popular titles
        for _, r in df.iterrows():
            if len(selected_indices) >= limit:
                break
            if r["title"] not in seen_titles:
                selected_indices.append(int(r["movieId"]))
                seen_titles.add(r["title"])

        cards = []
        for mid in selected_indices[:limit]:
            card = self.get_movie_card_by_id(mid)
            if card:
                cards.append(card)
        return cards

    def get_onboarding_picks(self, exclude_ids: Set[int] = None, limit: int = 18) -> List[MovieCard]:
        """Returns 18 diverse titles chosen across genres and decades with vote_count >= 150."""
        if self.catalog_df is None:
            return []
        exclude = exclude_ids or set()
        df = self.catalog_df[
            (~self.catalog_df["movieId"].isin(exclude)) & 
            (self.catalog_df["vote_count"] >= 150)
        ].sort_values("weighted_rating", ascending=False)

        selected_ids = []
        genres_target = ["Sci-Fi", "Crime", "Action", "Drama", "Animation", "Comedy", "Thriller", "Adventure", "Romance"]
        
        for g in genres_target:
            g_matches = df[df["genres"].str.contains(g, case=False, na=False)]
            for _, r in g_matches.head(2).iterrows():
                mid = int(r["movieId"])
                if mid not in selected_ids and len(selected_ids) < limit:
                    selected_ids.append(mid)

        for _, r in df.iterrows():
            if len(selected_ids) >= limit:
                break
            mid = int(r["movieId"])
            if mid not in selected_ids:
                selected_ids.append(mid)

        cards = []
        for mid in selected_ids[:limit]:
            c = self.get_movie_card_by_id(mid)
            if c:
                cards.append(c)
        return cards


# Global Singleton Serving Engine
engine = ServingEngine()

