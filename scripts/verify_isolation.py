"""
Verification script for Phase P1 Exit Gate:
Demonstrates two distinct cookie jars (clients) connecting to the live API,
verifying that their ratings, watchlists, and sessions are completely isolated.
"""
import urllib.request
import urllib.error
import http.cookiejar
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def create_client():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    return opener

def request_json(opener, path, method="GET", data=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"} if data else {}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with opener.open(req) as resp:
        return resp.getcode(), json.loads(resp.read().decode("utf-8"))

def main():
    print("--- CineMatch Phase P1 Session Isolation Verification ---")
    
    # 1. Initialize Client Alpha
    alpha = create_client()
    _, me_a = request_json(alpha, "/api/me")
    uid_a = me_a["user_id"]
    print(f"[Client Alpha] Connected, session user_id: {uid_a}")

    # 2. Initialize Client Beta
    beta = create_client()
    _, me_b = request_json(beta, "/api/me")
    uid_b = me_b["user_id"]
    print(f"[Client Beta]  Connected, session user_id: {uid_b}")

    assert uid_a != uid_b, "Error: User IDs must be distinct!"
    print("[PASS] User IDs are distinct random UUIDs.")

    # 3. Client Alpha rates Movie 1 (Toy Story) with 5.0 stars
    _, rate_a = request_json(alpha, "/api/me/ratings", method="POST", data={"movieId": 1, "rating": 5.0})
    print(f"[Client Alpha] Rated movieId 1 -> {rate_a['rating']} stars")

    # 4. Client Beta rates Movie 2 (Jumanji) with 4.5 stars
    _, rate_b = request_json(beta, "/api/me/ratings", method="POST", data={"movieId": 2, "rating": 4.5})
    print(f"[Client Beta]  Rated movieId 2 -> {rate_b['rating']} stars")

    # 5. Client Alpha saves Movie 10 to watchlist
    request_json(alpha, "/api/me/watchlist/10", method="PUT")
    print("[Client Alpha] Saved movieId 10 to watchlist")

    # 6. Verify Isolation
    _, ratings_a = request_json(alpha, "/api/me/ratings")
    _, ratings_b = request_json(beta, "/api/me/ratings")
    _, watchlist_a = request_json(alpha, "/api/me/watchlist")
    _, watchlist_b = request_json(beta, "/api/me/watchlist")

    print("\n--- Cross-Check State ---")
    print(f"[Client Alpha] Ratings: {[r['movieId'] for r in ratings_a]} | Watchlist: {[w['movieId'] for w in watchlist_a]}")
    print(f"[Client Beta]  Ratings: {[r['movieId'] for r in ratings_b]} | Watchlist: {[w['movieId'] for w in watchlist_b]}")

    assert len(ratings_a) == 1 and ratings_a[0]["movieId"] == 1, "Alpha ratings mismatch"
    assert len(ratings_b) == 1 and ratings_b[0]["movieId"] == 2, "Beta ratings mismatch"
    assert len(watchlist_a) == 1 and watchlist_a[0]["movieId"] == 10, "Alpha watchlist mismatch"
    assert len(watchlist_b) == 0, "Beta watchlist must be empty!"

    print("\n[SUCCESS] Session isolation confirmed: Alpha and Beta cannot see or modify each other's data.")
    
    # 7. Test Erase
    print("\n--- Testing Erase Data (DELETE /api/me) ---")
    _, erase_res = request_json(alpha, "/api/me", method="DELETE")
    print(f"[Client Alpha] Data erased: {erase_res}")
    _, me_a_post = request_json(alpha, "/api/me")
    print(f"[Client Alpha] Post-erase new session picks_count: {me_a_post['picks_count']}, library_count: {me_a_post['library_count']}")
    assert me_a_post["picks_count"] == 0 and me_a_post["library_count"] == 0
    print("[SUCCESS] DELETE /api/me fully wipes user profile and issues fresh clean session.")

if __name__ == "__main__":
    main()
