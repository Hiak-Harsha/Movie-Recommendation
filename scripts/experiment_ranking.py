"""
Ranking Experiments & Ablation Script (Phase P2)
Tests:
  1. Sanity test: Blend with pure popularity == Popularity Baseline
  2. Candidate recall ceiling
  3. Implicit feedback / Co-occurrence
  4. Popular-in-Taste (genre/decade affinity weighted popularity)
  5. Multi-signal Hybrid
  6. Global temporal robustness cross-check
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
from typing import Dict, List, Set
import numpy as np
import pandas as pd
from collections import defaultdict

from ml.data_loader import resolve_data_directory, load_raw_data, validate_and_clean_data
from ml.preprocessing import normalize_genres, parse_display_title, compute_popularity_metrics
from ml.als import ExplicitALS
from ml.knn import ItemKNN
from ml.content import ContentEngine
from ml.evaluation import build_per_user_temporal_split, calculate_user_ranking_metrics, compute_bootstrap_ci

def run_experiments():
    t0 = time.time()
    data_path = resolve_data_directory(None)
    movies, ratings, tags, links = load_raw_data(data_path)
    clean_movies, clean_ratings, clean_tags, clean_links, _ = validate_and_clean_data(movies, ratings, tags, links, data_path)

    catalog_genre_dict = {
        int(row["movieId"]): set(normalize_genres(str(row["genres"])))
        for _, row in clean_movies.iterrows()
    }
    all_mids = clean_movies["movieId"].tolist()

    # Split: 70/10/20 per-user temporal
    train_df, val_df, test_df = build_per_user_temporal_split(clean_ratings)

    # Catalog & Popularity
    catalog_df = clean_movies.copy()
    catalog_df["year"] = [parse_display_title(t)[1] for t in catalog_df["title"]]
    pop_res = compute_popularity_metrics(train_df)
    pop_stats = pop_res["movie_stats"].set_index("movieId")
    pop_ranked_ids = pop_stats.sort_values("weighted_rating", ascending=False).index.tolist()

    # Probabilities for novelty metric
    vote_counts = train_df.groupby("movieId").size()
    total_votes = len(train_df)
    item_pop_probs = {mid: count / total_votes for mid, count in vote_counts.items()}

    # Train ALS, KNN, Content
    print("Fitting models on train_df...")
    als = ExplicitALS(factors=20, reg_f=5.0, reg_b=2.0, iterations=8, random_seed=42)
    als.fit(train_df, val_df, all_movie_ids=all_mids)

    knn = ItemKNN(k=50, shrinkage_lambda=5.0)
    knn.fit(train_df, all_movie_ids=all_mids)

    max_train_ts = train_df["timestamp"].max()
    train_tags = clean_tags[clean_tags["timestamp"] <= max_train_ts] if "timestamp" in clean_tags.columns else clean_tags
    content = ContentEngine(genre_weight=0.60, tag_weight=0.40, top_k=50)
    content.fit(catalog_df, train_tags)

    # Build Implicit Co-occurrence Matrix from train_df
    print("Building implicit item co-occurrence...")
    user_movie_sets = train_df.groupby("userId")["movieId"].apply(set).to_dict()
    item_users = defaultdict(set)
    for u, m_set in user_movie_sets.items():
        for m in m_set:
            item_users[m].add(u)
    item_counts = {m: len(u_set) for m, u_set in item_users.items()}

    # Ground truth sets
    val_positives = val_df[val_df["rating"] >= 4.0]
    val_gt = val_positives.groupby("userId")["movieId"].apply(set).to_dict()
    val_users = [u for u in val_gt.keys() if u in als.user_to_idx]

    test_positives = test_df[test_df["rating"] >= 4.0]
    test_gt = test_positives.groupby("userId")["movieId"].apply(set).to_dict()
    test_users = [u for u in test_gt.keys() if u in als.user_to_idx]

    print(f"Eligible Val Users: {len(val_users)}, Eligible Test Users: {len(test_users)}")

    # Candidate Recall Ceiling Measurement:
    # How many test positives appear in top-K candidate pools?
    recall_hits = 0
    total_pos = sum(len(test_gt[u]) for u in test_users)
    for u in test_users:
        u_train = train_df[train_df["userId"] == u]
        rated = set(u_train["movieId"])
        # Top 500 popular + Top 100 ALS
        pool = set([m for m in pop_ranked_ids if m not in rated][:500])
        recall_hits += len(test_gt[u] & pool)
    print(f"Candidate Recall Ceiling (Top-500 pool): {recall_hits / total_pos:.4f} ({recall_hits}/{total_pos})")

    # Strategy Evaluation Functions
    def evaluate_strategy(name, strategy_fn, target_users, target_gt, is_val=False):
        ndcg_list = []
        coverage_set = set()
        for uid in target_users:
            gt_set = target_gt[uid]
            train_u = train_df[train_df["userId"] == uid]
            rated_ids = set(train_u["movieId"])
            if not is_val:
                val_u = val_df[val_df["userId"] == uid]
                rated_ids.update(val_u["movieId"])

            user_ratings = dict(zip(train_u["movieId"].astype(int), train_u["rating"].astype(float)))
            recs = strategy_fn(uid, user_ratings, rated_ids)[:10]
            coverage_set.update(recs)
            m = calculate_user_ranking_metrics(recs, gt_set, catalog_genre_dict, item_pop_probs, k=10)
            ndcg_list.append(m["ndcg"])

        return {
            "mean_ndcg": np.mean(ndcg_list),
            "coverage": len(coverage_set) / len(all_mids),
            "ndcg_ci": compute_bootstrap_ci(ndcg_list, n_rounds=200, seed=42)
        }

    # 1. Popularity Baseline
    def strat_pop(uid, u_ratings, rated_ids):
        return [m for m in pop_ranked_ids if m not in rated_ids]

    # 2. Sanity Test: Popularity pure blend
    def strat_sanity(uid, u_ratings, rated_ids):
        unseen = [m for m in pop_ranked_ids if m not in rated_ids][:100]
        # Re-score by 1.0 * popularity
        scored = sorted(unseen, key=lambda m: float(pop_stats.loc[m]["scaled_popularity"]) if m in pop_stats.index else 0.0, reverse=True)
        return scored

    # 3. Popular in Taste
    def strat_pop_taste(uid, u_ratings, rated_ids):
        # Compute user genre weights
        user_genre_weights = defaultdict(float)
        for mid, r in u_ratings.items():
            if r >= 3.0:
                for g in catalog_genre_dict.get(mid, []):
                    user_genre_weights[g] += (r - 2.5)
        # Normalize
        total_gw = sum(user_genre_weights.values()) or 1.0
        for g in user_genre_weights:
            user_genre_weights[g] /= total_gw

        candidates = [m for m in pop_ranked_ids if m not in rated_ids][:300]
        scored = []
        for m in candidates:
            m_genres = catalog_genre_dict.get(m, set())
            genre_match = sum(user_genre_weights.get(g, 0.0) for g in m_genres)
            p_score = float(pop_stats.loc[m]["scaled_popularity"]) if m in pop_stats.index else 0.0
            # Blend popularity with user taste affinity
            score = p_score * (0.65 + 0.35 * genre_match)
            scored.append((m, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored]

    # 4. Implicit Co-occurrence (Vectorized over candidates)
    def strat_cooccur(uid, u_ratings, rated_ids):
        pool = [m for m in pop_ranked_ids if m not in rated_ids][:250]
        high_rated = [m for m, r in u_ratings.items() if r >= 3.5]
        if not high_rated:
            return pool[:10]
        
        co_scores = defaultdict(float)
        for m_src in high_rated:
            src_users = item_users.get(m_src, set())
            if not src_users:
                continue
            for m_cand in pool:
                cand_users = item_users.get(m_cand, set())
                overlap = len(src_users & cand_users)
                if overlap > 0:
                    sim = overlap / np.sqrt(len(src_users) * len(cand_users))
                    co_scores[m_cand] += sim * (u_ratings[m_src] / 5.0)

        sorted_cand = sorted(pool, key=lambda m: co_scores.get(m, 0.0), reverse=True)
        return sorted_cand

    # 5. Hybrid (Popular-in-taste + Co-occurrence + ALS)
    def strat_hybrid(uid, u_ratings, rated_ids):
        pool = [m for m in pop_ranked_ids if m not in rated_ids][:250]
        
        # User genre affinity
        user_genre_weights = defaultdict(float)
        for mid, r in u_ratings.items():
            if r >= 3.0:
                for g in catalog_genre_dict.get(mid, []):
                    user_genre_weights[g] += (r - 2.5)
        total_gw = sum(user_genre_weights.values()) or 1.0
        for g in user_genre_weights:
            user_genre_weights[g] /= total_gw

        # Co-occurrence
        co_scores = defaultdict(float)
        high_rated = [m for m, r in u_ratings.items() if r >= 3.5]
        for m_src in high_rated:
            src_users = item_users.get(m_src, set())
            if not src_users:
                continue
            for m_cand in pool:
                cand_users = item_users.get(m_cand, set())
                overlap = len(src_users & cand_users)
                if overlap > 0:
                    sim = overlap / np.sqrt(len(src_users) * len(cand_users))
                    co_scores[m_cand] += sim

        max_co = max(co_scores.values()) if co_scores else 1.0
        if max_co > 0:
            for m in co_scores:
                co_scores[m] /= max_co

        scored = []
        for m in pool:
            p_score = float(pop_stats.loc[m]["scaled_popularity"]) if m in pop_stats.index else 0.0
            m_genres = catalog_genre_dict.get(m, set())
            genre_match = sum(user_genre_weights.get(g, 0.0) for g in m_genres)
            co_score = co_scores.get(m, 0.0)
            
            # Blend: Popularity + Taste Affinity + Co-occurrence
            final_score = 0.55 * p_score + 0.30 * (p_score * genre_match) + 0.15 * co_score
            scored.append((m, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in scored]

    strategies = {
        "Popularity Baseline": strat_pop,
        "Sanity (Popularity Pure Blend)": strat_sanity,
        "Popular in Taste": strat_pop_taste,
        "Implicit Co-occurrence": strat_cooccur,
        "CineMatch Hybrid v2": strat_hybrid,
    }

    print("\n--- Validation Split Results ---")
    val_out = {}
    for s_name, s_fn in strategies.items():
        res = evaluate_strategy(s_name, s_fn, val_users, val_gt, is_val=True)
        val_out[s_name] = res
        print(f"{s_name:32} | NDCG@10: {res['mean_ndcg']:.4f} (95% CI: [{res['ndcg_ci']['ci_lower']}, {res['ndcg_ci']['ci_upper']}]) | Coverage: {res['coverage']:.4f}")

    print("\n--- Test Split Results (Strict Once) ---")
    test_out = {}
    for s_name, s_fn in strategies.items():
        res = evaluate_strategy(s_name, s_fn, test_users, test_gt, is_val=False)
        test_out[s_name] = res
        print(f"{s_name:32} | NDCG@10: {res['mean_ndcg']:.4f} (95% CI: [{res['ndcg_ci']['ci_lower']}, {res['ndcg_ci']['ci_upper']}]) | Coverage: {res['coverage']:.4f}")

    print(f"\nCompleted in {time.time() - t0:.2f} s")

if __name__ == "__main__":
    run_experiments()
