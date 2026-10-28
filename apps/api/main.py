"""
CineMatch FastAPI Production Application
Serves real-time recommendation, search, similarity, persistence (D7), and media endpoints (D8).
Artifacts are loaded strictly during lifespan startup.
"""
from contextlib import asynccontextmanager
import io
import csv
import time
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status, Depends, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import httpx

from pathlib import Path
import json
import platform

from apps.api.config import api_settings
from apps.api.database import get_db, init_db
from apps.api.models import User, Rating, Watchlist, Feedback
from apps.api.media import fetch_media_details
from apps.api.sessions import get_current_user, COOKIE_NAME
from apps.api.schemas import (
    DemoProfile,
    ModelMetaResponse,
    MovieCard,
    RecommendationRequest,
    RecommendationResponse,
    SearchResponse,
    SimilarMoviesResponse,
    UserCreate,
    UserResponse,
    RatingCreate,
    RatingItem,
    WatchlistCreate,
    WatchlistItem,
    FeedbackCreate,
    FeedbackResponse,
    MediaDetails,
    MeResponse,
    ShelfItem,
    ShelvesResponse,
    ShowcaseResponse,
    OnboardingPicksResponse,
    MovieDetailResponse,
    AboutResponse
)
from apps.api.engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads model artifacts during startup, loads strategy, and initializes database tables."""
    t0 = time.time()
    try:
        init_db()
        engine.load_artifacts()
        engine.load_strategy()
    except Exception as e:
        raise RuntimeError(f"Failed to load CineMatch artifacts: {e}") from e
    duration = time.time() - t0
    app.state.startup_duration = duration
    yield


app = FastAPI(
    title=api_settings.app_name,
    version=api_settings.version,
    description="Production Movie Recommendation API with transparent multi-signal ranking.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=api_settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check() -> Dict[str, Any]:
    """Health check endpoint reporting artifact readiness and dataset fingerprint."""
    return {
        "status": "healthy",
        "dataset_fingerprint": engine.fingerprint,
        "is_loaded": engine.is_loaded,
        "catalog_size": len(engine.movie_ids),
        "startup_duration_seconds": round(getattr(app.state, "startup_duration", 0.0), 3)
    }


# ==========================================
# Phase 1: Search & Recommendation Endpoints
# ==========================================

@app.get("/api/search", response_model=SearchResponse)
def search_movies(
    q: str = Query(..., min_length=1, description="Movie search query"),
    limit: int = Query(20, ge=1, le=50)
) -> SearchResponse:
    """Typo-tolerant, article-aware movie search with character highlight offsets."""
    t0 = time.time()
    results = engine.search_movies(q, limit=limit)
    latency_ms = (time.time() - t0) * 1000.0
    return SearchResponse(query=q, results=results, latency_ms=round(latency_ms, 2))


@app.get("/api/similar", response_model=SimilarMoviesResponse)
def get_similar_movies(
    movieId: int = Query(..., description="Target seed movieId"),
    top_n: int = Query(20, ge=1, le=50),
    genres: Optional[str] = Query(None, description="Comma-separated genre filters"),
    genre_mode: str = Query("OR", description="'OR' or 'AND'"),
    year_min: Optional[int] = Query(None, ge=1880, le=2030),
    year_max: Optional[int] = Query(None, ge=1880, le=2030)
) -> SimilarMoviesResponse:
    """O(1) precomputed array similarity lookup combining content cosine and Item-kNN co-ratings."""
    t0 = time.time()
    genre_list = [g.strip() for g in genres.split(",")] if genres else None

    seed_card, similar_cards = engine.get_similar_movies(
        movieId,
        top_n=top_n,
        genres=genre_list,
        genre_mode=genre_mode,
        year_min=year_min,
        year_max=year_max
    )
    if seed_card is None:
        raise HTTPException(status_code=404, detail=f"Movie with movieId {movieId} not found in catalog.")

    latency_ms = (time.time() - t0) * 1000.0
    return SimilarMoviesResponse(
        seed_movie=seed_card,
        similar_movies=similar_cards,
        latency_ms=round(latency_ms, 2)
    )


@app.post("/api/recommendations", response_model=RecommendationResponse)
def get_recommendations(req: RecommendationRequest) -> RecommendationResponse:
    """Personalized hybrid recommendations using ALS fold-in, kNN, taste vector, and learned blend."""
    t0 = time.time()
    cards, cold_tier, summary = engine.get_recommendations(
        user_ratings=req.user_ratings,
        top_n=req.top_n,
        genres=req.genres,
        genre_mode=req.genre_mode,
        year_min=req.year_min,
        year_max=req.year_max,
        min_support=req.min_support,
        diversity_lambda=req.diversity_lambda,
        novelty_boost=req.novelty_boost,
        recency_prior=req.recency_prior,
        signal_mix=req.signal_mix
    )
    latency_ms = (time.time() - t0) * 1000.0
    return RecommendationResponse(
        recommendations=cards,
        total_candidates=len(cards),
        cold_start_tier=cold_tier,
        explanation_summary=summary,
        active_filters={
            "genres": req.genres,
            "genre_mode": req.genre_mode,
            "year_range": [req.year_min, req.year_max],
            "min_support": req.min_support
        },
        latency_ms=round(latency_ms, 2)
    )


@app.get("/api/meta/demo-profiles", response_model=List[DemoProfile])
def get_demo_profiles() -> List[DemoProfile]:
    """Returns dynamic demo user profiles computed directly from MovieLens training data."""
    return [DemoProfile(**p) for p in engine.demo_profiles]


@app.get("/api/meta/model", response_model=ModelMetaResponse)
def get_model_metadata() -> ModelMetaResponse:
    """Reports live model serving configuration, fingerprint, and quality gate outcome."""
    health = engine.meta_dict.get("health_report", {})
    counts = health.get("counts", {})
    metrics = health.get("metrics", {})
    return ModelMetaResponse(
        dataset_fingerprint=engine.fingerprint,
        catalog_size=len(engine.movie_ids),
        clean_ratings_count=counts.get("clean_ratings", 0),
        clean_users_count=counts.get("clean_users", 0),
        sparsity_percentage=metrics.get("sparsity_percentage", 98.3),
        als_factors=engine.Q.shape[1] if engine.Q is not None else 32,
        blend_coefficients=getattr(engine.blend_ranker, "coefficients", {}),
        quality_gate_selected_model=getattr(engine, "active_strategy", "Popularity Baseline")
    )


# ==========================================
# Phase 3: Persistence & User Accounts (D7)
# ==========================================

@app.post("/api/users", response_model=UserResponse)
def get_or_create_user(
    body: Optional[UserCreate] = None,
    user_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
) -> UserResponse:
    """Create a new user or get existing user by ID."""
    if user_id:
        existing = db.query(User).filter(User.id == user_id).first()
        if existing:
            rating_count = db.query(Rating).filter(Rating.user_id == user_id).count()
            watchlist_count = db.query(Watchlist).filter(Watchlist.user_id == user_id).count()
            return UserResponse(
                id=existing.id,
                username=existing.username,
                rating_count=rating_count,
                watchlist_count=watchlist_count,
                created_at=existing.created_at.isoformat()
            )

    new_id = f"u_{uuid.uuid4().hex[:12]}"
    username = body.username if body and body.username else f"Guest_{new_id[-4:]}"
    user = User(id=new_id, username=username)
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        username=user.username,
        rating_count=0,
        watchlist_count=0,
        created_at=user.created_at.isoformat()
    )


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user_profile(user_id: str, db: Session = Depends(get_db)) -> UserResponse:
    """Get user profile and active stats."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    rating_count = db.query(Rating).filter(Rating.user_id == user_id).count()
    watchlist_count = db.query(Watchlist).filter(Watchlist.user_id == user_id).count()
    return UserResponse(
        id=user.id,
        username=user.username,
        rating_count=rating_count,
        watchlist_count=watchlist_count,
        created_at=user.created_at.isoformat()
    )


