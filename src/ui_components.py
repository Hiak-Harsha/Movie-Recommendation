"""
CineMatch UI Components
Implements typographic poster tiles, real widget movie cards (st.container(border=True)),
pure watchlist state management, HTML escaping helpers, and ticker strip renderers.
"""
import html
from typing import Any, Dict, List, Optional, Tuple
import streamlit as st


GENRE_PALETTES: Dict[str, Tuple[str, str]] = {
    "Action": ("#2a1f18", "#e5a93c"),
    "Sci-Fi": ("#122228", "#38bdf8"),
    "Drama": ("#1f1828", "#c084fc"),
    "Comedy": ("#262312", "#facc15"),
    "Horror": ("#281216", "#f87171"),
    "Animation": ("#14251c", "#4ade80"),
    "Thriller": ("#211a14", "#fb923c"),
    "Romance": ("#29141d", "#f472b6"),
    "Adventure": ("#19241b", "#34d399"),
    "Crime": ("#241920", "#e879f9"),
    "Mystery": ("#181f28", "#60a5fa"),
    "Fantasy": ("#231b27", "#a78bfa"),
    "Western": ("#2b1f15", "#d97706"),
    "Documentary": ("#162326", "#2dd4bf"),
    "Film-Noir": ("#171717", "#a3a3a3"),
    "Default": ("#18191d", "#94a3b8"),
}


def safe_text(val: Any) -> str:
    """Escapes dynamic string to prevent HTML/XSS injection vulnerabilities."""
    if val is None:
        return ""
    return html.escape(str(val))


# --- Pure Watchlist Logic (Testable without Streamlit) ---

def add_to_watchlist(watchlist: Dict[int, Any], movie_data: Dict[str, Any]) -> Dict[int, Any]:
    """Pure function: adds movie to watchlist dictionary if not present."""
    mid = int(movie_data["movieId"])
    if mid not in watchlist:
        new_wl = dict(watchlist)
        new_wl[mid] = dict(movie_data)
        return new_wl
    return watchlist


def remove_from_watchlist(watchlist: Dict[int, Any], movie_id: int) -> Dict[int, Any]:
    """Pure function: removes movie from watchlist dictionary."""
    mid = int(movie_id)
    if mid in watchlist:
        new_wl = dict(watchlist)
        del new_wl[mid]
        return new_wl
    return watchlist


def is_in_watchlist(watchlist: Dict[int, Any], movie_id: int) -> bool:
    """Pure function: checks if movieId exists in watchlist."""
    return int(movie_id) in watchlist


# --- Streamlit Callbacks & State Helpers ---

