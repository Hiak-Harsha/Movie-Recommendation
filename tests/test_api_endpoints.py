"""
Unit Tests for CineMatch FastAPI Endpoints & Serving Engine
Tests:
  1. Lifespan artifact loading (< 3s).
  2. Typo-tolerant search with character match offsets.
  3. Precomputed similar movie lookups.
  4. Cold-start ladder rungs (0 ratings, 1-4 ratings, 5+ ratings).
  5. Structured explanation JSON format (computed facts only).
"""
import pytest
from fastapi.testclient import TestClient

from apps.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health_check_and_startup(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["is_loaded"] is True
    assert data["catalog_size"] > 9000
    assert data["startup_duration_seconds"] < 3.0


def test_search_typo_and_year_matching(client):
    # Test typo tolerance
    res1 = client.get("/api/search?q=matrx&limit=5")
    assert res1.status_code == 200
    results1 = res1.json()["results"]
    assert len(results1) > 0
    top_title1 = results1[0]["display_title"].lower()
    assert "matrix" in top_title1

    # Test year token parsing
    res2 = client.get("/api/search?q=matrix 1999&limit=5")
    assert res2.status_code == 200
    results2 = res2.json()["results"]
    assert results2[0]["year"] == 1999
    assert len(results2[0]["match_offsets"]) == 2


def test_similar_movies_lookup(client):
    # Toy Story (movieId: 1)
    res = client.get("/api/similar?movieId=1&top_n=10")
    assert res.status_code == 200
    data = res.json()
    assert data["seed_movie"]["movieId"] == 1
    assert len(data["similar_movies"]) == 10
    # Seed must not be in its own similar list
    similar_ids = [m["movieId"] for m in data["similar_movies"]]
    assert 1 not in similar_ids


def test_cold_start_ladder_tier_zero(client):
    """0 ratings -> Bayesian popularity baseline."""
    res = client.post("/api/recommendations", json={"user_ratings": {}, "top_n": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["cold_start_tier"] == "zero_ratings"
    assert len(data["recommendations"]) == 10
    assert data["recommendations"][0]["contributions"]["popularity"] > 0


def test_cold_start_ladder_tier_one(client):
    """1 to 4 ratings -> Content taste vector + popularity."""
    ratings = {"1": 5.0, "2": 4.0}
    res = client.post("/api/recommendations", json={"user_ratings": ratings, "top_n": 10})
    assert res.status_code == 200
    data = res.json()
    assert data["cold_start_tier"] == "content_fallback"
    assert len(data["recommendations"]) == 10
    rec_ids = [m["movieId"] for m in data["recommendations"]]
    assert 1 not in rec_ids and 2 not in rec_ids


def test_cold_start_ladder_tier_two_full_pipeline(client):
    """5+ ratings -> Full multi-signal hybrid with ALS fold-in."""
    ratings = {"1": 5.0, "2": 4.0, "260": 4.5, "296": 5.0, "318": 5.0, "356": 4.0, "593": 4.5, "2571": 5.0}
    res = client.post("/api/recommendations", json={"user_ratings": ratings, "top_n": 10, "diversity_lambda": 0.2})
    assert res.status_code == 200
    data = res.json()
    assert data["cold_start_tier"] == "full_pipeline"
    assert len(data["recommendations"]) == 10

    first_rec = data["recommendations"][0]
    # Verify structured explanations (not sentences)
    assert len(first_rec["signals"]) > 0
    assert isinstance(first_rec["signals"][0]["details"], dict)
    # Verify contributions
    contribs = first_rec["contributions"]
    assert "mf" in contribs and "content" in contribs


def test_demo_profiles_endpoint(client):
    res = client.get("/api/meta/demo-profiles")
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) > 0
    assert "userId" in profiles[0]
    assert "top_genres" in profiles[0]
