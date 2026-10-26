# CineMatch API Documentation

Production REST API for CineMatch recommendation intelligence, typo-tolerant search, item similarity graphs, persistent user profiles, and TMDB media proxies.

- **Base URL (Local)**: `http://localhost:8000`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`
- **OpenAPI Schema**: [docs/openapi.json](file:///c:/Users/madha/Desktop/Movie%20Recommendation/docs/openapi.json)

---

## 1. System & Health

### `GET /health`
Returns application status, dataset fingerprint verification, catalog count, and cold startup duration.

**Response (200 OK):**
```json
{
  "status": "healthy",
  "dataset_fingerprint": "8aaa97d2eb36dd06",
  "is_loaded": true,
  "catalog_size": 9742,
  "startup_duration_seconds": 1.483
}
```

---

## 2. Recommendation & Search

### `GET /api/search`
Typo-tolerant, article-aware search index over 9,742 catalog titles with character match offsets for UI highlighting.

- **Query Parameters**:
  - `q` (string, required): Search query string (e.g. `"matrix"`, `"godfathr 1972"`, `"interstellar"`).
  - `limit` (int, default 20): Maximum number of results.

### `GET /api/similar`
$O(1)$ precomputed array lookup combining shrunk Item-kNN co-ratings and TF-IDF content cosine similarity.

- **Query Parameters**:
  - `movieId` (int, required): Target seed movie identifier.
  - `top_n` (int, default 20): Number of neighbors to return.
  - `genres` (string, optional): Comma-separated genre filters.
  - `genre_mode` (string, default `"OR"`): Filter mode (`"OR"` or `"AND"`).
  - `year_min` / `year_max` (int, optional): Release year boundary filters.

### `POST /api/recommendations`
Personalized multi-signal hybrid recommendation using closed-form explicit ALS fold-in, shrunk Item-kNN, content taste vectors, and learned blend scoring.

- **Request Body (`RecommendationRequest`)**:
```json
{
  "user_ratings": {
    "1": 5.0,
    "296": 4.5,
    "2571": 5.0
  },
  "top_n": 20,
  "min_support": 5,
  "diversity_lambda": 0.15,
  "novelty_boost": 0.05,
  "recency_prior": 0.0
}
```

---

## 3. Persistence & User Accounts (Defect D7)

### `POST /api/users`
Creates or retrieves a persistent user profile stored in SQLite (`cinematch.db`).

### `GET /api/users/{user_id}`
Returns profile metadata, submitted rating counts, and watchlist item count.

### `POST /api/users/demo/{demo_user_id}/load/{user_id}`
Loads a real MovieLens demo user profile (e.g. User #414, #606, #177) into the active session.

### `GET /api/users/{user_id}/ratings`
Retrieves all ratings submitted by a user, joined with catalog titles, years, and genres.

### `POST /api/users/{user_id}/ratings`
Submits or updates a movie rating (0.5 to 5.0 stars) for a user.

### `DELETE /api/users/{user_id}/ratings/{movie_id}`
Deletes a user's rating.

### `GET /api/users/{user_id}/watchlist`
Retrieves all movies on a user's saved watchlist.

### `POST /api/users/{user_id}/watchlist`
Adds a movie to the user's watchlist with optional notes.

### `DELETE /api/users/{user_id}/watchlist/{movie_id}`
Removes a movie from the watchlist.

### `GET /api/users/{user_id}/watchlist/export`
Streams the user's watchlist as a downloadable CSV file (`cinematch_watchlist_{user_id}.csv`).

### `GET /api/users/{user_id}/recommendations`
Pulls persistent ratings directly from SQLite and executes real-time ALS fold-in recommendations.

---

## 4. Media & Visuals (Defect D8)

### `GET /api/media/movie/{movie_id}`
Retrieves movie posters, backdrops, overview synopsis, top 5 cast members, director, YouTube trailer key, and US streaming providers. Results are cached in the SQLite `media_cache` table. Falls back deterministically to genre-palette typographic art if offline or no TMDB key is provided.

---

## 5. Metadata & Model Transparency

### `GET /api/meta/model`
Reports the active dataset fingerprint, catalog size, ALS latent factor dimension, blend coefficients, and quality gate selected strategy.

### `GET /api/meta/demo-profiles`
Returns the verified MovieLens demo user profiles dynamically generated from training data.