@app.post("/api/users/demo/{demo_user_id}/load/{user_id}", response_model=Dict[str, Any])
def load_demo_ratings_into_user(demo_user_id: int, user_id: str, db: Session = Depends(get_db)):
    """Loads a demo user's real MovieLens ratings into the active user session."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    demo_p = next((p for p in engine.demo_profiles if p["userId"] == demo_user_id), None)
    if not demo_p:
        raise HTTPException(status_code=404, detail=f"Demo user #{demo_user_id} not found in metadata.")

    # Insert ratings in batch
    count = 0
    for m_id, r_val in demo_p["ratings"].items():
        existing = db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == int(m_id)).first()
        if existing:
            existing.rating = float(r_val)
        else:
            db.add(Rating(user_id=user_id, movie_id=int(m_id), rating=float(r_val)))
        count += 1
    db.commit()
    return {"status": "success", "loaded_ratings": count, "user_id": user_id, "demo_userId": demo_user_id}


# Ratings CRUD
@app.get("/api/users/{user_id}/ratings", response_model=List[RatingItem])
def get_user_ratings(user_id: str, db: Session = Depends(get_db)) -> List[RatingItem]:
    """Retrieve all ratings submitted by a user with catalog metadata."""
    ratings = db.query(Rating).filter(Rating.user_id == user_id).order_by(Rating.created_at.desc()).all()
    results = []
    for r in ratings:
        meta = engine.get_movie_metadata(r.movie_id)
        results.append(RatingItem(
            movieId=r.movie_id,
            rating=r.rating,
            title=meta.get("title", f"Movie #{r.movie_id}"),
            display_title=meta.get("display_title", meta.get("title", f"Movie #{r.movie_id}")),
            year=meta.get("year"),
            genres=meta.get("genres", []),
            created_at=r.created_at.isoformat()
        ))
    return results


@app.post("/api/users/{user_id}/ratings", response_model=RatingItem)
def submit_rating(user_id: str, body: RatingCreate, db: Session = Depends(get_db)) -> RatingItem:
    """Add or update a movie rating for a user."""
    # Ensure user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=f"User_{user_id[-4:]}")
        db.add(user)
        db.commit()

    existing = db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == body.movieId).first()
    if existing:
        existing.rating = body.rating
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_rating = Rating(user_id=user_id, movie_id=body.movieId, rating=body.rating)
        db.add(new_rating)
        db.commit()
        db.refresh(new_rating)
        target = new_rating

    meta = engine.get_movie_metadata(body.movieId)
    return RatingItem(
        movieId=target.movie_id,
        rating=target.rating,
        title=meta.get("title", f"Movie #{target.movie_id}"),
        display_title=meta.get("display_title", meta.get("title", f"Movie #{target.movie_id}")),
        year=meta.get("year"),
        genres=meta.get("genres", []),
        created_at=target.created_at.isoformat()
    )


@app.delete("/api/users/{user_id}/ratings/{movie_id}", status_code=status.HTTP_200_OK)
def delete_rating(user_id: str, movie_id: int, db: Session = Depends(get_db)):
    """Delete a user rating."""
    r = db.query(Rating).filter(Rating.user_id == user_id, Rating.movie_id == movie_id).first()
    if not r:
        raise HTTPException(status_code=404, detail=f"Rating for movie {movie_id} not found")
    db.delete(r)
    db.commit()
    return {"status": "deleted", "movieId": movie_id}


# Watchlist CRUD & Export
@app.get("/api/users/{user_id}/watchlist", response_model=List[WatchlistItem])
def get_user_watchlist(user_id: str, db: Session = Depends(get_db)) -> List[WatchlistItem]:
    """Retrieve all movies on a user's watchlist."""
    items = db.query(Watchlist).filter(Watchlist.user_id == user_id).order_by(Watchlist.created_at.desc()).all()
    results = []
    for item in items:
        meta = engine.get_movie_metadata(item.movie_id)
        results.append(WatchlistItem(
            movieId=item.movie_id,
            notes=item.notes,
            title=meta.get("title", f"Movie #{item.movie_id}"),
            display_title=meta.get("display_title", meta.get("title", f"Movie #{item.movie_id}")),
            year=meta.get("year"),
            genres=meta.get("genres", []),
            vote_average=float(meta.get("vote_average", 0.0)),
            vote_count=int(meta.get("vote_count", 0)),
            added_at=item.created_at.isoformat()
        ))
    return results


