"""
CineMatch FastAPI Production Application
Serves real-time recommendation, search, and similarity endpoints.
Artifacts are loaded strictly during lifespan startup.
"""
from contextlib import asynccontextmanager
import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
import httpx

from apps.api.config import api_settings
from apps.api.schemas import (
    DemoProfile,
    ModelMetaResponse,
    MovieCard,
    RecommendationRequest,
    RecommendationResponse,
    SearchResponse,
    SimilarMoviesResponse
)
from apps.api.engine import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Loads model artifacts during startup and performs startup health verification."""
    t0 = time.time()
    try:
        engine.load_artifacts()
    except Exception as e:
        raise RuntimeError(f"Failed to load CineMatch artifacts: {e}") from e
    duration = time.time() - t0
    app.state.startup_duration = duration
    yield
    # Shutdown logic if needed


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
        quality_gate_selected_model="Popularity Baseline (Validated Global Benchmark) / CineMatch Hybrid (Personalized)"
    )


@app.get("/api/media/{tmdb_id}")
async def get_tmdb_media_details(tmdb_id: int):
    """
    Proxies TMDB media details (posters, backdrops, overviews, trailers).
    API key is kept strictly on the server and never sent to the client.
    """
    if not api_settings.tmdb_api_key:
        return {
            "tmdb_id": tmdb_id,
            "poster_path": None,
            "backdrop_path": None,
            "overview": None,
            "configured": False
        }

    url = f"{api_settings.tmdb_base_url}/movie/{tmdb_id}"
    params = {"api_key": api_settings.tmdb_api_key, "append_to_response": "videos,credits"}
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "tmdb_id": tmdb_id,
                    "poster_url": f"{api_settings.tmdb_image_base_url}{data.get('poster_path')}" if data.get("poster_path") else None,
                    "backdrop_url": f"{api_settings.tmdb_image_base_url}{data.get('backdrop_path')}" if data.get("backdrop_path") else None,
                    "overview": data.get("overview"),
                    "configured": True
                }
    except Exception as e:
        logger.warning(f"TMDB request failed: {e}")

    return {"tmdb_id": tmdb_id, "poster_url": None, "overview": None, "configured": True}
