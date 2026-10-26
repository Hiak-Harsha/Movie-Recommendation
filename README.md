# CineMatch v2 — Production Movie Recommendation Workspace

![Python 3.14](https://img.shields.io/badge/python-3.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135+-009688.svg)
![Next.js](https://img.shields.io/badge/Next.js-16.4+-black.svg)
![React](https://img.shields.io/badge/React-19.3+-61DAFB.svg)
![Tests](https://img.shields.io/badge/pytest-47%20passed-brightgreen.svg)
![License](https://img.shields.io/badge/license-Research%20%26%20Dev-lightgrey.svg)

**CineMatch v2** is a production-grade movie recommendation intelligence workspace. It bridges machine learning rigor and studio-grade interactive dynamics—combining vectorized explicit ALS matrix factorization, shrunk Item-kNN co-ratings, TF-IDF content vectors, persistent SQLite user accounts, TMDB media integration, and an editorial Next.js web application built with GSAP and Lenis smooth scrolling.

---

## 1. System Architecture

```text
CineMatch/
├── apps/
│   ├── api/                    # Production FastAPI backend (lifespan artifact loading)
│   │   ├── config.py           # pydantic-settings environment configuration
│   │   ├── database.py         # SQLAlchemy 2.0 SQLite engine & sessions
│   │   ├── models.py           # User, Rating, Watchlist, Feedback, MediaCache ORM models
│   │   ├── schemas.py          # Pydantic v2 request & response schemas
│   │   ├── engine.py           # ServingEngine: O(1) candidate generation, fold-in & ranking
│   │   ├── media.py            # TMDB API client, SQLite cache & typographic poster fallbacks
│   │   └── main.py             # REST endpoints (Search, Similar, Recs, Users, Watchlist, Media)
│   └── web/                    # Next.js 16 App Router + TypeScript + Tailwind v4
│       ├── src/
│       │   ├── app/            # App Router: layout, globals.css, page.tsx
│       │   ├── components/     # Navbar, HeroWordmark, MarqueeTicker, PinnedStudioWorkflow,
│       │   │                   # MovieCard, MovieDetailModal, SearchModal
│       │   │   └── views/      # ForYouView, DiscoverView, SimilarView, WatchlistView, InsightsView
│       │   └── lib/            # Zustand global state store & query providers
│       ├── package.json        # Dependencies: GSAP, Lenis, Motion, TanStack Query, Zustand
│       └── next.config.ts      # Webpack bundler & package transpilation config
├── packages/
│   └── api-client/             # Strongly-typed API client generated from OpenAPI
│       ├── src/schema.d.ts     # Auto-generated schemas (openapi-typescript)
│       └── src/index.ts        # Typed CineMatchClient class with error handling
├── ml/                         # Offline ML training, artifact generation & evaluation CLI
│   ├── als.py                  # Vectorized explicit ALS in NumPy with isotonic calibration
│   ├── knn.py                  # Shrunk Item-kNN co-rating correlation
│   ├── content.py              # Multi-block atomic TF-IDF content features
│   ├── popularity.py           # Bayesian weighted rating & log-scaled popularity
│   ├── hybrid.py               # Candidate union, feature extraction & blend ranking
│   ├── build_artifacts.py      # Artifact compilation CLI -> artifacts/<fingerprint>/
│   ├── evaluation.py           # 591-user temporal holdout evaluation & bootstrap CIs
│   └── report.py               # Markdown evaluation report generator (docs/eval_report.md)
├── artifacts/<fingerprint>/    # Versioned precomputed model artifacts
│   ├── catalog.parquet         # Enriched catalog with search keys & parsed titles
│   ├── item_factors.npy        # ALS latent factor matrix Q (9,742 x 32)
│   ├── item_bias.npy           # Item biases b_i (9,742,)
│   ├── knn_idx.npy             # Top-100 precomputed Item-kNN indices
│   ├── knn_sim.npy             # Top-100 Item-kNN shrunk similarities
│   ├── content_idx.npy         # Top-100 TF-IDF cosine neighbor indices
│   ├── tfidf.npz               # Sparse CSR feature matrix (9,742 x 1,349)
│   ├── blend_model.joblib      # Fitted logistic regression blend model
│   ├── strategy.json           # Live quality gate strategy declaration
│   └── meta.json               # Dataset fingerprint & demo user profiles
├── docs/
│   ├── motion-spec.md          # getartcraft.com motion & typography audit
│   ├── eval_report.md          # Generated evaluation report
│   ├── openapi.json            # OpenAPI 3.1.0 schema specification
│   └── api.md                  # REST endpoint documentation
├── tests/                      # 47 unit & integration tests (100% green)
├── bench.py                    # Production latency & cold-start benchmark suite
└── requirements.txt            # Pinned Python dependencies
```

---

## 2. Measured Production Latency Benchmarks (`bench.py`)

All numbers were measured directly against the active test suite and server runtime:

| Benchmark Target | Section 2 Target | Measured Performance | Status |
|---|---|---|---|
| **API Cold Start from Artifacts** | `< 3.00 s` | **0.363 s** | **PASS** |
| **/search Latency (p95)** | `< 30.00 ms` | **23.45 ms** (p50: 6.21 ms) | **PASS** |
| **/similar Latency (p95)** | `< 40.00 ms` | **20.26 ms** (p50: 19.15 ms) | **PASS** |
| **/recommendations Latency (p95)** | `< 150.00 ms` | **71.45 ms** (p50: 60.04 ms) | **PASS** |

*(Tested with User #414 with 2,698 historical ratings on a standard developer machine)*.

---

## 3. Statistically Rigorous Evaluation (`artifacts/eval_results.json`)

To resolve **Defect D2** (which previously relied on 9–14 users), evaluation uses a **Per-User Temporal Holdout Protocol (70% train / 10% validation / 20% test)**:

- **Evaluated Test Users ($n$):** **591 users** (exceeding the $n \ge 300$ requirement).
- **Held-out Test Rating Pairs:** **20,706 pairs**.
- **Rating Prediction Error:** Test RMSE = **0.9389**, Test MAE = **0.7225**.
- **Relevant Threshold:** Rating $\ge 4.0$.

### Top-10 Recommendation Comparison (95% Bootstrap CIs over Users)

| Model | Architecture | Test NDCG@10 (95% CI) | Recall@10 | HitRate@10 | Novelty | Diversity |
|---|---|---|---|---|---|---|
| **Popularity Baseline** | Bayesian Prior | **0.0563** [0.048, 0.065] | 0.0390 | 27.8% | 6.08 | 0.852 |
| **CineMatch Hybrid (v2)** | Multi-Signal Blend | **0.0409** [0.033, 0.048] | 0.0304 | 21.5% | 6.63 | 0.853 |
| **Explicit ALS** | 32-Factor MF | **0.0406** [0.033, 0.048] | 0.0298 | 23.2% | 6.72 | 0.851 |
| **Item-kNN** | Shrunk Cosine | **0.0126** [0.008, 0.017] | 0.0099 | 8.8% | 7.77 | 0.871 |
| **Content TF-IDF** | Atomic Vector Cosine | **0.0046** [0.002, 0.007] | 0.0040 | 3.4% | 8.32 | 0.824 |
| **Random Baseline** | Uniform Stochastic | **0.0009** [0.000, 0.002] | 0.0011 | 1.0% | 11.23 | 0.895 |

### Cold-Start Performance Ladder (Metrics vs. $k$ Prior Ratings)

| Prior Ratings ($k$) | Active Cold-Start Strategy | NDCG@10 | HitRate@10 | Recall@10 |
|---|---|---|---|---|
| **$k = 0$** | Tier 0: Bayesian Weighted Popularity | 0.0509 | 31.0% | 0.0416 |
| **$k = 3$** | Tier 1: Content Taste Vector + Prior | 0.0029 | 3.0% | 0.0027 |
| **$k = 5$** | Tier 2: Closed-Form ALS Fold-In | 0.0381 | 21.0% | 0.0275 |
| **$k = 10$** | Tier 2: Closed-Form ALS Fold-In | 0.0412 | 22.0% | 0.0301 |
| **$k = 20$** | Tier 2: Closed-Form ALS Fold-In | 0.0425 | 23.0% | 0.0315 |

---

## 4. Defect Fixes Summary (D1 – D10)

| ID | Issue Identified | Resolution in CineMatch v2 |
|---|---|---|
| **D1** | Reference ignored (Streamlit limitation) | Replaced Streamlit with Next.js 16 + GSAP, Lenis, per-letter wordmark, 45px/s marquee, and pinned studio workflow. |
| **D2** | Evaluation on 9–14 users | Rebuilt with primary per-user temporal holdout: **591 evaluated users**, 20,706 test pairs, 95% bootstrap CIs. |
| **D3** | Conflicting documentation metrics | All docs and UI tables are script-generated from `eval_results.json` (`make report`). |
| **D4** | Quality gate not wired to runtime | Quality gate outputs `artifacts/<fp>/strategy.json`. Serving strategy is verified at API startup and exposed to UI. |
| **D5** | Uncalibrated linear blend | Replaced arbitrary weights with logistic regression blend and isotonic rating calibration on validation period. |
| **D6** | 16s cold fit & 0.5s per request | Replaced with pure NumPy vectorized ALS (2.4s fit) and precomputed top-100 neighbor tables (< 0.04s per request). |
| **D7** | No persistence or accounts | Built SQLite persistence with SQLAlchemy 2.0: user sessions, ratings, watchlists, notes, feedback, and CSV export. |
| **D8** | No real visuals (typographic only) | Added TMDB proxy integration with SQLite caching for posters, backdrops, cast, trailers, and streaming providers. |
| **D9** | Dataset licensing compliance | Clarified research & development use of ml-latest-small; cited Harper and Konstan (2015). |
| **D10** | Hardcoded personal paths in logs | Converted all paths to relative paths via `pydantic-settings`; demo profiles are computed dynamically from data. |

---

## 5. Quickstart & Running Locally

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Build Artifacts & Verify Evaluated Models
```bash
python -m ml.build_artifacts
python -m ml.evaluation
```

### Step 3: Run Tests & Latency Benchmarks
```bash
python -m pytest -q
python bench.py
```

### Step 4: Run FastAPI Backend
```bash
python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

### Step 5: Run Next.js Web Studio
```bash
cd apps/web
npm install
npm run dev
```
Open **`http://localhost:3000`** in your browser.

---

## 6. Citation

```bibtex
@article{harper2015movielens,
  title={The MovieLens Datasets: History and Context},
  author={Harper, F. Maxwell and Konstan, Joseph A.},
  journal={ACM Transactions on Interactive Intelligent Systems (TiiS)},
  volume={5},
  number={4},
  pages={1--19},
  year={2015},
  publisher={ACM New York, NY, USA}
}
```
