"""
CineMatch Configuration
Centralized settings, file paths, model parameters, and UI defaults.
"""
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_CANDIDATE_PATHS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "ml-latest-small" / "ml-latest-small",
    PROJECT_ROOT / "ml-latest-small",
]

# Expected dataset filenames
MOVIES_FILENAME = "movies.csv"
RATINGS_FILENAME = "ratings.csv"
TAGS_FILENAME = "tags.csv"
LINKS_FILENAME = "links.csv"
README_FILENAME = "README.txt"

# Tag processing parameters
TAG_MIN_MOVIES = 1
TAG_MIN_USERS = 1
TAG_MAX_PER_USER_MOVIE = 10

# Model Hyperparameters & Defaults
DEFAULT_HYBRID_WEIGHTS = {
    "content": 0.45,
    "collaborative": 0.45,
    "popularity": 0.10,
}

# Fallback weights when collaborative filtering is unavailable (cold-start)
COLD_START_WEIGHTS = {
    "content": 0.75,
    "collaborative": 0.0,
    "popularity": 0.25,
}

# Collaborative filtering rules
MIN_USER_RATINGS_FOR_CF = 5
MIN_RECOGNIZED_ITEMS_FOR_CF = 3
CF_MIN_CO_RATINGS = 3
CF_SHRINKAGE_LAMBDA = 5.0
MF_FACTORS = 20
MF_REGULARIZATION = 0.05
MF_ITERATIONS = 15

# Bayesian popularity smoothing parameters
# m: minimum rating count threshold for Bayesian prior weighting
# Default percentile of training rating-count distribution
BAYESIAN_PERCENTILE = 80
FALLBACK_BAYESIAN_MIN_RATINGS = 10

# Ranking Evaluation parameters (70% Train / 10% Val / 20% Test)
EVAL_TRAIN_RATIO = 0.70
EVAL_VAL_RATIO = 0.10
EVAL_TEST_RATIO = 0.20
MIN_USER_RATINGS_EVAL = 5
RELEVANCE_RATING_THRESHOLD = 4.0
DEFAULT_TOP_K = 10
RANDOM_SEED = 42
BOOTSTRAP_ROUNDS = 200

# UI Configuration
APP_TITLE = "CineMatch"
APP_TAGLINE = "Hybrid Movie Recommendation Workspace"
SUPPORTED_GENRES = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]
