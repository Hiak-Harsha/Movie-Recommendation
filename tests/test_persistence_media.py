"""
Tests for Phase 3 (Persistence & User Accounts) and Phase 4 (Visuals & Media Integration).
Defects D7 & D8 verified.
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_user_creation_and_profile(client):
    # Create guest user
    resp = client.post("/api/users")
    assert resp.status_code == 200
    user_data = resp.json()
    assert "id" in user_data
    assert user_data["username"].startswith("Guest_")
    assert user_data["rating_count"] == 0
    assert user_data["watchlist_count"] == 0

    user_id = user_data["id"]

    # Get user profile
    resp2 = client.get(f"/api/users/{user_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == user_id


def test_ratings_crud(client):
    # Create user
    user_resp = client.post("/api/users", json={"username": "MovieBuff"})
    user_id = user_resp.json()["id"]

    # Submit rating for movieId 1 (Toy Story)
    r_resp = client.post(f"/api/users/{user_id}/ratings", json={"movieId": 1, "rating": 4.5})
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    assert r_data["movieId"] == 1
    assert r_data["rating"] == 4.5
    assert "Toy Story" in r_data["title"]

    # Update rating
    r_resp2 = client.post(f"/api/users/{user_id}/ratings", json={"movieId": 1, "rating": 5.0})
    assert r_resp2.status_code == 200
    assert r_resp2.json()["rating"] == 5.0

    # Retrieve ratings
    list_resp = client.get(f"/api/users/{user_id}/ratings")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["movieId"] == 1
    assert items[0]["rating"] == 5.0

    # Delete rating
    del_resp = client.delete(f"/api/users/{user_id}/ratings/1")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"

    # Verify empty
    list_resp2 = client.get(f"/api/users/{user_id}/ratings")
    assert len(list_resp2.json()) == 0


def test_watchlist_crud_and_csv_export(client):
    user_resp = client.post("/api/users")
    user_id = user_resp.json()["id"]

    # Add Inception (movieId 79132) to watchlist
    w_resp = client.post(
        f"/api/users/{user_id}/watchlist",
        json={"movieId": 79132, "notes": "Must rewatch in 4K"}
    )
    assert w_resp.status_code == 200
    w_data = w_resp.json()
    assert w_data["movieId"] == 79132
    assert "Inception" in w_data["title"]
    assert w_data["notes"] == "Must rewatch in 4K"

    # Get watchlist
    list_resp = client.get(f"/api/users/{user_id}/watchlist")
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["movieId"] == 79132

    # CSV Export
    csv_resp = client.get(f"/api/users/{user_id}/watchlist/export")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_content = csv_resp.text
    assert "MovieId,Title,Year,Genres,VoteAverage,VoteCount,AddedAt,Notes" in csv_content
    assert "79132" in csv_content
    assert "Inception" in csv_content
    assert "Must rewatch in 4K" in csv_content

    # Remove from watchlist
    del_resp = client.delete(f"/api/users/{user_id}/watchlist/79132")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "removed"

    # Verify empty
    list_resp2 = client.get(f"/api/users/{user_id}/watchlist")
    assert len(list_resp2.json()) == 0


def test_demo_profile_load_and_personalized_recommendations(client):
    user_resp = client.post("/api/users")
    user_id = user_resp.json()["id"]

    # Load Demo user #414 ratings
    load_resp = client.post(f"/api/users/demo/414/load/{user_id}")
    assert load_resp.status_code == 200
    assert load_resp.json()["status"] == "success"
    assert load_resp.json()["loaded_ratings"] > 0

    # Check that ratings were stored
    ratings_resp = client.get(f"/api/users/{user_id}/ratings")
    assert len(ratings_resp.json()) > 0

    # Request personalized recommendations for user
    rec_resp = client.get(f"/api/users/{user_id}/recommendations?top_n=5")
    assert rec_resp.status_code == 200
    rec_data = rec_resp.json()
    assert len(rec_data["recommendations"]) == 5
    assert rec_data["cold_start_tier"] == "full_pipeline"


def test_feedback_tracking(client):
    user_resp = client.post("/api/users")
    user_id = user_resp.json()["id"]

    fb_resp = client.post(
        f"/api/users/{user_id}/feedback",
        json={"movieId": 296, "interaction_type": "like"}
    )
    assert fb_resp.status_code == 200
    assert fb_resp.json()["status"] == "recorded"


def test_media_endpoints(client):
    # MovieId 1 (Toy Story, tmdbId 862)
    resp = client.get("/api/media/movie/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["movieId"] == 1
    assert "Toy Story" in data["title"]
    assert "overview" in data
    assert "fallback_accent" in data
    assert data["fallback_accent"].startswith("#")

    # Direct tmdbId query
    resp2 = client.get("/api/media/tmdb/862")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["tmdb_id"] == 862
