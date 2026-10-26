"""
CineMatch Performance Benchmark CLI
Measures:
  1. API cold start from precomputed artifacts (< 3.0 s target).
  2. /search p50 and p95 latency (< 30 ms target).
  3. /similar p50 and p95 latency (< 40 ms target).
  4. /recommendations p50 and p95 latency for active users (< 150 ms target).
"""
import sys
import time
from pathlib import Path
import numpy as np
from fastapi.testclient import TestClient

from apps.api.main import app

def run_benchmarks():
    print("=" * 70)
    print("CINEMATCH v2 PERFORMANCE & LATENCY BENCHMARKS")
    print("=" * 70)

    with TestClient(app) as client:
        # 1. Startup & Health Check
        res = client.get("/health")
        assert res.status_code == 200, res.text
        data = res.json()
        cold_start = data["startup_duration_seconds"]
        cs_status = "PASS" if cold_start < 3.0 else "FAIL"
        print(f"[*] API Cold Start from Artifacts: {cold_start:.3f} s (Target: < 3.000 s) -> [{cs_status}]")

        # 2. /search latency
        queries = ["matrix", "toy story", "star wars", "godfather", "inception", "pulp fiction", "alien", "batman", "lord of the rings", "jurassic park"]
        search_lats = []
        for q in queries:
            t0 = time.perf_counter()
            resp = client.get(f"/api/search?q={q}&limit=10")
            dur = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            search_lats.append(dur)

        s_p50 = float(np.percentile(search_lats, 50))
        s_p95 = float(np.percentile(search_lats, 95))
        s_status = "PASS" if s_p95 < 30.0 else "FAIL"
        print(f"[*] /search Latency (10 queries): p50={s_p50:.2f} ms, p95={s_p95:.2f} ms (Target: < 30.00 ms) -> [{s_status}]")

        # 3. /similar latency
        seeds = [1, 2, 260, 296, 318, 356, 593, 2571, 2959, 4993]
        similar_lats = []
        for mid in seeds:
            t0 = time.perf_counter()
            resp = client.get(f"/api/similar?movieId={mid}&top_n=20")
            dur = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            similar_lats.append(dur)

        sim_p50 = float(np.percentile(similar_lats, 50))
        sim_p95 = float(np.percentile(similar_lats, 95))
        sim_status = "PASS" if sim_p95 < 40.0 else "FAIL"
        print(f"[*] /similar Latency (10 seeds): p50={sim_p50:.2f} ms, p95={sim_p95:.2f} ms (Target: < 40.00 ms) -> [{sim_status}]")

        # 4. /recommendations latency
        demo_resp = client.get("/api/meta/demo-profiles")
        profiles = demo_resp.json()
        u15 = next((p for p in profiles if p["userId"] == 15), profiles[0])
        ratings_135 = u15["ratings"]

        rec_lats = []
        for _ in range(15):
            t0 = time.perf_counter()
            resp = client.post(
                "/api/recommendations",
                json={
                    "user_ratings": ratings_135,
                    "top_n": 20,
                    "diversity_lambda": 0.15,
                    "novelty_boost": 0.05
                }
            )
            dur = (time.perf_counter() - t0) * 1000.0
            assert resp.status_code == 200
            rec_lats.append(dur)

        rec_p50 = float(np.percentile(rec_lats, 50))
        rec_p95 = float(np.percentile(rec_lats, 95))
        rec_status = "PASS" if rec_p95 < 150.0 else "FAIL"
        print(f"[*] /recommendations Latency (User #{u15['userId']} with {len(ratings_135)} ratings): p50={rec_p50:.2f} ms, p95={rec_p95:.2f} ms (Target: < 150.00 ms) -> [{rec_status}]")
        print("=" * 70)


if __name__ == "__main__":
    run_benchmarks()
