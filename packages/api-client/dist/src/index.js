export class CineMatchClient {
    constructor(baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000") {
        this.baseUrl = baseUrl.replace(/\/$/, "");
    }
    async request(path, options = {}) {
        const res = await fetch(`${this.baseUrl}${path}`, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {}),
            },
        });
        if (!res.ok) {
            let errorMsg = `API Error ${res.status}: ${res.statusText}`;
            try {
                const errorJson = await res.json();
                if (errorJson.detail)
                    errorMsg = errorJson.detail;
            }
            catch { }
            throw new Error(errorMsg);
        }
        return res.json();
    }
    // Health
    async getHealth() {
        return this.request("/health");
    }
    // Search
    async searchMovies(query, limit = 20) {
        const params = new URLSearchParams({ q: query, limit: limit.toString() });
        return this.request(`/api/search?${params.toString()}`);
    }
    // Similar Movies
    async getSimilarMovies(movieId, topN = 20, filters) {
        const params = new URLSearchParams({
            movieId: movieId.toString(),
            top_n: topN.toString(),
        });
        if (filters?.genres && filters.genres.length > 0) {
            params.set("genres", filters.genres.join(","));
        }
        if (filters?.genreMode) {
            params.set("genre_mode", filters.genreMode);
        }
        if (filters?.yearMin !== undefined) {
            params.set("year_min", filters.yearMin.toString());
        }
        if (filters?.yearMax !== undefined) {
            params.set("year_max", filters.yearMax.toString());
        }
        return this.request(`/api/similar?${params.toString()}`);
    }
    // Hybrid Recommendations
    async getRecommendations(req) {
        return this.request("/api/recommendations", {
            method: "POST",
            body: JSON.stringify(req),
        });
    }
    // Users & Persistence
    async getOrCreateUser(username, userId) {
        const params = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
        return this.request(`/api/users${params}`, {
            method: "POST",
            body: JSON.stringify({ username }),
        });
    }
    async getUserProfile(userId) {
        return this.request(`/api/users/${encodeURIComponent(userId)}`);
    }
    async loadDemoRatings(demoUserId, userId) {
        return this.request(`/api/users/demo/${demoUserId}/load/${encodeURIComponent(userId)}`, { method: "POST" });
    }
    // User Ratings
    async getUserRatings(userId) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/ratings`);
    }
    async submitRating(userId, movieId, rating) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/ratings`, {
            method: "POST",
            body: JSON.stringify({ movieId, rating }),
        });
    }
    async deleteRating(userId, movieId) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/ratings/${movieId}`, { method: "DELETE" });
    }
    // Watchlist
    async getUserWatchlist(userId) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/watchlist`);
    }
    async addToWatchlist(userId, movieId, notes) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/watchlist`, {
            method: "POST",
            body: JSON.stringify({ movieId, notes }),
        });
    }
    async removeFromWatchlist(userId, movieId) {
        return this.request(`/api/users/${encodeURIComponent(userId)}/watchlist/${movieId}`, { method: "DELETE" });
    }
    getWatchlistExportUrl(userId) {
        return `${this.baseUrl}/api/users/${encodeURIComponent(userId)}/watchlist/export`;
    }
    // User Recommendations (Persistent)
    async getUserPersonalizedRecommendations(userId, topN = 20, filters) {
        const params = new URLSearchParams({ top_n: topN.toString() });
        if (filters?.genres?.length)
            params.set("genres", filters.genres.join(","));
        if (filters?.genreMode)
            params.set("genre_mode", filters.genreMode);
        if (filters?.yearMin !== undefined)
            params.set("year_min", filters.yearMin.toString());
        if (filters?.yearMax !== undefined)
            params.set("year_max", filters.yearMax.toString());
        if (filters?.minSupport !== undefined)
            params.set("min_support", filters.minSupport.toString());
        if (filters?.diversityLambda !== undefined)
            params.set("diversity_lambda", filters.diversityLambda.toString());
        if (filters?.noveltyBoost !== undefined)
            params.set("novelty_boost", filters.noveltyBoost.toString());
        if (filters?.recencyPrior !== undefined)
            params.set("recency_prior", filters.recencyPrior.toString());
        return this.request(`/api/users/${encodeURIComponent(userId)}/recommendations?${params.toString()}`);
    }
    // Media Details
    async getMediaDetails(movieId) {
        return this.request(`/api/media/movie/${movieId}`);
    }
    // Model Metadata & Demo Profiles
    async getModelMeta() {
        return this.request("/api/meta/model");
    }
    async getDemoProfiles() {
        return this.request("/api/meta/demo-profiles");
    }
}
export const apiClient = new CineMatchClient();
