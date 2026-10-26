"""
CineMatch UI Components
Reusable components for rendering movie cards, badges, explanations,
sample profile loaders, and session state helpers.
"""
from typing import Any, Dict, List, Optional
import streamlit as st


def init_session_state():
    """Initializes default Streamlit session state keys if not already present."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Discover"
    if "watchlist" not in st.session_state:
        # dict of movieId -> movie_dict
        st.session_state.watchlist = {}
    if "user_ratings" not in st.session_state:
        # dict of movieId -> float rating
        st.session_state.user_ratings = {}
    if "selected_seed_id" not in st.session_state:
        st.session_state.selected_seed_id = 1  # Toy Story default
    if "preferred_genres" not in st.session_state:
        st.session_state.preferred_genres = []
    if "year_range" not in st.session_state:
        st.session_state.year_range = (1950, 2020)
    if "demo_profile_id" not in st.session_state:
        st.session_state.demo_profile_id = None
    if "evaluation_results" not in st.session_state:
        st.session_state.evaluation_results = None


def toggle_watchlist(movie_info: Dict[str, Any]):
    """Adds or removes a movie from the active session watchlist."""
    mid = movie_info["movieId"]
    if mid in st.session_state.watchlist:
        del st.session_state.watchlist[mid]
    else:
        st.session_state.watchlist[mid] = movie_info


def set_user_rating(movie_id: int, rating: float):
    """Sets or updates a movie rating in session state."""
    st.session_state.user_ratings[movie_id] = float(rating)


def remove_user_rating(movie_id: int):
    """Removes a movie rating from session state."""
    if movie_id in st.session_state.user_ratings:
        del st.session_state.user_ratings[movie_id]


def render_movie_card(
    movie: Dict[str, Any],
    card_type: str = "hybrid",
    key_suffix: str = "",
    show_similar_btn: bool = True
):
    """
    Renders a structured, visually polished movie card without broken images.
    
    Args:
        movie: Dictionary with movie attributes and scores
        card_type: 'similar', 'hybrid', 'popular', or 'watchlist'
        key_suffix: Unique suffix for Streamlit button widget IDs
        show_similar_btn: Whether to display the 'Find Similar' shortcut button
    """
    mid = movie["movieId"]
    title = movie.get("clean_title", movie.get("title", f"Movie #{mid}"))
    year = movie.get("release_year")
    year_str = f"({year})" if year else ""
    genres = movie.get("genres_display", "")
    
    is_in_watchlist = mid in st.session_state.watchlist

    with st.container():
        st.markdown('<div class="movie-card">', unsafe_allow_html=True)
        
        # Header Row: Title & Year
        col_title, col_score = st.columns([3, 1])
        with col_title:
            st.markdown(
                f'<div class="movie-card-title">{title} <span class="movie-year">{year_str}</span></div>',
                unsafe_allow_html=True
            )
            # Genre tags
            genres_list = movie.get("genres_list", [])
            tags_html = "".join([f'<span class="genre-tag">{g}</span>' for g in genres_list[:4]])
            st.markdown(tags_html, unsafe_allow_html=True)

        with col_score:
            if card_type == "similar" and "content_similarity" in movie:
                sim_pct = int(movie["content_similarity"] * 100)
                st.markdown(
                    f'<div style="text-align: right;"><span class="score-badge-gold">Match {sim_pct}%</span></div>',
                    unsafe_allow_html=True
                )
            elif card_type == "hybrid" and "hybrid_score" in movie:
                hyb_pct = int(movie["hybrid_score"] * 100)
                st.markdown(
                    f'<div style="text-align: right;"><span class="score-badge-gold">Score {hyb_pct}%</span></div>',
                    unsafe_allow_html=True
                )
            elif card_type == "popular" and "weighted_rating" in movie:
                w_rating = movie.get("weighted_rating", 0.0)
                st.markdown(
                    f'<div style="text-align: right;"><span class="score-badge-gold">★ {w_rating}</span></div>',
                    unsafe_allow_html=True
                )
            elif "mean_rating" in movie and movie["mean_rating"] > 0:
                st.markdown(
                    f'<div style="text-align: right;"><span class="score-badge-gold">★ {movie["mean_rating"]}</span></div>',
                    unsafe_allow_html=True
                )

        # Evidence / Explanation Row
        reasons = movie.get("reasons", [])
        if reasons:
            reasons_html = "<br>".join([f"• {r}" for r in reasons[:3]])
            st.markdown(f'<div class="evidence-box">{reasons_html}</div>', unsafe_allow_html=True)

        # Detailed score breakdown if in hybrid mode
        if card_type == "hybrid":
            c_score = int(movie.get("content_score", 0.0) * 100)
            collab_score = movie.get("collab_score")
            cf_str = f"{int(collab_score * 100)}%" if collab_score is not None else "N/A (Cold-Start)"
            pop_score = int(movie.get("popularity_score", 0.0) * 100)
            pred_r = movie.get("predicted_rating")
            pred_str = f"{pred_r}★" if pred_r is not None else "N/A"

            st.caption(f"Signals: Content: {c_score}% | CF Pred: {pred_str} ({cf_str}) | Popularity: {pop_score}%")

        # Community Rating Stats
        r_count = movie.get("rating_count", 0)
        mean_r = movie.get("mean_rating", 0.0)
        if r_count > 0:
            st.caption(f"Dataset stats: {mean_r}★ avg across {r_count:,} reviews in MovieLens")

        # Action Buttons
        btn_cols = st.columns([1, 1, 2])
        with btn_cols[0]:
            wl_label = "✓ In Watchlist" if is_in_watchlist else "+ Watchlist"
            if st.button(wl_label, key=f"wl_{mid}_{key_suffix}", use_container_width=True):
                toggle_watchlist(movie)
                st.rerun()

        with btn_cols[1]:
            if show_similar_btn:
                if st.button("Find Similar", key=f"sim_{mid}_{key_suffix}", use_container_width=True):
                    st.session_state.selected_seed_id = mid
                    st.session_state.current_page = "Similar Movies"
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)
