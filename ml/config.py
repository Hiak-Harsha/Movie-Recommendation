"""
CineMatch ML Configuration (pydantic-settings)
Strictly uses environment variables and relative project paths.
No absolute or machine-specific personal paths.
"""
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class MLSettings(BaseSettings):
    # Paths relative to repository root
    project_root: Path = Path(__file__).resolve().parent.parent
    data_dir: Path = Path(__file__).resolve().parent.parent / "data"
    artifacts_dir: Path = Path(__file__).resolve().parent.parent / "artifacts"
    
    # Dataset files
    movies_filename: str = "movies.csv"
    ratings_filename: str = "ratings.csv"
    tags_filename: str = "tags.csv"
    links_filename: str = "links.csv"
    readme_filename: str = "README.txt"

    # Reproducibility
    random_seed: int = 42

    # Content Model
    genre_weight: float = 0.60
    tag_weight: float = 0.40
    tag_min_movies: int = 1
    tag_min_users: int = 1
    tag_max_per_user_movie: int = 10

    # Item-kNN Collaborative Filtering
    knn_k: int = 100
    knn_min_co_ratings: int = 3
    knn_shrinkage_lambda: float = 5.0

    # Explicit ALS Factorization
    als_factors: int = 32
    als_reg: float = 0.08
    als_iterations: int = 12
    als_bias_reg: float = 0.05

    # Bayesian Popularity Smoothing
    bayesian_percentile: int = 80
    fallback_bayesian_m: float = 12.0

    # Evaluation Split Ratios
    eval_train_ratio: float = 0.70
    eval_val_ratio: float = 0.10
    eval_test_ratio: float = 0.20
    eval_min_ratings_per_user: int = 5
    eval_relevance_threshold: float = 4.0
    eval_bootstrap_iterations: int = 200

    # Re-Ranking Defaults
    default_diversity_lambda: float = 0.15
    default_novelty_boost: float = 0.05
    default_recency_prior: float = 0.0

    model_config = SettingsConfigDict(
        env_prefix="CINEMATCH_",
        case_sensitive=False,
        extra="ignore"
    )


settings = MLSettings()