def init_session_state():
    """Initializes Streamlit session state keys."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Discover"
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = {}  # {movieId: movie_dict}
    if "user_ratings" not in st.session_state:
        st.session_state.user_ratings = {}  # {movieId: rating}
    if "selected_seed_id" not in st.session_state:
        st.session_state.selected_seed_id = 2571  # The Matrix default
    if "demo_profile_id" not in st.session_state:
        st.session_state.demo_profile_id = None


def toggle_watchlist_callback(movie_dict: Dict[str, Any]):
    """Callback for toggling watchlist membership without triggering model recalculation."""
    mid = int(movie_dict["movieId"])
    if mid in st.session_state.watchlist:
        st.session_state.watchlist = remove_from_watchlist(st.session_state.watchlist, mid)
    else:
        st.session_state.watchlist = add_to_watchlist(st.session_state.watchlist, movie_dict)


def set_seed_movie_callback(movie_id: int):
    """Callback to switch the seed movie in Similar Movies without a page reload."""
    st.session_state.selected_seed_id = int(movie_id)
    st.session_state.current_page = "Similar Movies"


def render_typographic_poster(display_title: str, genres_list: List[str], release_year: Optional[int]) -> str:
    """Generates an original typographic poster tile with initial letter and genre palette."""
    first_genre = genres_list[0] if genres_list else "Default"
    bg_color, text_color = GENRE_PALETTES.get(first_genre, GENRE_PALETTES["Default"])

    # Extract initial letter (ignoring leading quotes or non-alphanumeric)
    clean_title = safe_text(display_title).strip()
    letter = "M"
    for char in clean_title:
        if char.isalnum():
            letter = char.upper()
            break

    year_str = str(release_year) if release_year else "—"

    return f"""
    <div class="poster-tile" style="background: {bg_color}; color: {text_color}; border-color: {text_color}40;">
        <span class="poster-letter">{letter}</span>
        <span class="poster-year">{year_str}</span>
    </div>
    """


def render_movie_card(
    movie: Dict[str, Any],
    card_type: str = "hybrid",
    key_suffix: str = "",
    page_context: str = "main"
):
    """
    Renders an accessible movie card using real Streamlit widgets (st.container(border=True)).
    Features typographic poster tile, real IMDb link, safe HTML escaping, and watchlist action.
    """
    mid = int(movie["movieId"])
    display_title = movie.get("display_title", movie.get("title", f"Movie #{mid}"))
    release_year = movie.get("release_year")
    genres_list = movie.get("genres_list", [])
    imdb_id = movie.get("imdbId")

    in_wl = is_in_watchlist(st.session_state.watchlist, mid)

    with st.container(border=True):
        col_poster, col_content, col_actions = st.columns([1, 4, 1.5])

        with col_poster:
            poster_html = render_typographic_poster(display_title, genres_list, release_year)
            st.markdown(poster_html, unsafe_allow_html=True)

        with col_content:
            # Title, Year, and IMDb link
            safe_title = safe_text(display_title)
            year_tag = f"<span style='color: #8b949e; font-size: 0.9rem;'> ({release_year})</span>" if release_year else ""
            
            imdb_html = ""
            if imdb_id and pd.notnull(imdb_id):
                imdb_url = f"https://www.imdb.com/title/tt{int(imdb_id):07d}/"
                imdb_html = f"&nbsp;•&nbsp; <a href='{imdb_url}' target='_blank' class='imdb-link'>Open on IMDb ↗</a>"

            st.markdown(
                f"<div style='font-size: 1.15rem; font-weight: 700; color: #ffffff; margin-bottom: 4px;'>"
                f"{safe_title}{year_tag}{imdb_html}</div>",
                unsafe_allow_html=True
            )

            # Genre Chips
            chips_html = "".join([f"<span class='badge-genre'>{safe_text(g)}</span>" for g in genres_list[:4]])
            st.markdown(chips_html, unsafe_allow_html=True)

            # Evidence & Explanations
            reasons = movie.get("reasons", [])
            if reasons:
                reasons_escaped = "<br>".join([f"• {safe_text(r)}" for r in reasons[:2]])
                st.markdown(f"<div class='evidence-quote'>{reasons_escaped}</div>", unsafe_allow_html=True)

            # Community rating stats
            r_count = movie.get("rating_count", 0)
            m_rating = movie.get("mean_rating", 0.0)
            if r_count > 0:
                st.caption(f"Dataset stats: {m_rating}★ from {r_count:,} reviews (Training set)")
            else:
                st.caption("No historical reviews in training set.")

        with col_actions:
            # Score badge
            if card_type == "similar" and movie.get("content_similarity") is not None:
                sim = movie["content_similarity"]
                st.markdown(f"<div style='text-align: right;'><span class='badge-score'>Similarity {sim:.2f}</span></div>", unsafe_allow_html=True)
            elif card_type == "hybrid" and "hybrid_score" in movie:
                hyb = movie["hybrid_score"]
                st.markdown(f"<div style='text-align: right;'><span class='badge-score'>Match {hyb:.2f}</span></div>", unsafe_allow_html=True)
            elif "weighted_rating" in movie and movie["weighted_rating"] > 0:
                w_r = movie["weighted_rating"]
                st.markdown(f"<div style='text-align: right;'><span class='badge-score'>★ {w_r:.2f}</span></div>", unsafe_allow_html=True)

            st.write("")
            # Watchlist real widget button with callback
            btn_label = "✓ Saved" if in_wl else "+ Watchlist"
            st.button(
                btn_label,
                key=f"wl_{page_context}_{mid}_{key_suffix}",
                on_click=toggle_watchlist_callback,
                args=(movie,),
                use_container_width=True
            )

            # Similar exploration shortcut
            if card_type != "similar":
                st.button(
                    "Find Similar",
                    key=f"sim_btn_{page_context}_{mid}_{key_suffix}",
                    on_click=set_seed_movie_callback,
                    args=(mid,),
                    use_container_width=True
                )


def render_ticker_strip(top_items: List[Dict[str, Any]]) -> str:
    """Renders a studio ticker strip of computed top titles or genres."""
    items_html = []
    for itm in top_items[:6]:
        title = safe_text(itm.get("display_title", itm.get("title", "")))
        w_r = itm.get("weighted_rating", 0.0)
        items_html.append(f"<span class='ticker-item'><strong>{title}</strong> ★ {w_r}</span>")

    strip_content = "".join(items_html)
    return f"""
    <div class="ticker-strip">
        <span class="ticker-label">Catalog Spotlight</span>
        {strip_content}
    </div>
    """
