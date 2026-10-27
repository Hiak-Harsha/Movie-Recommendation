# CineMatch — Cinematic Rebuild

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.4+-black.svg)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.3+-61DAFB.svg)](https://react.dev)
[![Pytest](https://img.shields.io/badge/pytest-51%20passed-brightgreen.svg)](https://pytest.org)
[![Zero Overlap](https://img.shields.io/badge/playwright-zero%20overlap-brightgreen.svg)](https://playwright.dev)
[![License](https://img.shields.io/badge/license-Non--Commercial%20Research-lightgrey.svg)](https://grouplens.org/datasets/movielens/)

**CineMatch** is a movie recommendation experience rebuilt as a scroll-driven cinema. The dashboard emerges dynamically from the page across a 700vh pinned stage, moving all technical and algorithmic details behind a single About module.

---

## 1. Living Dashboard Experience (Scenes 00–06)

The interface appears and changes as you scroll through pinned scenes and animated transitions:

- **Scene 00 (0–100vh): Cinema Showcase & Wordmark**  
  5-column drifting poster wall with 3D perspective (`rotateX(8deg) rotateZ(-6deg)`), letterbox bars retracting over first 25vh, mask-rising CINEMATCH wordmark, and warm visitor copy.
- **Scene 01 (100–180vh): Search**  
  Poster wall rack-focuses (0 to 12px blur); central search under a projector-beam light cone with real film title typing effect (`/api/search`).
- **Scene 02 (180–300vh): Taste Profile**  
  18-poster onboarding grid with live progress ring; pick 5 films to calibrate your personal taste (`/api/onboarding/picks`, `/api/me/ratings`).
- **Scene 03 (300–440vh): Curated Shelves ("For You")**  
  Horizontal movie rows with plain-language reasons (*Because you liked Alien*, *Hidden gems in Sci-Fi*, *From a decade you love*) (`/api/me/shelves`).
- **Scene 04 (440–540vh): Tune**  
  Novelty, Diversity, and Era faders with midpoint threshold swaps and real-time reordering (`/api/me/recommendations`).
- **Scene 05 (540–620vh): Cinema Library**  
  Saved films formatted as cinema ticket stubs with perforated tear lines (`/api/me/watchlist`).
- **Scene 06 (620–700vh): Closing & Credits**  
  Closing scrub reveal and clean visitor footer with links to About, Data & Credits, and Terms.

---

## 2. Universal StageModule UX Contract

Every module implements strict isolation (`apps/web/src/modules/`):
- `search/` (01/ Search, `/api/search`)
- `taste/` (02/ Taste, `/api/onboarding/picks`, `/api/me/ratings`)
- `foryou/` (03/ For You, `/api/me/shelves`)
- `tune/` (04/ Tune, `/api/me/recommendations`)
- `library/` (05/ Library, `/api/me/watchlist`, `/api/me/export`, `DELETE /api/me`)
- `detail/` (Overlay route `/movie/[id]`, `/api/movies/[id]`)
- `about/` (About drawer with 5 tabs, `/api/about`)

---

## 3. Statistical Benchmark Report (Generated from Artifacts)

Evaluated across 591 test users and 20,706 held-out ratings with zero data leakage:

| Strategy | NDCG@10 | 95% Bootstrap CI | Recall@10 | Hit Rate | Novelty | Diversity |
|---|---|---|---|---|---|---|


**Active Serving Strategy**: `CineMatch Hybrid`

---

## 4. Quick Start

### Local Development
```bash
# 1. Start FastAPI backend (port 8000)
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000

# 2. Start Next.js web application (port 3000)
cd apps/web && npm run dev
```

### Run Tests & Verification
```bash
# Backend pytest suite (51 tests)
python -m pytest tests

# Verify session isolation between cookie jars
python scripts/verify_isolation.py

# Verify zero banned words in visitor surface copy
python scripts/check_copy.py

# Verify CSS toolchain & utilities
python scripts/check_utilities.py

# Verify zero cross-module import violations
python scripts/check_module_boundaries.py

# Verify zero hardcoded JSX literals
python scripts/check_jsx_literals.py

# Playwright zero-overlap test suite (8 viewports + zoom)
cd apps/web && npx playwright test
```

### Docker Compose
```bash
docker compose up --build
```
Access the application at `http://localhost:3000`.

---

## 5. Provenance & Citations

- **MovieLens**: F. Maxwell Harper and Joseph A. Konstan. 2015. The MovieLens Datasets: History and Context. ACM TiiS 5, 4, Article 19. Non-commercial, educational use only.
- **TMDB**: Movie metadata and posters provided by The Movie Database (TMDB). This product uses the TMDB API but is not endorsed or certified by TMDB.
