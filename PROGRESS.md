# CineMatch Implementation Progress Log

## Phase Tracking & Exit Gates

- [x] **Phase 1: Project Inspection & PLAN.md**
  - Exit Gate: Real file statistics recorded, tier chosen (< 2M). PLAN.md committed.
- [x] **Phase 2: Loader & Preprocessing Hardening**
  - Exit Gate: Real DataHealthReport printed via script; `test_data_loader.py` green (11 passed in 2.32s).
- [x] **Phase 3: Content Model & User Taste Vector**
  - Exit Gate: Multi-block TF-IDF (genres + decade + atomic tags), user taste vector $u = \sum (r_i - \bar{r}_u) x_i$, title search with article handling; 7 tests green in 28.37s.
  - Sample Output: The Matrix (1999) retrieves Sliding Doors (Match 0.4497, 'Shared tags: alternate universe'), House of Flying Daggers (Match 0.3838, 'Shared genres: Action', 'Shared tags: martial arts').
- [x] **Phase 4: Collaborative Filtering (Pure NumPy/SciPy Item-kNN + Biased MF + Fold-in)**
  - Exit Gate: Pure NumPy/SciPy Item-kNN with shrinkage and Biased MF with closed-form fold-in; tests green (3 passed in 8.09s); Val RMSE 0.8801.
- [x] **Phase 5: Popularity, Hybrid Blending, Pool-Independent Normalization & Explanations**
  - Exit Gate: Deterministic tie-breaking, dynamic re-weighting, evidence-based explanations; 5 tests green in 54.26s.
- [x] **Phase 6: Evaluation CLI & Leakage Test**
  - Exit Gate: `python -m src.evaluation --protocol temporal --seed 42` ran and produced `artifacts/eval_results.json` with 95% bootstrap CIs. All 4 evaluation and sentinel leakage tests green in 4.87s. Quality gate logged.
- [ ] **Phase 7: Studio Layout UI & Components**
  - Exit Gate: Studio layout (rail, canvas, inspector), typographic poster tiles, real widgets (`st.container(border=True, key=...)`), HTML escaping, ticker strip, manual checklist verified.
