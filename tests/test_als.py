"""
Unit Tests for CineMatch Explicit ALS (Vectorized NumPy)
Tests:
  1. Fit time < 5.0 s on training ratings.
  2. Factor shapes and bias dimensions.
  3. Closed-form fold-in for new visitors.
  4. Isotonic calibration bounds [0.5, 5.0].
"""
import time
import pytest
import numpy as np
import pandas as pd

from ml.als import ExplicitALS


@pytest.fixture
def sample_ratings_df():
    """Generates synthetic rating matrix for 20 users and 30 items."""
    np.random.seed(42)
    rows = []
    for u in range(1, 21):
        rated_items = np.random.choice(range(1, 31), size=12, replace=False)
        for m in rated_items:
            r = float(np.random.choice([1.0, 2.0, 3.0, 4.0, 5.0]))
            rows.append({"userId": u, "movieId": m, "rating": r, "timestamp": 100000 + u * 10 + m})
    return pd.DataFrame(rows)


def test_als_fit_dimensions_and_speed(sample_ratings_df):
    als = ExplicitALS(factors=16, reg_f=1.0, reg_b=1.0, iterations=6)
    t0 = time.time()
    als.fit(sample_ratings_df)
    duration = time.time() - t0

    assert duration < 5.0, f"ALS fit took {duration:.2f}s, expected < 5.0s"
    assert als.is_fitted
    assert als.Q.shape == (30, 16)
    assert als.P.shape == (20, 16)
    assert als.bi.shape == (30,)
    assert als.bu.shape == (20,)


def test_als_closed_form_fold_in(sample_ratings_df):
    als = ExplicitALS(factors=16, reg_f=1.0, reg_b=1.0, iterations=6)
    als.fit(sample_ratings_df)

    # Test visitor with clear preference for items 1, 2, 3
    visitor_ratings = {1: 5.0, 2: 5.0, 3: 4.5}
    fold_in_res = als.fold_in_user(visitor_ratings)
    assert fold_in_res is not None
    b_new, p_new = fold_in_res
    assert isinstance(b_new, float)
    assert p_new.shape == (16,)

    preds = als.predict_for_user_ratings(visitor_ratings, candidate_movie_ids=[4, 5, 6])
    assert len(preds) == 3
    for mid, r in preds.items():
        assert 0.5 <= r <= 5.0


def test_als_empty_ratings_fails():
    als = ExplicitALS()
    with pytest.raises(ValueError):
        als.fit(pd.DataFrame(columns=["userId", "movieId", "rating"]))
