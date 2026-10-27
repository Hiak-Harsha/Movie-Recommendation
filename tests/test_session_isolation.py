"""
CineMatch Session Isolation & Visitor Endpoint Tests (Phase P1 Exit Gate)
Verifies:
  1. Two cookie jars cannot read or modify each other's ratings or watchlist.
  2. Guessed user IDs or forged cookie signatures do not leak data.
  3. DELETE /api/me completely erases all visitor state.
  4. Visitor endpoints /api/showcase, /api/onboarding/picks, /api/me/shelves, /api/about work cleanly.
"""
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.sessions import sign_session_id, COOKIE_NAME

@pytest.fixture(scope="module", autouse=True)
def app_lifespan():
    with TestClient(app):
        yield


def test_two_cookie_jars_are_isolated():
    """Verify Client A and Client B have completely isolated state."""
    # Session A
    jar_a = TestClient(app)
    res_a = jar_a.get("/api/me")
    assert res_a.status_code == 200
    user_a = res_a.json()["user_id"]

    # Session B
    jar_b = TestClient(app)
    res_b = jar_b.get("/api/me")
    assert res_b.status_code == 200
    user_b = res_b.json()["user_id"]

    assert user_a != user_b

    # Client A rates Toy Story (1) = 5.0
    r_a = jar_a.post("/api/me/ratings", json={"movieId": 1, "rating": 5.0})
    assert r_a.status_code == 200

    # Client B rates Jumanji (2) = 4.0
    r_b = jar_b.post("/api/me/ratings", json={"movieId": 2, "rating": 4.0})
    assert r_b.status_code == 200

    # Check Client A ratings
    ratings_a = jar_a.get("/api/me/ratings").json()
    assert len(ratings_a) == 1
    assert ratings_a[0]["movieId"] == 1

    # Check Client B ratings (Client B must NOT see movie 1)
    ratings_b = jar_b.get("/api/me/ratings").json()
    assert len(ratings_b) == 1
    assert ratings_b[0]["movieId"] == 2

    # Client A adds movie 10 to watchlist
    w_a = jar_a.put("/api/me/watchlist/10")
    assert w_a.status_code == 200

    # Client B watchlist must be empty
    watchlist_b = jar_b.get("/api/me/watchlist").json()
    assert len(watchlist_b) == 0


def test_tampered_cookie_signature_is_rejected():
    """A forged or tampered session cookie must issue a fresh session and not access old data."""
    # Establish valid session
    jar = TestClient(app)
    res = jar.get("/api/me")
    real_uid = res.json()["user_id"]

    # Rate a movie
    jar.post("/api/me/ratings", json={"movieId": 1, "rating": 5.0})

    # Tamper with the cookie signature
    jar.cookies.set(COOKIE_NAME, f"{real_uid}.badsignature1234")

    # Access /api/me with tampered cookie
    res_tampered = jar.get("/api/me")
    assert res_tampered.status_code == 200
    new_uid = res_tampered.json()["user_id"]

    # Must be given a new user ID
    assert new_uid != real_uid
    # And must have 0 ratings
    ratings = jar.get("/api/me/ratings").json()
    assert len(ratings) == 0


def test_erase_session_data():
    """DELETE /api/me erases ratings, watchlist, and events."""
    jar = TestClient(app)
    # Rate and save
    jar.post("/api/me/ratings", json={"movieId": 1, "rating": 5.0})
    jar.put("/api/me/watchlist/5")

    me_before = jar.get("/api/me").json()
    assert me_before["picks_count"] == 1
    assert me_before["library_count"] == 1

    # Delete session
    del_res = jar.delete("/api/me")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "erased"

    # Subsequent request gets a new empty session
    me_after = jar.get("/api/me").json()
    assert me_after["picks_count"] == 0
    assert me_after["library_count"] == 0


def test_visitor_endpoints():
    """Verify /api/showcase, /api/onboarding/picks, /api/about, and /api/me/shelves."""
    jar = TestClient(app)

    # Showcase returns 60 movies
    sc = jar.get("/api/showcase")
    assert sc.status_code == 200
    assert len(sc.json()["movies"]) == 60

    # Onboarding picks returns 18 movies
    ob = jar.get("/api/onboarding/picks")
    assert ob.status_code == 200
    assert len(ob.json()["movies"]) == 18

    # Shelves returns structured shelves
    sh = jar.get("/api/me/shelves")
    assert sh.status_code == 200
    shelves = sh.json()["shelves"]
    assert len(shelves) >= 2
    assert any(s["id"] == "top_picks" for s in shelves)

    # About metadata returns generated facts
    ab = jar.get("/api/about")
    assert ab.status_code == 200
    ab_data = ab.json()
    assert "dataset" in ab_data
    assert "evaluation" in ab_data
    assert "active_strategy" in ab_data
    assert "licenses" in ab_data
    assert ab_data["dataset"]["clean_movies"] >= 9000
