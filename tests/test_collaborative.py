"""
Unit tests for Pure NumPy/SciPy Collaborative Filtering (Item-kNN, Biased MF, Fold-in).
"""
import pytest
import numpy as np
import pandas as pd

from src.data_loader import load_raw_data, validate_and_clean_data
from src.collaborative_model import ItemKNNRecommender, BiasedMFRecommender, CollaborativeEngine


@pytest.fixture(scope="module")
def cf_data():
    """Loads and cleans dataset for collaborative filtering tests."""
    movies_raw, ratings_raw, tags_raw, links_raw, resolved_dir = load_raw_data()
    m_clean, r_clean, t_clean, l_clean, report = validate_and_clean_data(
        movies_raw, ratings_raw, tags_raw, links_raw, str(resolved_dir)
    )
    return r_clean


def test_item_knn_fit_and_predict(cf_data):
    """Verify Item-kNN fits and predicts valid rating bounded by [0.5, 5.0]."""
    knn = ItemKNNRecommender().fit(cf_data.head(5000))
    assert knn.is_fitted
    
    # Test user with 5 ratings
    u_ratings = {1: 5.0, 2: 4.0, 3: 3.5, 47: 4.5, 50: 5.0}
    pred, neighbor_info = knn.predict_rating_for_item(u_ratings, target_movie_id=260)
    if pred is not None:
        assert 0.5 <= pred <= 5.0


def test_biased_mf_fold_in_new_user(cf_data):
    """Verify closed-form fold-in ridge regression for new visitor."""
    mf = BiasedMFRecommender(factors=10, iterations=5).fit(cf_data.head(5000))
    assert mf.is_fitted

    u_ratings = {1: 5.0, 2: 4.0, 3: 3.5, 47: 4.5, 50: 5.0}
    fold_res = mf.fold_in_user(u_ratings)
    assert fold_res is not None
    b_new, p_new = fold_res
    assert isinstance(b_new, float)
    assert p_new.shape == (10,)

    preds = mf.predict_for_user_ratings(u_ratings, candidate_movie_ids=[260, 2571])
    assert len(preds) > 0
    for mid, r_hat in preds.items():
        assert 0.5 <= r_hat <= 5.0


def test_collaborative_engine_minimum_evidence(cf_data):
    """Verify collaborative engine enforces minimum rating threshold."""
    engine = CollaborativeEngine().fit(cf_data.head(5000))
    
    # Only 2 ratings (below threshold of 5)
    under_ratings = {1: 5.0, 2: 4.0}
    res_under = engine.predict_user_preferences(under_ratings)
    assert res_under == {}

    # 5 ratings
    valid_ratings = {1: 5.0, 2: 4.0, 3: 3.5, 47: 4.5, 50: 5.0}
    res_valid = engine.predict_user_preferences(valid_ratings)
    assert len(res_valid) > 0
    # Already-rated movies should not be in predictions
    for rated_id in valid_ratings.keys():
        assert rated_id not in res_valid
