# CineMatch — Hybrid Movie Recommendation Workspace

![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56+-FF4B4B.svg)
![Tests](https://img.shields.io/badge/pytest-21%20passed-brightgreen.svg)
![Dataset](https://img.shields.io/badge/MovieLens-ml--latest--small-orange.svg)

**CineMatch** is an end-to-end, workflow-driven movie recommendation workspace inspired by clean, process-oriented tools. It replaces generic black-box recommendations with a transparent hybrid recommendation pipeline, evidence-based explanations, zero-leakage offline evaluation, and a refined dark cinematic interface.

---

## 1. Architecture & Directory Structure

```text
Movie Recommendation/
├── app.py                      # Main Streamlit application shell & page workflows
├── config.py                   # Centralized configuration, paths, and hyperparameters
├── requirements.txt            # Dependency specifications
├── README.md                   # System documentation & setup guide
├── .gitignore                  # Git exclusions
├── .streamlit/
│   └── config.toml             # Streamlit dark cinematic theme & server options
├── data/                       # MovieLens dataset CSV files
│   ├── movies.csv              # 9,742 movie records (movieId, title, genres)
│   ├── ratings.csv             # 100,836 ratings across 610 users (0.5 to 5.0 stars)
│   ├── tags.csv                # 3,683 user-applied descriptive tags
│   ├── links.csv               # External identifiers (IMDb, TMDb)
│   └── README.txt              # Official GroupLens dataset metadata
├── src/
│   ├── __init__.py             # Package marker
│   ├── data_loader.py          # Flexible path resolution, schema validation & data health audit
│   ├── preprocessing.py       # Title release year extraction, genre normalization, Bayesian smoothing
│   ├── content_model.py        # TF-IDF vectorization, sparse cosine similarity, and search
│   ├── collaborative_model.py  # Item-Item Collaborative Filtering with mean centering & shrinkage
│   ├── hybrid_model.py         # Multi-signal ranker, candidate filtering, and cold-start fallback
│   ├── evaluation.py           # 80/20 per-user temporal split, Precision@10, Recall@10, RMSE/MAE
│   ├── styles.py               # Cinematic dark design system (custom CSS)
│   └── ui_components.py        # Reusable movie cards, session state manager & badge formatters
└── tests/
    ├── test_data_loader.py     # Schema integrity, missing paths, duplicate records, Bayesian smoothing
    ├── test_recommendations.py # Title search, seed movie exclusion, deterministic results, filters
    └── test_hybrid_model.py    # Score combination, cold-start fallback, already-rated exclusion, evaluation
```

---

## 2. Recommendation Algorithms & Mathematical Formulations

### A. Content-Based Filtering (`src/content_model.py`)
- **Feature Representation:** Builds a combined text corpus per movie using normalized genres (e.g. `sci_fi`, `film_noir`) and aggregated user tags.
- **Vectorization:** `TfidfVectorizer` transforms features into high-dimensional sparse representations with sublinear term-frequency scaling.
- **Retrieval:** Evaluates cosine similarity directly on sparse vectors via linear kernel dot products:
  $$\text{Sim}(v_{\text{seed}}, v_j) = \frac{v_{\text{seed}} \cdot v_j}{\|v_{\text{seed}}\| \|v_j\|}$$
  Avoids computing dense $N \times N$ similarity matrices.
- **Search:** Case-insensitive, multi-token fuzzy title search ranking exact matches, prefix matches, and token intersections.

### B. Item-Item Collaborative Filtering (`src/collaborative_model.py`)
- **Rating Prediction:** Operates on the sparse training rating matrix. Unobserved ratings are **never** treated as zeros.
- Given active user ratings $\mathcal{I}_u$ and user mean rating $\bar{r}_u$, the predicted preference for unrated candidate item $j$ is:
  $$\hat{r}_{u, j} = \bar{r}_u + \frac{\sum_{i \in \mathcal{I}_u, s(i, j) > 0} s_{\text{shrunk}}(i, j) \cdot (r_{u, i} - \bar{r}_u)}{\sum_{i \in \mathcal{I}_u, s(i, j) > 0} |s_{\text{shrunk}}(i, j)|}$$
- **Significance Shrinkage:** Down-weights item pairs with few co-raters to penalize low-confidence noise:
  $$s_{\text{shrunk}}(i, j) = s(i, j) \cdot \min\left(\frac{n_{i, j}}{\gamma}, 1.0\right)$$
  where $n_{i, j}$ is the number of co-raters and $\gamma = 5$.
- Normalized collaborative score: $\text{collab\_score} = \frac{\hat{r}_{u, j} - 0.5}{4.5} \in [0, 1]$.

### C. Bayesian Popularity Smoothing (`src/preprocessing.py`)
- Calculates a weighted rating to eliminate sample-size bias (e.g. movies with 1 rating of 5.0):
  $$\text{weighted\_rating} = \left(\frac{v}{v + m}\right) R + \left(\frac{m}{v + m}\right) C$$
  Where:
  - $R$ = average training rating of the movie
  - $v$ = count of training ratings for the movie
  - $m$ = prior weight threshold ($m = 10$)
  - $C$ = overall global mean training rating ($C \approx 3.50$)

### D. Hybrid Multi-Signal Ranking (`src/hybrid_model.py`)
- Combines normalized component scores:
  $$\text{hybrid\_score} = w_c \cdot S_{\text{content}} + w_{cf} \cdot S_{\text{collab}} + w_p \cdot S_{\text{pop}}$$
  Default weights: $w_c = 0.45, w_{cf} = 0.45, w_p = 0.10$.
- **Cold-Start Fallback:** When a visitor has $< 3$ ratings, the collaborative signal is unavailable. CineMatch transparently redistributes weights to Content ($0.75$) and Bayesian Popularity ($0.25$), displaying an honest notification badge explaining the fallback.
- **Candidate Filtering:** Explicitly filters out items already rated by the user and enforces optional genre and release-year bounds prior to top-$K$ ranking.

---

## 3. Reproduction & Setup Instructions

### Prerequisites
- Python 3.11, 3.12, 3.13, or 3.14.
- All dependencies run entirely locally with standard libraries (Pandas, SciPy, Scikit-learn, Streamlit). No external API key (TMDB or OpenAI) is required.

### Installation
Clone or navigate into the repository:
```bash
cd "c:\Users\madha\Desktop\Movie Recommendation"
```

Install the dependencies:
```bash
python -m pip install -r requirements.txt
```

### Dataset Placement
The dataset files are automatically detected from `data/` or `ml-latest-small/ml-latest-small/`. Ensure the following files exist:
- `data/movies.csv`
- `data/ratings.csv`
- `data/tags.csv`
- `data/links.csv`

### Running the Test Suite
Run the 21 automated unit tests:
```bash
python -m pytest -v
```

### Launching the Application
Start the Streamlit application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 4. Workspaces & Workflows

1. **🧭 Discover:**
   - Quick search across 9,742 titles.
   - Bayesian top-rated classics ($m \ge 10$ prior smoothing).
   - One-click workflow routing to Similar Movies or Personalized recommendations.
2. **🎬 Similar Movies:**
   - Search and select any seed film.
   - Real-time TF-IDF content similarity ranking with genre and release year constraints.
   - Factual explanations detailing shared genres and matching community tags.
3. **✨ For You (Personalized Hybrid):**
   - Rate movies using an interactive 0.5–5.0 star selector, or load real MovieLens benchmark profiles (e.g., User #15, User #414, User #599, User #606).
   - View component score breakdowns (Content %, Collaborative predicted stars, Popularity %).
   - Fine-tune hybrid weights in real time with interactive sliders.
4. **📌 Watchlist:**
   - Save or remove titles during the discovery session.
   - Tracks session counts and average rating without broken links or placeholders.
5. **📊 Model Insights:**
   - Data health summary with null audits, duplicate checks, and unrated title analysis.
   - Evaluated metrics (Precision@10, Recall@10, Catalog Coverage, RMSE, MAE) computed strictly on held-out test data.

---

## 5. Offline Evaluation Protocol & Real Results

Evaluation protocol:
- **Split:** 80/20 per-user temporal split based on ratings timestamp. Earliest 80% used for training, latest 20% held out for evaluation.
- **Relevance:** Test ratings $\ge 4.0$ stars are treated as positive ground-truth items.

### Evaluated Results Summary
| Model Pipeline | Precision@10 | Recall@10 | Catalog Coverage | Evaluated Test Users |
| :--- | :--- | :--- | :--- | :--- |
| **Popularity Baseline** | 0.046 | 0.052 | 0.4% | 35 |
| **Content-Based Model** | 0.040 | 0.048 | 6.8% | 35 |
| **Collaborative Filtering** | 0.063 | 0.076 | 4.9% | 35 |
| **CineMatch Hybrid** | **0.069** | **0.082** | **7.4%** | 35 |

- **Collaborative Rating Prediction RMSE:** `0.887`
- **Collaborative Rating Prediction MAE:** `0.694`
*(Computed on held-out test ratings strictly without data leakage).*

---

## 6. Known Limitations & Next 3 Improvements

### Known Limitations
1. **Metadata Coverage:** MovieLens `ml-latest-small` does not provide plot summaries, cast lists, or director credits. CineMatch strictly bases content similarity on genres and user tags and avoids fabricating narrative plot themes.
2. **Matrix Sparsity:** With 100,836 ratings over 610 users and 9,724 rated movies (density $\approx 1.7\%$), very niche movies with few co-ratings rely primarily on content and Bayesian signals.
3. **Session Persistence:** Watchlists and custom ratings are maintained in memory within the current Streamlit browser session.

### Next 3 High-Value Improvements
1. **Lightweight Neural Embeddings (Two-Tower Model):** Train a dual-encoder architecture mapping user rating sequences and movie genre/tag tokens into a shared low-dimensional embedding space.
2. **Local Metadata Enrichment (TMDb / OMDB Integration):** Optional offline ingestion of director, cast, and poster art via TMDB API for users who provide an optional free API key.
3. **Session Persistence with SQLite:** Add a local SQLite database to persist custom user profiles and watchlists across multiple sessions without cloud accounts.
