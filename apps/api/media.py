"""
CineMatch Media Service (Defect D8: Visuals & Media Integration)
Fetches and caches TMDB media assets (posters, backdrops, trailers, cast, directors, streaming providers).
Falls back gracefully to rich typographic palettes and metadata when TMDB is unavailable or offline.
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session

from apps.api.config import api_settings
from apps.api.models import MediaCache
from apps.api.schemas import CastMember, MediaDetails

logger = logging.getLogger("cinematch.media")

GENRE_ACCENTS: Dict[str, str] = {
    "Action": "#ef4444",
    "Adventure": "#f97316",
    "Animation": "#8b5cf6",
    "Children": "#38bdf8",
    "Comedy": "#eab308",
    "Crime": "#64748b",
    "Documentary": "#10b981",
    "Drama": "#f59e0b",
    "Fantasy": "#ec4899",
    "Film-Noir": "#475569",
    "Horror": "#dc2626",
    "Musical": "#d946ef",
    "Mystery": "#6366f1",
    "Romance": "#f43f5e",
    "Sci-Fi": "#06b6d4",
    "Thriller": "#0284c7",
    "War": "#78716c",
    "Western": "#d97706",
}


def get_accent_for_genres(genres: List[str]) -> str:
    """Returns primary accent color for a movie based on its genres."""
    for g in genres:
        if g in GENRE_ACCENTS:
            return GENRE_ACCENTS[g]
    return "#f59e0b"  # Default warm gold


async def fetch_media_details(
    movie_id: int,
    tmdb_id: Optional[int],
    title: str,
    year: Optional[int],
    genres: List[str],
    db: Session
) -> MediaDetails:
    """
    Retrieves media details for a movie from cache, TMDB, or fallback.
    """
    accent = get_accent_for_genres(genres)

    if tmdb_id is not None and tmdb_id > 0:
        # Check database cache first
        cached = db.query(MediaCache).filter(MediaCache.tmdb_id == tmdb_id).first()
        if cached:
            cast_list = []
            if cached.cast_json:
                try:
                    cast_raw = json.loads(cached.cast_json)
                    cast_list = [CastMember(**c) for c in cast_raw]
                except Exception:
                    pass

            providers_list = []
            if cached.streaming_providers_json:
                try:
                    providers_list = json.loads(cached.streaming_providers_json)
                except Exception:
                    pass

            return MediaDetails(
                movieId=movie_id,
                tmdb_id=tmdb_id,
                title=title,
                poster_url=cached.poster_url,
                backdrop_url=cached.backdrop_url,
                overview=cached.overview,
                cast=cast_list,
                director=cached.director,
                trailer_key=cached.trailer_key,
                streaming_providers=providers_list,
                runtime=cached.runtime,
                vote_average=cached.vote_average,
                fallback_accent=accent,
            )

        # If TMDB API key is available, query TMDB API
        if api_settings.tmdb_api_key:
            url = f"{api_settings.tmdb_base_url}/movie/{tmdb_id}"
            params = {
                "api_key": api_settings.tmdb_api_key,
                "append_to_response": "credits,videos,watch/providers",
            }
            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        poster_path = data.get("poster_path")
                        poster_url = f"{api_settings.tmdb_image_base_url}{poster_path}" if poster_path else None

                        backdrop_path = data.get("backdrop_path")
                        backdrop_url = f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None

                        overview = data.get("overview")
                        runtime = data.get("runtime")
                        vote_avg = data.get("vote_average")

                        # Parse Cast
                        credits = data.get("credits", {})
                        cast_members = []
                        for c in credits.get("cast", [])[:5]:
                            cast_members.append(CastMember(name=c.get("name", ""), character=c.get("character", "")))

                        # Parse Director
                        director = None
                        for crew in credits.get("crew", []):
                            if crew.get("job") == "Director":
                                director = crew.get("name")
                                break

                        # Parse Trailer
                        trailer_key = None
                        for v in data.get("videos", {}).get("results", []):
                            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser"):
                                trailer_key = v.get("key")
                                break

                        # Parse Providers (US)
                        providers = []
                        us_prov = data.get("watch/providers", {}).get("results", {}).get("US", {})
                        for p in us_prov.get("flatrate", [])[:4]:
                            providers.append(p.get("provider_name", ""))

                        # Save to cache
                        cache_entry = MediaCache(
                            tmdb_id=tmdb_id,
                            poster_url=poster_url,
                            backdrop_url=backdrop_url,
                            overview=overview,
                            cast_json=json.dumps([c.model_dump() for c in cast_members]),
                            director=director,
                            trailer_key=trailer_key,
                            streaming_providers_json=json.dumps(providers),
                            runtime=runtime,
                            vote_average=vote_avg,
                            fetched_at=datetime.utcnow(),
                        )
                        db.merge(cache_entry)
                        db.commit()

                        return MediaDetails(
                            movieId=movie_id,
                            tmdb_id=tmdb_id,
                            title=title,
                            poster_url=poster_url,
                            backdrop_url=backdrop_url,
                            overview=overview,
                            cast=cast_members,
                            director=director,
                            trailer_key=trailer_key,
                            streaming_providers=providers,
                            runtime=runtime,
                            vote_average=vote_avg,
                            fallback_accent=accent,
                        )
            except Exception as e:
                logger.warning(f"Failed to fetch TMDB data for {tmdb_id}: {e}")

    # Fallback response (deterministic, rich typography representation)
    genre_str = ", ".join(genres) if genres else "Cinema"
    year_str = f" ({year})" if year else ""
    fallback_overview = f"A classic {genre_str} film{year_str} preserved in the MovieLens catalog archive with verified community ratings."

    return MediaDetails(
        movieId=movie_id,
        tmdb_id=tmdb_id,
        title=title,
        poster_url=None,
        backdrop_url=None,
        overview=fallback_overview,
        cast=[],
        director=None,
        trailer_key=None,
        streaming_providers=[],
        runtime=None,
        vote_average=None,
        fallback_accent=accent,
    )
