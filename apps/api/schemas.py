"""
CineMatch API Schemas (Pydantic v2)
Structured, typed request and response models.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SignalExplanation(BaseModel):
    type: str = Field(..., description="Type of signal evidence: 'neighbor', 'genre', 'tags', 'cf', 'popularity'")
    details: Dict[str, Any] = Field(default_factory=dict, description="Raw computed facts")


class SignalContributions(BaseModel):
    mf: float = 0.0
    knn: float = 0.0
    content: float = 0.0
    popularity: float = 0.0


class MovieCard(BaseModel):
    movieId: int
    title: str
    display_title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    vote_count: int = 0
    vote_average: float = 0.0
    weighted_rating: float = 0.0
    score: float = Field(0.0, description="Normalized score in [0.0, 1.0]")
    predicted_rating: Optional[float] = None
    signals: List[SignalExplanation] = Field(default_factory=list)
    contributions: SignalContributions = Field(default_factory=SignalContributions)
    imdbId: Optional[str] = None
    tmdbId: Optional[int] = None
    poster_url: Optional[str] = None


class RecommendationRequest(BaseModel):
    user_ratings: Dict[int, float] = Field(default_factory=dict, description="Map of {movieId: rating}")
    top_n: int = Field(20, ge=1, le=100)
    genres: Optional[List[str]] = None
    genre_mode: str = Field("OR", description="'OR' or 'AND'")
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    min_support: int = Field(5, ge=0, description="Minimum rating count support (lower for hidden gems)")
    diversity_lambda: float = Field(0.15, ge=0.0, le=1.0)
    novelty_boost: float = Field(0.05, ge=0.0, le=1.0)
    recency_prior: float = Field(0.0, ge=-1.0, le=1.0)
    signal_mix: Optional[Dict[str, float]] = Field(
        default_factory=lambda: {"collaborative": 1.0, "content": 1.0, "popularity": 1.0}
    )


class RecommendationResponse(BaseModel):
    recommendations: List[MovieCard]
    total_candidates: int
    cold_start_tier: str = Field(..., description="'zero_ratings', 'content_fallback', or 'full_pipeline'")
    explanation_summary: str
    active_filters: Dict[str, Any]
    latency_ms: float


class SimilarMoviesResponse(BaseModel):
    seed_movie: MovieCard
    similar_movies: List[MovieCard]
    latency_ms: float


class SearchResult(BaseModel):
    movieId: int
    title: str
    display_title: str
    year: Optional[int] = None
    genres: List[str]
    vote_count: int
    vote_average: float
    weighted_rating: float
    imdbId: Optional[str] = None
    tmdbId: Optional[int] = None
    score: float
    match_offsets: List[int] = Field(default_factory=list, description="[start, end] char indices for highlighting")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    latency_ms: float


class DemoProfile(BaseModel):
    userId: int
    label: str
    rating_count: int
    top_genres: List[str]
    top_decade: str
    avg_rating: float
    ratings: Dict[int, float]


class ModelMetaResponse(BaseModel):
    dataset_fingerprint: str
    catalog_size: int
    clean_ratings_count: int
    clean_users_count: int
    sparsity_percentage: float
    als_factors: int
    blend_coefficients: Dict[str, float]
    quality_gate_selected_model: str


# Persistence & Accounts Schemas (Defect D7)
class UserCreate(BaseModel):
    username: Optional[str] = Field(None, max_length=128)


class UserResponse(BaseModel):
    id: str
    username: str
    rating_count: int = 0
    watchlist_count: int = 0
    created_at: str


class RatingCreate(BaseModel):
    movieId: int = Field(..., ge=1)
    rating: float = Field(..., ge=0.5, le=5.0)


class RatingItem(BaseModel):
    movieId: int
    rating: float
    title: str
    display_title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    created_at: str


class WatchlistCreate(BaseModel):
    movieId: int = Field(..., ge=1)
    notes: Optional[str] = Field(None, max_length=500)


class WatchlistItem(BaseModel):
    movieId: int
    notes: Optional[str] = None
    title: str
    display_title: str
    year: Optional[int] = None
    genres: List[str] = Field(default_factory=list)
    vote_average: float = 0.0
    vote_count: int = 0
    added_at: str


class FeedbackCreate(BaseModel):
    movieId: int
    interaction_type: str = Field(..., pattern="^(click|like|dislike|dismiss)$")


class FeedbackResponse(BaseModel):
    status: str
    message: str


# Visuals & Media Schemas (Defect D8)
class CastMember(BaseModel):
    name: str
    character: Optional[str] = None


class MediaDetails(BaseModel):
    tmdb_id: Optional[int] = None
    movieId: int
    title: str
    poster_url: Optional[str] = None
    backdrop_url: Optional[str] = None
    overview: Optional[str] = None
    cast: List[CastMember] = Field(default_factory=list)
    director: Optional[str] = None
    trailer_key: Optional[str] = None
    streaming_providers: List[str] = Field(default_factory=list)
    runtime: Optional[int] = None
    vote_average: Optional[float] = None
    fallback_accent: str = "#f59e0b"


# ==========================================
# Phase P1: Identity & Visitor Schemas
# ==========================================
class MeResponse(BaseModel):
    user_id: str
    username: str
    picks_count: int
    library_count: int
    has_picks: bool
    created_at: str


class ShelfItem(BaseModel):
    id: str
    title: str
    reason: str
    movies: List[MovieCard]


class ShelvesResponse(BaseModel):
    shelves: List[ShelfItem]


class ShowcaseResponse(BaseModel):
    movies: List[MovieCard]


class OnboardingPicksResponse(BaseModel):
    movies: List[MovieCard]


class MovieDetailResponse(BaseModel):
    movie: MovieCard
    media: Optional[MediaDetails] = None
    similar_ids: List[int] = Field(default_factory=list)


class AboutResponse(BaseModel):
    dataset: Dict[str, Any]
    evaluation: Dict[str, Any]
    active_strategy: Dict[str, Any]
    versions: Dict[str, str]
    licenses: Dict[str, str]


