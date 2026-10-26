"""
CineMatch Configuration
Centralized settings, file paths, model parameters, and UI defaults.
"""
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent
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

# Bayesian popularity smoothing parameters
# m: minimum rating count threshold for Bayesian prior weighting
BAYESIAN_MIN_RATINGS = 10

# Ranking Evaluation parameters
RELEVANCE_RATING_THRESHOLD = 4.0
DEFAULT_TOP_K = 10
EVALUATION_TEST_RATIO = 0.20
RANDOM_STATE = 42

# UI Configuration
APP_TITLE = "CineMatch"
APP_TAGLINE = "Hybrid Movie Recommendation Workspace"
SUPPORTED_GENRES = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "Musical",
    "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western"
]
