# CineMatch Implementation Plan & Phase 1 Audit

## 1. Environment & Tools Verification
- **Python Version:** 3.14.3
- **Streamlit Version:** 1.56.0 (supports `st.container(border=True, key=...)`, `st.fragment`, modern layout primitives)
- **Key Scientific Libraries:**
  - `numpy`: 2.4.4
  - `scipy`: 1.17.1 (sparse matrix computation, linear algebra)
  - `pandas`: 3.0.2
  - `scikit-learn`: 1.8.0
  - `pytest`: 9.1.1

## 2. Dataset Audit & File Evidence
- **Detected Dataset Version:** MovieLens `ml-latest-small` (generated September 26, 2018 by GroupLens Research)
- **Dataset Tier (§6):** Tier 1 (< 2,000,000 ratings). Total ratings = 100,836. Full in-memory computation, zero disk swapping required.
- **File Inventory:**
  - `movies.csv`: 9,742 rows, 3 columns (`movieId`, `title`, `genres`), 494,431 bytes. 0 nulls, 0 duplicate rows.
  - `ratings.csv`: 100,836 rows, 4 columns (`userId`, `movieId`, `rating`, `timestamp`), 2,483,723 bytes. 0 nulls, 0 duplicate rows. Scale: 0.5 to 5.0 (step 0.5).
  - `tags.csv`: 3,683 rows, 4 columns (`userId`, `movieId`, `tag`, `timestamp`), 118,660 bytes. 0 nulls, 0 duplicate rows.
  - `links.csv`: 9,742 rows, 3 columns (`movieId`, `imdbId`, `tmdbId`), 197,979 bytes. 8 nulls in `tmdbId`.
  - `README.txt`: 8,342 bytes.
  - `genome-scores.csv` & `genome-tags.csv`: **NOT PRESENT**. Dependent genome features are cleanly disabled and noted on Model Insights.

## 3. ID Consistency & Data Integrity Verification
- **Rating to Movie ID match:** 100% match. Exactly 0 orphan ratings (all 9,724 rated movie IDs exist in `movies.csv`).
- **Tag to Movie ID match:** 100% match. Exactly 0 orphan tags.
- **Unrated Movies:** 18 movies in `movies.csv` have zero ratings in `ratings.csv`.
- **Timestamp Ranges:**
  - Ratings: 828,124,615 (1996-03-29 18:36:55 UTC) to 1,537,799,250 (2018-09-24 14:27:30 UTC).
  - Tags: 1,137,179,352 (2006-01-13) to 1,537,098,603 (2018-09-16).
- **Duplicate Titles:** 10 titles appear more than once with distinct `movieId`s (e.g. remakes/same titles). `movieId` is strictly enforced as the primary key.

## 4. Algorithm Candidates to Compare & Implement
1. **Baselines:**
   - Uniform Random baseline
   - Bayesian Popularity baseline ($m$ at 80th percentile of training rating counts, global mean $C$)
2. **Content-Based Model:**
   - Multi-block feature representation: Atomic genres (`sci_fi`, `film_noir`), decade token, and cleaned atomic user tags (`min_df`, `sublinear_tf`).
   - Sparse cosine similarity on normalized TF-IDF representations.
   - User taste vector: $u = \sum (r_i - \bar{r}_u) \cdot x_i$ normalized; cosine against candidate movies.
3. **Collaborative Filtering Candidates (NumPy/SciPy):**
   - Candidate A: Item-kNN with adjusted cosine / mean centering, minimum co-raters, and shrinkage $s \cdot \frac{n_{ij}}{n_{ij} + \lambda}$.
   - Candidate B: Biased Matrix Factorization (ALS / SGD in pure NumPy/SciPy on observed ratings only): $\hat{r} = \mu + b_u + b_i + p_u \cdot q_i$.
   - Fold-in for custom/new visitors: Closed-form ridge regression $p_u = (Q_I^T Q_I + \lambda I)^{-1} Q_I^T (r - \mu - b_i)$.
4. **Hybrid Ranker:**
   - Tuned blend of Content, Collaborative, and Popularity signals.
   - Pool-independent score normalization (avoiding rank shifts when filtering).
   - Dynamic weight re-normalization for cold-start fallbacks.
   - Model selection gate: Compare validation NDCG@10. If hybrid does not beat the best single component on validation, ship the best single component and state so transparently.

## 5. Risk Assessment & Mitigations
- **Risk 1: Evaluation Leakage.** Future tags or future ratings leaking into vocabulary, popularity, or item similarities.
  - *Mitigation:* Strict temporal cutoffs (Train 70% / Val 10% / Test 20%). Tags with `timestamp >= cutoff` and ratings `>= cutoff` are strictly excluded from model fitting, vocab, and priors. Automated leakage tests with sentinel data.
- **Risk 2: XSS in user tags/titles.** MovieLens tags contain arbitrary user-entered strings.
  - *Mitigation:* Comprehensive HTML escaping helper for all dynamic text.
- **Risk 3: UI reruns on clicks.** Recomputing heavy models on simple watchlist clicks.
  - *Mitigation:* Cached model artifacts, `st.fragment`, and `on_click` callbacks with session state IDs.
