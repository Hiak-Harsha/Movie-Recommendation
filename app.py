"""
CineMatch — Hybrid Movie Recommendation Workspace (Studio Layout)
ArtCraft-inspired workflow-first recommendation tool powered by MovieLens.
"""
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit as st
import pandas as pd
import numpy as np

import config
from src.data_loader import load_raw_data, validate_and_clean_data, compute_dataset_fingerprint
from src.preprocessing import build_movie_catalog, compute_popularity_metrics
from src.content_model import ContentRecommender
from src.collaborative_model import CollaborativeEngine
from src.hybrid_model import HybridRecommender
from src.styles import STUDIO_CSS, render_studio_header, render_step_bar
from src.ui_components import (
    init_session_state,
    render_movie_card,
    render_ticker_strip,
    safe_text
)

# Page Setup
st.set_page_config(
    page_title="CineMatch — Hybrid Movie Recommendation Workspace",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject Studio Theme CSS
st.markdown(STUDIO_CSS, unsafe_allow_html=True)

# Initialize Session State
init_session_state()


@st.cache_resource(show_spinner="Initializing CineMatch Studio Workspace...")
def initialize_system(data_fingerprint: str):
    """Loads dataset and fits core recommendation pipelines keyed by dataset fingerprint."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    movies_clean, ratings_clean, tags_clean, links_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )

    # Popularity metrics strictly from observed ratings
    pop_df, global_mean, m_threshold = compute_popularity_metrics(ratings_clean)
    catalog = build_movie_catalog(movies_clean, tags_clean, pop_df, links_clean)

    # Train production models
    content_model = ContentRecommender().fit(catalog)
    collab_engine = CollaborativeEngine().fit(ratings_clean)
    hybrid_model = HybridRecommender(content_model, collab_engine, catalog)

    return {
        "catalog": catalog,
        "content_model": content_model,
        "collab_engine": collab_engine,
        "hybrid_model": hybrid_model,
        "ratings_clean": ratings_clean,
        "health_report": report,
        "global_mean": global_mean,
        "m_threshold": m_threshold,
    }


# Check data directory and compute fingerprint
try:
    data_dir = config.DATA_CANDIDATE_PATHS[0] if config.DATA_CANDIDATE_PATHS[0].exists() else config.PROJECT_ROOT / "data"
    curr_fingerprint = compute_dataset_fingerprint(data_dir) if data_dir.exists() else "unknown"
    system_data = initialize_system(curr_fingerprint)
    catalog = system_data["catalog"]
    content_model = system_data["content_model"]
    collab_engine = system_data["collab_engine"]
    hybrid_model = system_data["hybrid_model"]
    health_report = system_data["health_report"]
except Exception as e:
    st.error(f"Failed to initialize CineMatch workspace: {str(e)}")
    st.info("Please verify your MovieLens CSV files exist in the data/ folder.")
    st.stop()


# -------------------------------------------------------------
# LEFT RAIL NAVIGATION
# -------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="eyebrow" style="color:#e5a93c;">Studio Workspace</div>', unsafe_allow_html=True)
    st.markdown('<h2 style="color: #ffffff; margin-top: 0; font-weight: 800;">🎬 CineMatch</h2>', unsafe_allow_html=True)
    st.caption("Workflow-Driven Movie Discovery")
    st.markdown("---")

    nav_pages = ["Discover", "Similar Movies", "For You", f"Watchlist ({len(st.session_state.watchlist)})", "Model Insights"]
    active_idx = 0
    for idx, name in enumerate(["Discover", "Similar Movies", "For You", "Watchlist", "Model Insights"]):
        if name in st.session_state.current_page:
            active_idx = idx
            break

    selected_page_item = st.radio(
        "Workspace Rail",
        nav_pages,
        index=active_idx,
        label_visibility="collapsed"
    )

    for clean_name in ["Discover", "Similar Movies", "For You", "Watchlist", "Model Insights"]:
        if clean_name in selected_page_item:
            st.session_state.current_page = clean_name
            break

    st.markdown("---")
    st.markdown('<div class="eyebrow">Session Status</div>', unsafe_allow_html=True)
    st.write(f"• **Rated Movies:** {len(st.session_state.user_ratings)}")
    st.write(f"• **Saved Watchlist:** {len(st.session_state.watchlist)}")
    if st.session_state.demo_profile_id:
        st.write(f"• **Demo Profile:** #{st.session_state.demo_profile_id}")

    if st.session_state.user_ratings or st.session_state.watchlist:
        if st.button("Reset Session State", use_container_width=True):
            st.session_state.user_ratings = {}
            st.session_state.watchlist = {}
            st.session_state.demo_profile_id = None
            st.rerun()

    st.markdown("---")
    st.caption(f"Fingerprint: `{curr_fingerprint}` | 100% Local data.")


current_page = st.session_state.current_page


# =============================================================
# PAGE 1: DISCOVER
# =============================================================
if current_page == "Discover":
    st.markdown(render_studio_header(
        "01 / Studio Overview",
        "Find what to watch next.",
        "A process-first cinema exploration canvas. Choose a task, configure signals, and inspect real data evidence."
    ), unsafe_allow_html=True)

    # Real computed ticker strip from Bayesian top-rated movies
    spotlight_movies = catalog[catalog["rating_count"] >= 30].sort_values(by="weighted_rating", ascending=False).head(8)
    spotlight_dicts = [content_model.get_movie_details(int(row["movieId"])) for _, row in spotlight_movies.iterrows()]
    st.markdown(render_ticker_strip(spotlight_dicts), unsafe_allow_html=True)

    # Studio 3:1 Layout: Canvas (Col 1) and Inspector (Col 2)
    col_canvas, col_inspector = st.columns([3, 1])

    with col_canvas:
        st.markdown("### Prominent Movie Search")
        search_query = st.text_input(
            "Search MovieLens Catalog",
            placeholder="Type 'the matrix', 'toy story', 'clockwork orange'...",
            label_visibility="collapsed"
        )

        if search_query:
            results = content_model.search_movies(search_query, limit=6)
            if not results.empty:
                st.caption(f"Found {len(results)} match(es) for '{safe_text(search_query)}'")
                for _, row in results.iterrows():
                    m_data = content_model.get_movie_details(int(row["movieId"]))
                    render_movie_card(m_data, card_type="popular", key_suffix=f"disc_{row['movieId']}", page_context="discover")
            else:
                st.info(f"No titles found matching '{safe_text(search_query)}'.")

        st.markdown("---")
        st.markdown("### Highest-Rated Community Baseline")
        st.caption(f"Bayesian smoothed weighted ratings (prior threshold m={system_data['m_threshold']:.1f}). Computed from verified training data.")

        top_catalog = catalog[catalog["rating_count"] >= 25].sort_values(by="weighted_rating", ascending=False).head(6)
        for _, row in top_catalog.iterrows():
            m_data = content_model.get_movie_details(int(row["movieId"]))
            m_data["reasons"] = [
                f"Bayesian rating {m_data['weighted_rating']}★ based on {m_data['rating_count']:,} reviews",
                f"Genres: {m_data['genres_display']}"
            ]
            render_movie_card(m_data, card_type="popular", key_suffix=f"pop_{row['movieId']}", page_context="discover")

    with col_inspector:
        st.markdown('<div class="inspector-card">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Task Selector</div>', unsafe_allow_html=True)
        st.markdown("#### Explore Workflows")
        
        if st.button("Similar Movies →", use_container_width=True):
            st.session_state.current_page = "Similar Movies"
            st.rerun()
            
        if st.button("Personalized For You →", use_container_width=True):
            st.session_state.current_page = "For You"
            st.rerun()

        if st.button("Inspect Model Audit →", use_container_width=True):
            st.session_state.current_page = "Model Insights"
            st.rerun()

        st.markdown("---")
        st.markdown('<div class="eyebrow">Quick Onboarding</div>', unsafe_allow_html=True)
        st.caption("Rate an iconic title to begin your profile:")
        onboard_picks = [260, 2571, 1, 296]  # Star Wars, The Matrix, Toy Story, Pulp Fiction
        for pid in onboard_picks:
            p_details = content_model.get_movie_details(pid)
            if p_details:
                rated_val = st.session_state.user_ratings.get(pid, 0.0)
                btn_txt = f"★ {rated_val} {p_details['display_title']}" if rated_val > 0 else f"+ Rate {p_details['display_title']}"
                if st.button(btn_txt, key=f"onb_{pid}", use_container_width=True):
                    st.session_state.user_ratings[pid] = 5.0
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# =============================================================
# PAGE 2: SIMILAR MOVIES
# =============================================================
elif current_page == "Similar Movies":
    st.markdown(render_studio_header(
        "02 / Content Discovery",
        "Similar Movies Studio",
        "Sparse cosine similarity across multi-block TF-IDF genre tokens, decade tags, and atomic user tags."
    ), unsafe_allow_html=True)

    st.markdown(render_step_bar("Choose Seed Film", "Tune Filters & Scope", "Review Similar Titles", active_step=2), unsafe_allow_html=True)

    col_canvas, col_inspector = st.columns([3, 1])

    with col_inspector:
        st.markdown('<div class="inspector-card">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Controls & Filters</div>', unsafe_allow_html=True)
        
        sim_top_n = st.slider("Result Count:", min_value=3, max_value=24, value=6, step=3)
        sim_genre_filter = st.multiselect("Genre Constraints:", options=config.SUPPORTED_GENRES)
        
        use_year_filter = st.checkbox("Release Year Filter", value=False)
        sim_year_range = None
        if use_year_filter:
            sim_year_range = st.slider("Year Bounds:", min_value=1930, max_value=2018, value=(1980, 2018))

        st.markdown('</div>', unsafe_allow_html=True)

    with col_canvas:
        # Search & Select Seed Film
        c_search, c_dropdown = st.columns([1, 1])
        with c_search:
            sim_search = st.text_input("Search Seed Movie:", placeholder="Type movie title (e.g. Inception, Matrix, Alien)...")
        
        matches = content_model.search_movies(sim_search if sim_search else "The Matrix", limit=12)
        match_options = {int(row["movieId"]): f"{row['display_title']} ({row.get('release_year', '—')})" for _, row in matches.iterrows()}

        current_seed = st.session_state.selected_seed_id
        if current_seed not in match_options and match_options:
            current_seed = list(match_options.keys())[0]

        with c_dropdown:
            seed_choice = st.selectbox(
                "Active Seed Film:",
                options=list(match_options.keys()),
                format_func=lambda m: match_options.get(m, f"Movie #{m}"),
                index=list(match_options.keys()).index(current_seed) if current_seed in match_options else 0
            )
            st.session_state.selected_seed_id = seed_choice

        # Seed Summary Card
        seed_data = content_model.get_movie_details(seed_choice)
        if seed_data:
            with st.container(border=True):
                s1, s2 = st.columns([3, 1])
                with s1:
                    st.markdown(f'<div class="eyebrow">Active Seed Film</div>', unsafe_allow_html=True)
                    st.markdown(f"### {safe_text(seed_data['display_title'])}")
                    st.caption(f"**Genres:** {seed_data['genres_display']} &nbsp;|&nbsp; **Community Rating:** {seed_data['mean_rating']}★ ({seed_data['rating_count']} reviews)")
                    if seed_data["tags"]:
                        tag_badges = "".join([f"<span class='badge-genre'>{safe_text(t.replace('_', ' '))}</span>" for t in seed_data["tags"][:6]])
                        st.markdown(f"**Tags:** {tag_badges}", unsafe_allow_html=True)
                with s2:
                    if seed_data.get("imdbId"):
                        imdb_url = f"https://www.imdb.com/title/tt{int(seed_data['imdbId']):07d}/"
                        st.markdown(f"<div style='text-align:right;'><a href='{imdb_url}' target='_blank' class='imdb-link'>Open on IMDb ↗</a></div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("### Ranked Similar Films")
        st.caption(f"Excludes seed title '{safe_text(seed_data['display_title'])}'. Sorted by cosine similarity of multi-block TF-IDF features.")

        similar_recs = content_model.get_similar_movies(
            movie_id=seed_choice,
            top_n=sim_top_n,
            genre_filter=sim_genre_filter if sim_genre_filter else None,
            year_range=sim_year_range
        )

        if similar_recs:
            for rec in similar_recs:
                render_movie_card(rec, card_type="similar", key_suffix=f"sim_page_{rec['movieId']}", page_context="similar")
        else:
            st.warning("No movies matched your genre or release year filters. Loosen your constraints to view more matches.")


# =============================================================
# PAGE 3: FOR YOU (PERSONALIZED HYBRID WORKSPACE)
# =============================================================
elif current_page == "For You":
    st.markdown(render_studio_header(
        "03 / Personalized Studio",
        "For You Recommendation Canvas",
        "Combines your personal rating history, user taste vectors, Item-kNN neighbor similarities, and Bayesian priors."
    ), unsafe_allow_html=True)

    st.markdown(render_step_bar("Build Taste Profile", "Configure Signal Mix", "Review Ranked Picks", active_step=2), unsafe_allow_html=True)

    col_canvas, col_inspector = st.columns([3, 1])

    with col_inspector:
        st.markdown('<div class="inspector-card">', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">Inspector & Signal Mix</div>', unsafe_allow_html=True)

        fy_top_n = st.slider("Result Count:", min_value=3, max_value=24, value=6, step=3, key="fy_n")
        fy_genres = st.multiselect("Genre Filter:", options=config.SUPPORTED_GENRES, key="fy_g")
        fy_match_mode = st.radio("Genre Match Mode:", ["OR (Match Any)", "AND (Match All)"], index=0)
        clean_mode = "AND" if "AND" in fy_match_mode else "OR"

        fy_use_year = st.checkbox("Year Bounds", value=False, key="fy_y_chk")
        fy_years = None
        if fy_use_year:
            fy_years = st.slider("Year Range:", min_value=1930, max_value=2018, value=(1980, 2018), key="fy_y_sld")

        st.markdown("---")
        st.markdown('<div class="eyebrow">Signal Mix (Tuning)</div>', unsafe_allow_html=True)
        w_c = st.slider("Content Weight:", 0.0, 1.0, config.DEFAULT_HYBRID_WEIGHTS["content"], 0.05)
        w_cf = st.slider("Collaborative Weight:", 0.0, 1.0, config.DEFAULT_HYBRID_WEIGHTS["collaborative"], 0.05)
        w_p = st.slider("Popularity Weight:", 0.0, 1.0, config.DEFAULT_HYBRID_WEIGHTS["popularity"], 0.05)
        active_weights = {"content": w_c, "collaborative": w_cf, "popularity": w_p}

        st.markdown('</div>', unsafe_allow_html=True)

    with col_canvas:
        # Profile Configuration Tabs
        tab_custom, tab_demo = st.tabs(["⭐ Custom Visitor Profile", "👤 MovieLens Benchmark Profiles"])

        with tab_custom:
            st.markdown("#### Search & Rate Movies to Build Your Profile")
            st.caption("Rate at least 5 movies for personalized Collaborative Filtering. (Fewer ratings trigger the Content + Popularity fallback).")

            rate_query = st.text_input("Search movie you've watched:", placeholder="e.g. Inception, Gladiator, Star Wars...")
            if rate_query:
                r_matches = content_model.search_movies(rate_query, limit=5)
                if not r_matches.empty:
                    for _, r_row in r_matches.iterrows():
                        r_mid = int(r_row["movieId"])
                        r_title = r_row["display_title"]
                        curr_star = st.session_state.user_ratings.get(r_mid, 4.0)

                        c1, c2, c3 = st.columns([3, 2, 1])
                        with c1:
                            st.write(f"**{r_title}** ({r_row.get('release_year', '—')})")
                        with c2:
                            new_star = st.select_slider(
                                f"Stars for {r_mid}",
                                options=[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                                value=curr_star,
                                key=f"slide_rate_{r_mid}",
                                label_visibility="collapsed"
                            )
                        with c3:
                            is_r = r_mid in st.session_state.user_ratings
                            btn_lbl = "Update" if is_r else "+ Rate"
                            if st.button(btn_lbl, key=f"btn_r_{r_mid}"):
                                st.session_state.user_ratings[r_mid] = float(new_star)
                                st.session_state.demo_profile_id = None
                                st.rerun()
                else:
                    st.info("No matching titles.")

        with tab_demo:
            st.markdown("#### Test with Real MovieLens Benchmark Profiles")
            st.caption("Copies actual historical MovieLens test profiles into your active session. Clearly labeled as sample dataset profiles.")

            demo_options = {
                15: "User #15 — Sci-Fi & Action enthusiast (135 dataset reviews)",
                414: "User #414 — Comprehensive Classic & Drama buff (2,698 reviews)",
                599: "User #599 — Animation & Comedy lover (2,478 reviews)",
                606: "User #606 — International & Independent cinema buff (1,115 reviews)",
            }

            demo_choice = st.selectbox(
                "Select Sample Dataset User:",
                options=list(demo_options.keys()),
                format_func=lambda u: demo_options[u]
            )

            if st.button(f"Load Sample Profile #{demo_choice}", use_container_width=True):
                demo_ratings = collab_engine.get_existing_user_ratings(demo_choice)
                st.session_state.user_ratings = demo_ratings
                st.session_state.demo_profile_id = demo_choice
                st.success(f"Copied {len(demo_ratings)} ratings from MovieLens User #{demo_choice} into your profile view.")
                st.rerun()

        # Active Rating Inspection Section
        active_ratings = st.session_state.user_ratings
        if active_ratings:
            st.markdown(f"**Active Profile:** {len(active_ratings)} rated title(s).")
            with st.expander("Inspect or remove your active ratings", expanded=False):
                for mid, r in list(active_ratings.items())[:15]:
                    d = content_model.get_movie_details(mid)
                    title = d["display_title"] if d else f"Movie #{mid}"
                    c_t, c_s, c_del = st.columns([3, 1, 1])
                    with c_t:
                        st.write(f"• {title}")
                    with c_s:
                        st.write(f"★ {r}")
                    with c_del:
                        if st.button("Remove", key=f"del_user_r_{mid}"):
                            del st.session_state.user_ratings[mid]
                            st.rerun()
                if len(active_ratings) > 15:
                    st.caption(f"Showing first 15 of {len(active_ratings)} ratings.")
        else:
            st.info("Your rating profile is currently empty. Rate movies above or select a sample benchmark profile to begin.")

        st.markdown("---")
        # Run Recommendation
        recs, meta = hybrid_model.recommend_for_user(
            user_ratings=active_ratings,
            preferred_genres=fy_genres if fy_genres else None,
            genre_match_mode=clean_mode,
            year_range=fy_years,
            weights=active_weights,
            top_n=fy_top_n
        )

        st.markdown(f"### Personalized Recommendations")
        st.caption(f"Evidence Level: **{meta['evidence_level']}** | Evaluated {meta['total_candidates_evaluated']:,} candidate films.")

        if meta["is_fallback"]:
            st.warning(f"ℹ️ **Honest Fallback Active:** {meta['fallback_reason']}")
        else:
            st.success(f"✓ **Full Multi-Signal Pipeline Active:** Combined Content taste vector, Collaborative fold-in predictions, and Bayesian prior.")

        with st.expander("Why am I seeing these? (Signal & Filter Breakdown)", expanded=False):
            st.write(f"• **Active Weights:** Content: {meta['active_weights']['content']:.2f} | Collaborative: {meta['active_weights']['collaborative']:.2f} | Popularity: {meta['active_weights']['popularity']:.2f}")
            st.write(f"• **Active User Ratings:** {meta['user_ratings_count']} titles in profile history.")
            st.write(f"• **Collaborative Predictions:** {meta['cf_predictions_count']} candidate scores computed via fold-in.")

        if recs:
            for rec in recs:
                render_movie_card(rec, card_type="hybrid", key_suffix=f"fy_card_{rec['movieId']}", page_context="for_you")
        else:
            st.warning("No recommendations met your genre or year criteria. Loosen your filters to view more candidates.")


# =============================================================
# PAGE 4: WATCHLIST
# =============================================================
elif current_page == "Watchlist":
    st.markdown(render_studio_header(
        "04 / Discovery Queue",
        "Your Watchlist",
        "Session-only discovery list. Titles are stored in local session memory and reset when you close the tab."
    ), unsafe_allow_html=True)

    watchlist_dict = st.session_state.watchlist

    if watchlist_dict:
        w1, w2, w3 = st.columns([1, 1, 2])
        with w1:
            st.metric("Saved Movies", len(watchlist_dict))
        with w2:
            ratings_list = [m.get("mean_rating", 0) for m in watchlist_dict.values() if m.get("mean_rating", 0) > 0]
            avg_r = np.mean(ratings_list) if ratings_list else 0.0
            st.metric("Avg Community Rating", f"{avg_r:.2f}★" if avg_r > 0 else "N/A")
        with w3:
            # CSV Download
            rows = []
            for mid, mdata in watchlist_dict.items():
                rows.append({
                    "movieId": mid,
                    "title": mdata.get("display_title", mdata.get("title", "")),
                    "year": mdata.get("release_year", ""),
                    "genres": mdata.get("genres_display", "")
                })
            df_export = pd.DataFrame(rows)
            csv_data = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Export Watchlist to CSV",
                data=csv_data,
                file_name="cinematch_watchlist.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")
        for mid, mdata in list(watchlist_dict.items()):
            render_movie_card(mdata, card_type="watchlist", key_suffix=f"wl_list_{mid}", page_context="watchlist")
    else:
        st.markdown(
            """
            <div class="inspector-card" style="text-align: center; padding: 3rem 1.5rem;">
                <h3 style="color: #8b949e; margin-bottom: 0.5rem;">Your Watchlist is Empty</h3>
                <p style="color: #6e7681; max-width: 500px; margin: 0 auto 1.5rem auto;">
                    Save titles you want to watch by clicking the <strong>+ Watchlist</strong> button on any movie card.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# =============================================================
# PAGE 5: MODEL INSIGHTS & FACTUAL AUDIT
# =============================================================
elif current_page == "Model Insights":
    st.markdown(render_studio_header(
        "05 / Factual Audit",
        "Model Diagnostics & Offline Evaluation",
        "Every metric, dataset count, and evaluation statistic is derived from computation on real data. No placeholder metrics."
    ), unsafe_allow_html=True)

    # 1. Dataset Health
    st.markdown("### 1. Dataset Scale & Health Verification")
    h1, h2, h3, h4 = st.columns(4)
    with h1:
        st.metric("Valid Movies", f"{health_report.clean_movie_count:,}")
    with h2:
        st.metric("Clean Ratings", f"{health_report.clean_rating_count:,}")
    with h3:
        st.metric("Historical Users", f"{health_report.clean_user_count:,}")
    with h4:
        st.metric("Matrix Sparsity", f"{health_report.sparsity_percentage}%")

    with st.expander("Detailed DataHealthReport (JSON Audit)", expanded=False):
        st.json(health_report.to_dict())

    st.markdown("---")

    # 2. Evaluation Results from artifacts/eval_results.json
    st.markdown("### 2. Leakage-Free Offline Evaluation Results")
    st.caption("Computed from a strict global temporal split (70% Train / 10% Validation / 20% Test).")

    eval_file = config.ARTIFACTS_DIR / "eval_results.json"
    if eval_file.exists():
        with open(eval_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

        # Quality Gate Outcome Box
        q_gate = eval_data.get("quality_gate", {})
        if q_gate.get("passed", False):
            st.success(f"✓ **{q_gate.get('selected_model', 'Hybrid')}**: {q_gate.get('summary', '')}")
        else:
            st.info(f"ℹ️ **Quality Gate Decision**: {q_gate.get('summary', '')}")

        # Metrics Table with 95% Bootstrap CIs
        st.markdown("#### Test Ranking Metrics @ 10 (with 95% Bootstrap CIs)")
        table_rows = []
        for mname, mobj in eval_data.get("test_metrics", {}).items():
            ndcg_m = mobj["ndcg"]["mean"]
            ndcg_ci = f"[{mobj['ndcg']['ci_lower']:.3f}, {mobj['ndcg']['ci_upper']:.3f}]"
            prec_m = mobj["precision"]["mean"]
            rec_m = mobj["recall"]["mean"]
            map_m = mobj["map"]["mean"]
            cov_pct = f"{mobj['catalog_coverage'] * 100:.1f}%"

            table_rows.append({
                "Model Pipeline": mname,
                "NDCG@10 (95% CI)": f"{ndcg_m:.3f} {ndcg_ci}",
                "Precision@10": f"{prec_m:.3f}",
                "Recall@10": f"{rec_m:.3f}",
                "MAP@10": f"{map_m:.3f}",
                "Catalog Coverage": cov_pct
            })
        st.table(pd.DataFrame(table_rows))

        # Rating Prediction Metrics
        r_metrics = eval_data.get("rating_prediction_metrics", {})
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.metric("Test Rating RMSE", f"{r_metrics.get('test_rmse', 'N/A')}")
        with rc2:
            st.metric("Test Rating MAE", f"{r_metrics.get('test_mae', 'N/A')}")
        with rc3:
            st.metric("Evaluated Test Pairs", f"{r_metrics.get('evaluated_pairs', 0):,}")

    else:
        st.warning(
            "Evaluation results file (`artifacts/eval_results.json`) not yet computed. "
            "Run from terminal: `python -m src.evaluation --protocol temporal --seed 42`"
        )

    st.markdown("---")
    st.markdown("### 3. Documented Limitations & Edge-Case Rules")
    st.markdown(
        """
        - **Source Metadata Bounds:** MovieLens `ml-latest-small` contains titles, release years, genres, and user tags. It does **not** contain director names, cast lists, or plot synopses. CineMatch strictly bases content features on genres and community tags, avoiding fabricated plot narratives.
        - **Cold-Start Handling:** Visitors with $< 5$ ratings cannot reliably activate collaborative filtering; weights are transparently redistributed to Content and Bayesian Popularity baselines.
        - **Session Scope:** Watchlists and user ratings are maintained in memory within the current Streamlit browser session.
        """
    )