@app.post("/api/users/{user_id}/watchlist", response_model=WatchlistItem)
def add_to_watchlist(user_id: str, body: WatchlistCreate, db: Session = Depends(get_db)) -> WatchlistItem:
    """Add a movie to user's watchlist."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=f"User_{user_id[-4:]}")
        db.add(user)
        db.commit()

    existing = db.query(Watchlist).filter(Watchlist.user_id == user_id, Watchlist.movie_id == body.movieId).first()
    if existing:
        if body.notes is not None:
            existing.notes = body.notes
            db.commit()
            db.refresh(existing)
        target = existing
    else:
        new_item = Watchlist(user_id=user_id, movie_id=body.movieId, notes=body.notes)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        target = new_item

    meta = engine.get_movie_metadata(body.movieId)
    return WatchlistItem(
        movieId=target.movie_id,
        notes=target.notes,
        title=meta.get("title", f"Movie #{target.movie_id}"),
        display_title=meta.get("display_title", meta.get("title", f"Movie #{target.movie_id}")),
        year=meta.get("year"),
        genres=meta.get("genres", []),
        vote_average=float(meta.get("vote_average", 0.0)),
        vote_count=int(meta.get("vote_count", 0)),
        added_at=target.created_at.isoformat()
    )


@app.delete("/api/users/{user_id}/watchlist/{movie_id}", status_code=status.HTTP_200_OK)
def remove_from_watchlist(user_id: str, movie_id: int, db: Session = Depends(get_db)):
    """Remove a movie from user's watchlist."""
    item = db.query(Watchlist).filter(Watchlist.user_id == user_id, Watchlist.movie_id == movie_id).first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Movie {movie_id} not in watchlist")
    db.delete(item)
    db.commit()
    return {"status": "removed", "movieId": movie_id}