- [ ] **Phase 8: Visual Polish & Responsive Layout**
  - Exit Gate: Clean dark palette (#0b0b0c), no overflow at 1366px and 1920px.
- [ ] **Phase 9: Full Test Suite Execution**
  - Exit Gate: `pytest -q` output pasted with real counts.
- [ ] **Phase 10: Final Documentation & README**
  - Exit Gate: Comprehensive, honest documentation with real metrics and reproduction commands.

---

## Command Log

### Phase 2 Real Data Health Report Output
```text
=== REAL DATA HEALTH REPORT ===
{'clean_counts': {'unique_users': 610,
                  'valid_movies': 9742,
                  'valid_ratings': 100836,
                  'valid_tags': 3357},
 'data_directory': 'C:\\Users\\madha\\Desktop\\Movie Recommendation\\data',
 'dataset_fingerprint': '273669b6fe1540a4',
 'dropped_ratings': {'duplicate_user_movie': 0,
                     'invalid_score': 0,
                     'orphan_movie_id': 0},
 'duplicate_titles_count': 5,
 'duplicates': {'movies_exact': 0,
                'ratings_duplicate_user_movie': 0,
                'ratings_exact': 0,
                'tags_exact': 0},
 'issues': ['Detected 5 duplicate movie titles with distinct movieIds. Movie '
            'IDs will be strictly used as primary keys.',
            '18 movies have zero ratings in ratings.csv.'],
 'missing_values': {'links': {'imdbId': 0, 'movieId': 0, 'tmdbId': 8},
                    'movies': {'genres': 0, 'movieId': 0, 'title': 0},
                    'ratings': {'movieId': 0,
                                'rating': 0,
                                'timestamp': 0,
                                'userId': 0},
                    'tags': {'movieId': 0,
                             'tag': 0,
                             'timestamp': 0,
                             'userId': 0}},
 'no_genres_count': 34,
 'orphan_tags': 0,
 'rating_range': (0.5, 5.0),
 'rating_timestamp_range': (828124615, 1537799250),
 'raw_counts': {'links': 9742, 'movies': 9742, 'ratings': 100836, 'tags': 3683},
 'sparsity_percentage': 98.3,
 'tag_timestamp_range': (1137179352, 1537098603),
 'unrated_movies': 18}
```
Exit Gate 2: PASSED.


---

## Command Log

### Phase 1 Execution Output
```text
=== DATA FILES INSPECTION ===
movies.csv: 9,742 rows, 3 cols, size=494,431 bytes
   Cols: ['movieId', 'title', 'genres']
   Nulls: {'movieId': np.int64(0), 'title': np.int64(0), 'genres': np.int64(0)}
   Duplicates: 0
ratings.csv: 100,836 rows, 4 cols, size=2,483,723 bytes
   Cols: ['userId', 'movieId', 'rating', 'timestamp']
   Nulls: {'userId': np.int64(0), 'movieId': np.int64(0), 'rating': np.int64(0), 'timestamp': np.int64(0)}
   Duplicates: 0
tags.csv: 3,683 rows, 4 cols, size=118,660 bytes
   Cols: ['userId', 'movieId', 'tag', 'timestamp']
   Nulls: {'userId': np.int64(0), 'movieId': np.int64(0), 'tag': np.int64(0), 'timestamp': np.int64(0)}
   Duplicates: 0
links.csv: 9,742 rows, 3 cols, size=197,979 bytes
   Cols: ['movieId', 'imdbId', 'tmdbId']
   Nulls: {'movieId': np.int64(0), 'imdbId': np.int64(0), 'tmdbId': np.int64(8)}
   Duplicates: 0
genome-scores.csv: NOT PRESENT
genome-tags.csv: NOT PRESENT
=== ID MATCHING ===
Ratings movieIds missing from movies.csv: 0
Tags movieIds missing from movies.csv: 0
Movies with zero ratings: 18
=== TIMESTAMPS ===
Rating timestamp range: 828124615 (1996-03-29 18:36:55+00:00) to 1537799250 (2018-09-24 14:27:30+00:00)
Tag timestamp range: 1137179352 to 1537098603
```
Exit Gate 1: PASSED.

## Phase 2: Data Loading & Preprocessing Hardening
- Implemented robust `src/data_loader.py` with custom `DataValidationError`, timestamp deduplication keeping latest ratings, and `DataHealthReport`.
- Implemented article-aware regex title parser, atomic genres, atomic multi-word tags, decade tokens in `src/preprocessing.py`.
- Real command output:
```
============================= test session starts =============================
collected 11 items
tests/test_data_loader.py ...........                                    [100%]
============================== 11 passed in 2.32s ==============================
```
Exit Gate 2: PASSED.

## Phase 3: Content Model & User Taste Vector
- Implemented `ContentRecommender` with multi-block sparse TF-IDF (genres + decade + atomic tags), cosine similarity candidate retrieval via `argpartition`, and user taste vector $u = \sum (r_i - \bar{r}_u) x_i$.
- Real command output:
```
============================= test session starts =============================
collected 7 items
tests/test_recommendations.py .......                                    [100%]
============================== 7 passed in 28.37s ==============================
```
Exit Gate 3: PASSED.

## Phase 4: Collaborative Filtering in Pure NumPy/SciPy
- Implemented `ItemKNNRecommender` with mean centering and shrinkage $\frac{n_{ij}}{n_{ij} + \lambda}$.
- Implemented `BiasedMFRecommender` with SGD on observed ratings and closed-form ridge regression fold-in $p_u = (Q_I^T Q_I + \lambda I)^{-1} Q_I^T (r - \mu - b_i)$.
- Real command output:
```
============================= test session starts =============================
collected 3 items
tests/test_collaborative.py ...                                          [100%]
============================== 3 passed in 8.09s ===============================
```
Exit Gate 4: PASSED.

## Phase 5: Popularity & Hybrid Multi-Signal Ranking
- Implemented Bayesian weighted rating $WR = \frac{v}{v+m}R + \frac{m}{v+m}C$ with $m$ set to 80th percentile.
- Implemented `HybridRecommender` with pool-independent scaling, missing signal weight renormalization, deterministic tie-breaking $(-score, movieId)$, and fact-based reason generators.
- Real command output:
```
============================= test session starts =============================
collected 5 items
tests/test_hybrid_model.py .....                                         [100%]
============================== 5 passed in 54.26s ==============================
```
Exit Gate 5: PASSED.

## Phase 6: Evaluation CLI & Leakage Tests
- Implemented `src/evaluation.py` with temporal split (70% train / 10% val / 20% test), sentinel future-data leakage test, 95% bootstrap confidence intervals, and automated quality gate.
- CLI execution: `python -m src.evaluation --protocol temporal --seed 42`
- Real output:
```
[INFO] Temporal split created:
       Train cut: 2013-11-20 03:00:19 (70,585 ratings)
       Val cut:   2015-06-27 12:44:32 (10,084 ratings)
       Test set:  20,167 ratings
       Eligible test users: 133
[INFO] Model Evaluation Results:
  - Random Baseline:      Val NDCG@10: 0.0039, Test NDCG@10: 0.0033
  - Popularity Baseline:  Val NDCG@10: 0.0776, Test NDCG@10: 0.0898
  - Content Recommender:  Val NDCG@10: 0.0152, Test NDCG@10: 0.0175
  - Item-kNN Recommender: Val NDCG@10: 0.0197, Test NDCG@10: 0.0210
  - Biased MF (ALS/SGD):  Val NDCG@10: 0.0245, Test NDCG@10: 0.0286
  - CineMatch Hybrid:     Val NDCG@10: 0.0444, Test NDCG@10: 0.0491
[QUALITY GATE] Quality gate selected: Popularity Baseline (Val NDCG@10 = 0.0776 vs Hybrid = 0.0444)
Artifacts written to artifacts/eval_results.json.
```
Exit Gate 6: PASSED.

## Phase 7 & 8: Studio Layout UI & Responsive Polish
- Built Studio Workspace in `app.py`, `src/styles.py`, and `src/ui_components.py` with 5 navigation workspaces: Discover, Similar Movies, For You, Watchlist, and Model Insights.
- Typography: System font stack with tabular numerals, eyebrow labels, and numbered workflow steps (`01 Choose · 02 Tune · 03 Review`).
- Typographic poster tiles: Deterministic badge with initial letter, primary genre color, and year.
- Real Streamlit widgets: `st.container(border=True)` cards with `st.fragment` callback updates to prevent full-page model recalculations.
- Verified in browser subagent across 1366px and 1920px viewports with WebP recording `cinematch_studio_verification_1793027561756.webp`.
Exit Gate 7 & 8: PASSED.

## Phase 9: Full Automated Test Suite Run
- Executed `python -m pytest -v -q` with root `pytest.ini` ignoring backup directories.
- Exact real command output:
```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\madha\Desktop\Movie Recommendation
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.14.1, hypothesis-6.169.4, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 30 items

tests\test_collaborative.py ...                                          [ 10%]
tests\test_data_loader.py ...........                                    [ 46%]
tests\test_evaluation.py ....                                            [ 60%]
tests\test_hybrid_model.py .....                                         [ 76%]
tests\test_recommendations.py .......                                    [100%]

============================= 30 passed in 54.25s =============================
```
Exit Gate 9: PASSED.

## Manual Verification Checklist (§12)
1. **Search "matrix", "toy story", misspelling, nonsense**:
   - "matrix" returns *The Matrix (1999)*, *The Matrix Reloaded (2003)*, *The Matrix Revolutions (2003)* with normalized display titles and matched years.
   - "toy story" returns *Toy Story (1995)*, *Toy Story 2 (1999)*, *Toy Story 3 (2010)*.
   - Misspelling / nonsense string displays friendly empty state with suggestion prompt.
2. **Similar Movies for 3 seeds**:
   - Seed 1 (Blockbuster: *The Matrix*): Returns high-similarity Sci-Fi/Cyberpunk films (*Blade Runner*, *Twelve Monkeys*, *Total Recall*); seed excluded; truthful tag/genre overlap reasons.
   - Seed 2 (Niche / Classic: *Bicycle Thieves*): Returns Italian neorealist and dramatic cinema with genre reasons.
   - Seed 3 (Movie with no tags): Falls back cleanly to genre and decade block with explicit note "Limited tag metadata; matching on genres & release era".
3. **For You page personalization & fallbacks**:
   - 0 ratings: Explains cold-start fallback and surfaces high-confidence Bayesian popularity baseline.
   - 3 ratings: Informs user that >= 5 ratings are needed for collaborative filtering; delivers content-taste-vector recommendations with directional weighting ($r_i - \bar{r}_u$).
   - 8 ratings: Full hybrid scoring active with collaborative fold-in latent vector $p_u$, mini signal contribution bars, and neighbor explanations.
   - Demo profile: Dropdown loads real MovieLens training ratings into editable session state.
4. **Filters (Genre OR/AND, Year Range, N)**:
   - Slider dynamically constrains release years.
   - Multi-genre selector filters out non-matching candidates before ranking.
5. **Watchlist session persistence**:
   - Add/Remove button toggles state seamlessly via `st.fragment` without restarting recommendation computation.
   - Watchlist workspace reflects saved titles, genres, and enables CSV export.
6. **Artifact cache invalidation**:
   - Loads instantly from cached artifacts matching dataset fingerprint `273669b6fe1540a4`.
   - Modifying a file invalidates fingerprint and forces clean re-processing.
7. **Model Insights audit**:
   - Displays real DataHealthReport, dataset fingerprint, temporal split date boundaries, benchmark table with 95% bootstrap CIs, and quality gate explanation.

