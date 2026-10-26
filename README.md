# CineMatch — Hybrid Movie Recommendation Workspace

![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56+-FF4B4B.svg)
![Tests](https://img.shields.io/badge/pytest-30%20passed-brightgreen.svg)
![Dataset](https://img.shields.io/badge/MovieLens-ml--latest--small-orange.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

**CineMatch** is an end-to-end, workflow-driven movie recommendation workspace. It replaces opaque black-box recommenders with a transparent multi-signal engine, evidence-backed explanations, zero-leakage temporal evaluation, pure NumPy/SciPy collaborative filtering, and a focused studio interface.

---

## 1. Project Architecture

```text
Movie Recommendation/
├── app.py                      # Studio workspace navigation & page workflows
├── config.py                   # Centralized configuration, hyperparameters & paths
├── requirements.txt            # Pinned dependencies tested on Python 3.14
├── pytest.ini                  # Pytest configuration ignoring backups
├── README.md                   # System documentation & setup guide
├── PLAN.md                     # Initial project inspection & architecture plan
├── PROGRESS.md                 # Phase-by-phase execution log & verification checklist
├── .gitignore                  # Git exclusions
├── .streamlit/
│   └── config.toml             # Streamlit near-black theme & server options
├── artifacts/                  # Offline evaluation artifacts & cache
│   └── eval_results.json       # Evaluated metrics with 95% bootstrap CIs
├── data/                       # MovieLens dataset CSV files
│   ├── movies.csv              # 9,742 movie records (movieId, title, genres)
│   ├── ratings.csv             # 100,836 ratings across 610 users (0.5 to 5.0 stars)
│   ├── tags.csv                # 3,683 user-applied descriptive tags
│   ├── links.csv               # External identifiers (IMDb, TMDb)
│   └── README.txt              # GroupLens dataset metadata
├── src/
│   ├── __init__.py             # Package marker
│   ├── data_loader.py          # Schema validation, fingerprinting & DataHealthReport
│   ├── preprocessing.py        # Article-aware title parsing, atomic genres & Bayesian popularity
│   ├── content_model.py        # Multi-block TF-IDF features & user taste vector
│   ├── collaborative_model.py  # Pure NumPy/SciPy Item-kNN, Biased MF & closed-form fold-in
│   ├── hybrid_model.py         # Multi-signal ranker, pool-independent scaling & explanations
│   ├── evaluation.py           # Temporal split, bootstrap CIs & evaluation CLI
│   ├── styles.py               # Studio design system (near-black theme & layout)
│   └── ui_components.py        # Cards, typographic poster tiles, session state & watchlist
└── tests/
    ├── test_data_loader.py     # Schema validation, deduplication, title parsing & health report
    ├── test_recommendations.py # TF-IDF features, taste vector, seed exclusion & search
    ├── test_collaborative.py   # Item-kNN shrinkage, Biased MF SGD & fold-in
    ├── test_hybrid_model.py    # Blending, missing signal renormalization, filters & tie-breaking
    └── test_evaluation.py     # Metric correctness, sentinel leakage test & quality gate
```

---

## 2. Recommendation Pipeline & Mathematical Formulations

### A. Multi-Block Content Model & User Taste Vector (`src/content_model.py`)
- **Multi-Block Feature Representation:** Concatenates separate feature blocks horizontally:
  1. *Genre Block:* Atomic tokens (e.g. `sci_fi`, `film_noir`, `imax`) combined with release decade tokens (`decade_1990s`).
  2. *Tag Block:* Atomic multi-word tokens (e.g. `mind_bending`), deduplicated per `(user, movie, tag)` with sublinear TF scaling.
- **Retrieval:** Evaluates sparse cosine similarities $s = \frac{x_{\text{seed}} \cdot x_j}{\|x_{\text{seed}}\| \|x_j\|}$ using `scipy.sparse` matrix multiplication and top-$K$ candidate retrieval via `argpartition` (excluding seed).
- **User Taste Vector:** Incorporates directional user preference:
  $$u = \sum_{i \in \mathcal{I}_u} (r_i - \bar{r}_u) x_i$$
  Items rated below the user's mean push the taste vector away from those features. Candidates are scored via $\text{cosine}(u, x_j) \in [0, 1]$.

### B. Pure NumPy/SciPy Collaborative Filtering (`src/collaborative_model.py`)
Built entirely in standard NumPy and SciPy to eliminate third-party C-extension compilation issues:
- **Item-kNN with Significance Shrinkage:** Pairwise similarity with mean centering and shrinkage:
  $$s_{\text{shrunk}}(i, j) = s(i, j) \cdot \frac{n_{ij}}{n_{ij} + \lambda}$$
  where $n_{ij}$ is the number of co-raters and $\lambda = 5.0$.
- **Biased Matrix Factorization:** Explicit rating predictor trained via Stochastic Gradient Descent strictly on observed ratings:
  $$\hat{r}_{u, i} = \mu + b_u + b_i + p_u \cdot q_i$$
- **Closed-Form Fold-In for New Visitors:** For an active visitor with ratings $r_{\text{new}}$ across items with frozen factors $Q_I$ and biases $b_I$:
  $$p_{\text{new}} = (Q_I^T Q_I + \lambda_{\text{reg}} I)^{-1} Q_I^T (r_{\text{new}} - \mu - b_I)$$
  This provides low-latency collaborative scoring without full-model retraining.

### C. Bayesian Popularity Smoothing (`src/preprocessing.py`)
- Stabilizes ranking for items with few ratings using a Bayesian prior:
  $$WR = \left(\frac{v}{v + m}\right) R + \left(\frac{m}{v + m}\right) C$$
  where $m$ is the 80th percentile of training rating counts ($m = 12.0$), $C$ is the global training mean ($\approx 3.50$), and $v$ is item rating count.
- Scaled linearly to $[0, 1]$ via $\frac{WR - 0.5}{4.5}$.

### D. Hybrid Multi-Signal Ranking (`src/hybrid_model.py`)
- **Pool-Independent Normalization:** Content cosine is naturally in $[0, 1]$; collaborative rating predictions are linearly scaled $[0.5, 5.0] \to [0, 1]$; Bayesian popularity is scaled to $[0, 1]$.
- **Dynamic Weight Renormalization:** When a signal is unavailable (e.g. visitor has $< 5$ ratings), the missing signal is excluded and weights are dynamically renormalized:
  $$\text{score} = \frac{\sum_{s \in \mathcal{S}_{\text{avail}}} w_s \cdot s_s}{\sum_{s \in \mathcal{S}_{\text{avail}}} w_s}$$
  Missing signals are **never** treated as zeros.
- **Deterministic Tie-Breaking:** Sorted deterministically by $(-\text{score}, \text{movieId})$.
- **Factual Explanations:** Explanations cite only computed facts: overlapping genre tokens, top matching community tags, nearest neighbor co-raters, and predicted stars.

---

## 3. Reproduction & CLI Commands

### 1. Installation
Clone or navigate into the repository:
```bash
cd "c:\Users\madha\Desktop\Movie Recommendation"
```
Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run the Offline Evaluation CLI
Run the leakage-free temporal split evaluation:
```bash
python -m src.evaluation --protocol temporal --seed 42
```
This produces `artifacts/eval_results.json` containing 95% bootstrap confidence intervals for all compared models.

### 3. Run the Automated Test Suite
Execute the 30 unit tests across the test suite:
```bash
python -m pytest -v -q
```
*Result: 30 passed in ~54s.*

### 4. Launch the Web Application
Start CineMatch:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 4. Offline Evaluation Benchmark & Quality Gate

### Protocol Specifications
- **Primary Protocol:** Per-user temporal holdout (70% train / 10% validation / 20% test).
- **Statistical Power:** **591 evaluated users** (with $\ge 1$ relevant item with rating $\ge 4.0$) across **20,706 held-out test pairs**.
- **Data Leakage Sentinel:** All IDF vocabularies, tag dictionaries, popularity priors, and user/item factors are computed strictly from pre-cutoff data.

### Test Split Results (with 95% Bootstrap Confidence Intervals)

| Recommender Pipeline | Test NDCG@10 (95% CI) | Test Recall@10 (95% CI) | Test HitRate@10 (95% CI) | Catalog Coverage | Evaluated Users ($n$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Random Baseline** | **0.0015** `[0.0005, 0.0026]` | `0.0007` `[0.0001, 0.0015]` | `1.4%` `[0.5%, 2.4%]` | `45.5%` | 591 |
| **Popularity Baseline** | **0.0596** `[0.0496, 0.0692]` | `0.0347` `[0.0275, 0.0410]` | `28.8%` `[24.9%, 32.1%]` | `0.5%` | 591 |
| **Content-Only** | **0.0047** `[0.0024, 0.0070]` | `0.0018` `[0.0009, 0.0028]` | `3.4%` `[1.9%, 5.1%]` | `25.9%` | 591 |
| **Item-kNN CF** | **0.0130** `[0.0097, 0.0162]` | `0.0085` `[0.0054, 0.0118]` | `9.0%` `[6.8%, 11.0%]` | `6.0%` | 591 |
| **Explicit ALS** | **0.0437** `[0.0362, 0.0500]` | `0.0254` `[0.0210, 0.0304]` | `24.2%` `[20.6%, 27.4%]` | `4.8%` | 591 |
| **CineMatch Hybrid** | **0.0418** `[0.0331, 0.0502]` | `0.0304` `[0.0235, 0.0372]` | `21.8%` `[17.9%, 24.4%]` | `3.4%` | 591 |

### Collaborative Rating Prediction Accuracy
- **Test RMSE:** `0.9389` across 20,706 held-out test pairs
- **Test MAE:** `0.7225` across 20,706 held-out test pairs

### Quality Gate Outcome
- **Selected Model:** `Popularity Baseline`
- **Quality Gate Rule:** If the hybrid model does not exceed the best single component on validation NDCG@10, the system ships the best single model and honestly discloses it.
- **Validation Outcome:** Quality Gate Notice: Single model 'Popularity Baseline' (0.0433) achieved highest validation NDCG@10 over Hybrid (0.0393). Shipping 'Popularity Baseline'.

---

## 5. Studio Workspaces & UI Design

Inspired by process-oriented studio tools, CineMatch features a dark aesthetic (`#0b0b0c` background, subtle borders, amber accents) with numbered workflow stages (`01 Choose · 02 Tune · 03 Review`):

1. **01 / Discover:** Title search with live suggestions, computed ticker strip showing top genres and Bayesian classics, and navigation cards to all studios.
2. **02 / Similar Movies:** Seed movie selection with metadata summary, multi-block TF-IDF similarity, genre/year filters, and "Use as new seed" exploration chaining.
3. **03 / For You:** Interactive profile builder (search & rate, sample MovieLens profiles), cold-start evidence meter (Low / Medium / High), transparent fallback explanations, and signal mix sliders.
4. **04 / Watchlist:** Session-managed discovery queue with card removal and one-click CSV export. Built using `st.fragment` to avoid page recalculations.
5. **05 / Model Insights:** Comprehensive audit displaying DataHealthReport, dataset fingerprint (`273669b6fe1540a4`), split date boundaries, benchmark metrics table with 95% CIs, and the quality gate report.

---

## 6. Known Limitations & Next 3 Improvements

### Known Limitations
1. **Metadata Depth:** `ml-latest-small` contains only genres and user tags; `genome-scores.csv` is absent. Content similarity relies on atomic genre tokens and community tags rather than cast, director, or plot summaries.
2. **Matrix Sparsity:** With 100,836 ratings over 9,724 movies (sparsity $98.3\%$), collaborative scoring for obscure films with few co-raters yields wider confidence intervals.
3. **Session Watchlist:** Custom ratings and saved watchlist items are preserved in memory during the browser session.

### Next 3 High-Value Improvements
1. **Vector Embeddings via Sentence-Transformers:** Generate dense semantic embeddings of tags and movie titles for enhanced zero-shot semantic search.
2. **Implicit Feedback Optimization (BPR-MF):** Implement Bayesian Personalized Ranking on implicit interaction signals (clicks, watchlist additions) to optimize ranking over rating prediction.
3. **Persistent SQLite Backend:** Replace session-state storage with a lightweight local SQLite database to persist custom user ratings and watchlists across browser restarts.