@app.get("/api/users/{user_id}/watchlist/export")
def export_watchlist_csv(user_id: str, db: Session = Depends(get_db)):
    """Export user's watchlist as a downloadable CSV."""
    items = db.query(Watchlist).filter(Watchlist.user_id == user_id).order_by(Watchlist.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["MovieId", "Title", "Year", "Genres", "VoteAverage", "VoteCount", "AddedAt", "Notes"])

    for item in items:
        meta = engine.get_movie_metadata(item.movie_id)
        writer.writerow([
            item.movie_id,
            meta.get("title", ""),
            meta.get("year", ""),
            "|".join(meta.get("genres", [])),
            meta.get("vote_average", ""),
            meta.get("vote_count", ""),
            item.created_at.isoformat(),
            item.notes or ""
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=cinematch_watchlist_{user_id}.csv"}
    )


# Feedback Tracking
@app.post("/api/users/{user_id}/feedback", response_model=FeedbackResponse)
def track_feedback(user_id: str, body: FeedbackCreate, db: Session = Depends(get_db)) -> FeedbackResponse:
    """Record user interaction feedback for model audit."""
    fb = Feedback(user_id=user_id, movie_id=body.movieId, interaction_type=body.interaction_type)
    db.add(fb)
    db.commit()
    return FeedbackResponse(status="recorded", message=f"Recorded '{body.interaction_type}' for movie #{body.movieId}")


def _compute_user_recommendations(
    user_id: str,
    top_n: int = 20,
    genres: Optional[str] = None,
    genre_mode: str = "OR",
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    min_support: int = 5,
    diversity_lambda: float = 0.15,
    novelty_boost: float = 0.05,
    recency_prior: float = 0.0,
    db: Session = None
) -> RecommendationResponse:
    """Internal business logic helper for user recommendations with native types."""
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all() if db else []
    user_ratings = {r.movie_id: r.rating for r in ratings}
    genre_list = [g.strip() for g in genres.split(",")] if genres else None

    req = RecommendationRequest(
        user_ratings=user_ratings,
        top_n=top_n,
        genres=genre_list,
        genre_mode=genre_mode or "OR",
        year_min=year_min,
        year_max=year_max,
        min_support=min_support if min_support is not None else 5,
        diversity_lambda=diversity_lambda if diversity_lambda is not None else 0.15,
        novelty_boost=novelty_boost if novelty_boost is not None else 0.05,
        recency_prior=recency_prior if recency_prior is not None else 0.0
    )
    return get_recommendations(req)


# Connected Recommendations using persistent ratings
@app.get("/api/users/{user_id}/recommendations", response_model=RecommendationResponse)
def get_user_personalized_recommendations(
    user_id: str,
    top_n: int = Query(20, ge=1, le=50),
    genres: Optional[str] = Query(None),
    genre_mode: str = Query("OR"),
    year_min: Optional[int] = Query(None),
    year_max: Optional[int] = Query(None),
    min_support: int = Query(5),
    diversity_lambda: float = Query(0.15),
    novelty_boost: float = Query(0.05),
    recency_prior: float = Query(0.0),
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """Personalized recommendations using persistent ratings loaded from SQLite."""
    return _compute_user_recommendations(
        user_id=user_id,
        top_n=top_n,
        genres=genres,
        genre_mode=genre_mode,
        year_min=year_min,
        year_max=year_max,
        min_support=min_support,
        diversity_lambda=diversity_lambda,
        novelty_boost=novelty_boost,
        recency_prior=recency_prior,
        db=db
    )


# ==========================================
# Phase 4: Media & Visuals Endpoints (D8)
# ==========================================

@app.get("/api/media/movie/{movie_id}", response_model=MediaDetails)
async def get_movie_media_details(movie_id: int, db: Session = Depends(get_db)) -> MediaDetails:
    """Fetches media details (posters, trailers, providers) by MovieLens movieId."""
    meta = engine.get_movie_metadata(movie_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Movie #{movie_id} not found in catalog")

    tmdb_id = meta.get("tmdbId")
    title = meta.get("title", f"Movie #{movie_id}")
    year = meta.get("year")
    genres = meta.get("genres", [])

    return await fetch_media_details(
        movie_id=movie_id,
        tmdb_id=tmdb_id,
        title=title,
        year=year,
        genres=genres,
        db=db
    )


@app.get("/api/media/tmdb/{tmdb_id}", response_model=MediaDetails)
async def get_media_by_tmdb_id(tmdb_id: int, db: Session = Depends(get_db)) -> MediaDetails:
    """Fetches media details directly by TMDB ID."""
    # Find matching movie in catalog if possible
    movie_id = 0
    title = f"TMDB #{tmdb_id}"
    year = None
    genres = []

    if engine.is_loaded and "tmdbId" in engine.catalog_df.columns:
        match = engine.catalog_df[engine.catalog_df["tmdbId"] == tmdb_id]
        if not match.empty:
            row = match.iloc[0]
            movie_id = int(row["movieId"])
            title = str(row["title"])
            year = int(row["year"]) if row["year"] > 0 else None
            genres = str(row["genres"]).split("|") if row["genres"] else []

    return await fetch_media_details(
        movie_id=movie_id,
        tmdb_id=tmdb_id,
        title=title,
        year=year,
        genres=genres,
        db=db
    )


# ==========================================
# Phase P1: Identity & Visitor Endpoints (/api/me/*)
# ==========================================

@app.get("/api/me", response_model=MeResponse)
def get_current_session_info(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MeResponse:
    """Returns current visitor session status and interaction counts."""
    picks_count = db.query(Rating).filter(Rating.user_id == user.id).count()
    library_count = db.query(Watchlist).filter(Watchlist.user_id == user.id).count()
    return MeResponse(
        user_id=user.id,
        username=user.username,
        picks_count=picks_count,
        library_count=library_count,
        has_picks=picks_count >= 5,
        created_at=user.created_at.isoformat()
    )


@app.get("/api/me/ratings", response_model=List[RatingItem])
def get_my_ratings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[RatingItem]:
    """Retrieve all ratings submitted by active session."""
    return get_user_ratings(user_id=user.id, db=db)


@app.post("/api/me/ratings", response_model=RatingItem)
def submit_my_rating(
    body: RatingCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RatingItem:
    """Submit or update a rating in active session."""
    return submit_rating(user_id=user.id, body=body, db=db)


@app.delete("/api/me/ratings/{movie_id}")
def delete_my_rating(
    movie_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a rating from active session."""
    return delete_rating(user_id=user.id, movie_id=movie_id, db=db)


@app.get("/api/me/watchlist", response_model=List[WatchlistItem])
def get_my_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[WatchlistItem]:
    """Retrieve watchlist movies for active session."""
    return get_user_watchlist(user_id=user.id, db=db)


@app.put("/api/me/watchlist/{movie_id}", response_model=WatchlistItem)
def add_to_my_watchlist(
    movie_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> WatchlistItem:
    """Add a movie to active session's watchlist."""
    body = WatchlistCreate(movieId=movie_id)
    return add_to_watchlist(user_id=user.id, body=body, db=db)


@app.delete("/api/me/watchlist/{movie_id}")
def remove_from_my_watchlist(
    movie_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a movie from active session's watchlist."""
    return remove_from_watchlist(user_id=user.id, movie_id=movie_id, db=db)


@app.get("/api/me/shelves", response_model=ShelvesResponse)
def get_my_shelves(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ShelvesResponse:
    """Returns curated recommendation shelves with structured explanations."""
    ratings = db.query(Rating).filter(Rating.user_id == user.id).all()
    user_ratings = {r.movie_id: r.rating for r in ratings}
    seen_ids = set(user_ratings.keys())

    shelves: List[ShelfItem] = []

    # Shelf 1: Top picks
    rec_cards, _, _ = engine.get_recommendations(user_ratings=user_ratings, top_n=10)
    filtered_recs = [c for c in rec_cards if c.movieId not in seen_ids][:8]
    if filtered_recs:
        shelves.append(ShelfItem(
            id="top_picks",
            title="Top picks for you",
            reason="Curated to match your active taste profile",
            movies=filtered_recs
        ))
        seen_ids.update(c.movieId for c in filtered_recs)

    # Shelves 2-4: "Because you liked X"
    high_rated = sorted([r for r in ratings if r.rating >= 4.0], key=lambda r: r.rating, reverse=True)
    for r in high_rated[:3]:
        meta = engine.get_movie_metadata(r.movie_id)
        stitle = meta.get("display_title", meta.get("title", f"Movie #{r.movie_id}"))
        _, sim_cards = engine.get_similar_movies(r.movie_id, top_n=12)
        valid_sim = [c for c in sim_cards if c.movieId not in seen_ids][:8]
        if valid_sim:
            shelves.append(ShelfItem(
                id=f"because_liked_{r.movie_id}",
                title=f"Because you liked {stitle}",
                reason=f"Shares tone, genre, and community rating patterns with {stitle}",
                movies=valid_sim
            ))
            seen_ids.update(c.movieId for c in valid_sim)

    # Shelf 5: Hidden gems
    if engine.catalog_df is not None:
        gems_df = engine.catalog_df[
            (~engine.catalog_df["movieId"].isin(seen_ids)) &
            (engine.catalog_df["vote_count"] >= 15) &
            (engine.catalog_df["vote_count"] <= 120) &
            (engine.catalog_df["vote_average"] >= 3.8)
        ].sort_values("weighted_rating", ascending=False)
        gems_cards = []
        for mid in gems_df["movieId"].head(8):
            c = engine.get_movie_card_by_id(int(mid))
            if c:
                gems_cards.append(c)
        if gems_cards:
            shelves.append(ShelfItem(
                id="hidden_gems",
                title="Hidden gems",
                reason="Critically acclaimed films waiting to be discovered",
                movies=gems_cards
            ))
            seen_ids.update(c.movieId for c in gems_cards)

    # Shelf 6: Popular now
    if engine.catalog_df is not None:
        pop_df = engine.catalog_df[
            (~engine.catalog_df["movieId"].isin(seen_ids)) &
            (engine.catalog_df["vote_count"] >= 100)
        ].sort_values("weighted_rating", ascending=False)
        pop_cards = []
        for mid in pop_df["movieId"].head(8):
            c = engine.get_movie_card_by_id(int(mid))
            if c:
                pop_cards.append(c)
        if pop_cards:
            shelves.append(ShelfItem(
                id="popular_now",
                title="Popular right now",
                reason="Most celebrated films across all moviegoers",
                movies=pop_cards
            ))

    return ShelvesResponse(shelves=shelves)


@app.get("/api/me/recommendations", response_model=RecommendationResponse)
def get_my_recommendations(
    novelty: float = Query(0.05),
    diversity: float = Query(0.15),
    recency: float = Query(0.0),
    genres: Optional[str] = Query(None),
    decades: Optional[str] = Query(None),
    top_n: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> RecommendationResponse:
    """Ranked recommendations parameterized for the Tune faders."""
    year_min = None
    year_max = None
    if decades:
        dec = decades.lower().strip()
        if "2020" in dec:
            year_min, year_max = 2020, 2030
        elif "2010" in dec:
            year_min, year_max = 2010, 2019
        elif "2000" in dec:
            year_min, year_max = 2000, 2009
        elif "1990" in dec:
            year_min, year_max = 1990, 1999
        elif "1980" in dec:
            year_min, year_max = 1980, 1989
        elif "classic" in dec:
            year_min, year_max = 1880, 1979

    return _compute_user_recommendations(
        user_id=user.id,
        top_n=top_n,
        genres=genres,
        genre_mode="OR",
        year_min=year_min,
        year_max=year_max,
        min_support=5,
        diversity_lambda=diversity,
        novelty_boost=novelty,
        recency_prior=recency,
        db=db
    )


@app.post("/api/me/events", response_model=FeedbackResponse)
def record_my_event(
    body: FeedbackCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> FeedbackResponse:
    """Record interaction event (impression, click, dismiss)."""
    return track_feedback(user_id=user.id, body=body, db=db)


@app.get("/api/me/export")
def export_my_data(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export complete visitor profile and history as JSON."""
    ratings = db.query(Rating).filter(Rating.user_id == user.id).all()
    watchlist = db.query(Watchlist).filter(Watchlist.user_id == user.id).all()
    feedback = db.query(Feedback).filter(Feedback.user_id == user.id).all()

    data = {
        "user_id": user.id,
        "created_at": user.created_at.isoformat(),
        "ratings": [
            {"movie_id": r.movie_id, "rating": r.rating, "rated_at": r.created_at.isoformat()}
            for r in ratings
        ],
        "watchlist": [
            {"movie_id": w.movie_id, "notes": w.notes, "added_at": w.created_at.isoformat()}
            for w in watchlist
        ],
        "interactions": [
            {"movie_id": f.movie_id, "type": f.interaction_type, "timestamp": f.created_at.isoformat()}
            for f in feedback
        ]
    }
    return Response(content=json.dumps(data, indent=2), media_type="application/json")


@app.delete("/api/me")
def erase_my_data(
    response: Response,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Erase all user data (ratings, watchlist, events) and clear session cookie."""
    db.delete(user)
    db.commit()
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "erased", "message": "All session data erased successfully."}


@app.get("/api/showcase", response_model=ShowcaseResponse)
def get_showcase() -> ShowcaseResponse:
    """Returns 60 diverse, recognizable poster items for hero wall and ticker."""
    return ShowcaseResponse(movies=engine.get_showcase_movies(limit=60))


@app.get("/api/onboarding/picks", response_model=OnboardingPicksResponse)
def get_onboarding_picks(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> OnboardingPicksResponse:
    """Returns 18 titles chosen to cover genres and decades with high support."""
    rated_ids = {r.movie_id for r in db.query(Rating).filter(Rating.user_id == user.id).all()}
    return OnboardingPicksResponse(movies=engine.get_onboarding_picks(exclude_ids=rated_ids, limit=18))


@app.get("/api/movies/{id}", response_model=MovieDetailResponse)
async def get_movie_detail(
    id: int,
    db: Session = Depends(get_db)
) -> MovieDetailResponse:
    """Returns full movie details, media assets, cast, providers, and similar IDs."""
    card = engine.get_movie_card_by_id(id)
    if not card:
        raise HTTPException(status_code=404, detail=f"Movie #{id} not found in catalog")

    media = await fetch_media_details(
        movie_id=id,
        tmdb_id=card.tmdbId,
        title=card.title,
        year=card.year,
        genres=card.genres,
        db=db
    )
    _, similar_cards = engine.get_similar_movies(id, top_n=6)
    similar_ids = [c.movieId for c in similar_cards]

    return MovieDetailResponse(movie=card, media=media, similar_ids=similar_ids)


@app.get("/api/about", response_model=AboutResponse)
def get_about_metadata() -> AboutResponse:
    """Returns generated facts from eval_results.json, strategy.json, and dataset counts."""
    eval_path = Path("eval_results.json")
    if not eval_path.exists():
        eval_path = Path("artifacts/eval_results.json")
    eval_data: Dict[str, Any] = {}
    if eval_path.exists():
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                eval_data = json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read eval_results.json: {e}")

    return AboutResponse(
        dataset={
            "name": "MovieLens (ml-latest-small)",
            "citation": "F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM TiiS 5, 4, Article 19.",
            "clean_ratings": 100836,
            "clean_users": 610,
            "clean_movies": len(engine.movie_ids) if engine.is_loaded else 9742,
            "sparsity_pct": 98.3,
            "terms": "Non-commercial, educational and research development dataset."
        },
        evaluation=eval_data,
        active_strategy={
            "strategy": getattr(engine, "active_strategy", "Popularity Baseline"),
            "data": getattr(engine, "strategy_data", {})
        },
        versions={
            "python": platform.python_version(),
            "fastapi": "0.115.0",
            "nextjs": "16.4.3",
            "scikit_learn": "1.6.1",
            "numpy": "2.2.3"
        },
        licenses={
            "movielens": "GroupLens Non-Commercial Research License",
            "tmdb": "Movie metadata and posters provided by The Movie Database (TMDB). This product uses the TMDB API but is not endorsed or certified by TMDB.",
            "code": "MIT License"
        }
    )

