export class CineMatchClient {
    constructor(baseUrl = process.env.NEXT_PUBLIC_API_URL || "") {
        this.baseUrl = baseUrl.replace(/\/$/, "");
    }
    async request(path, options = {}) {
        const res = await fetch(`${this.baseUrl}${path}`, {
            ...options,
            credentials: "include",
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
    // --- Visitor Session Endpoints (/api/me/*, showcase, onboarding, about) ---
    async getMe() {
        return this.request("/api/me");
    }
    async getMyRatings() {
        return this.request("/api/me/ratings");
    }
    async submitMyRating(movieId, rating) {
        return this.request("/api/me/ratings", {
            method: "POST",
            body: JSON.stringify({ movieId, rating }),
        });
    }
    async deleteMyRating(movieId) {
        return this.request(`/api/me/ratings/${movieId}`, {
            method: "DELETE",
        });
    }
    async getMyWatchlist() {
        return this.request("/api/me/watchlist");
    }
    async addToMyWatchlist(movieId) {
        return this.request(`/api/me/watchlist/${movieId}`, {
            method: "PUT",
        });
    }
    async removeFromMyWatchlist(movieId) {
        return this.request(`/api/me/watchlist/${movieId}`, {
            method: "DELETE",
        });
    }
    async getMyShelves() {
        return this.request("/api/me/shelves");
    }
    async getMyRecommendations(filters) {
        const params = new URLSearchParams();
        if (filters?.novelty !== undefined)
            params.set("novelty", filters.novelty.toString());
        if (filters?.diversity !== undefined)
            params.set("diversity", filters.diversity.toString());
        if (filters?.recency !== undefined)
            params.set("recency", filters.recency.toString());
        if (filters?.genres)
            params.set("genres", filters.genres);
        if (filters?.decades)
            params.set("decades", filters.decades);
        if (filters?.topN !== undefined)
            params.set("top_n", filters.topN.toString());
        return this.request(`/api/me/recommendations?${params.toString()}`);
    }
    async recordEvent(movieId, interactionType) {
        return this.request("/api/me/events", {
            method: "POST",
            body: JSON.stringify({ movieId, interaction_type: interactionType }),
        });
    }
    getExportDataUrl() {
        return `${this.baseUrl}/api/me/export`;
    }
    async eraseMyData() {
        return this.request("/api/me", {
            method: "DELETE",
        });
    }
    async getShowcase() {
        return this.request("/api/showcase");
    }
    async getShowcaseMovies() {
        return this.getShowcase();
    }
    async getOnboardingPicks() {
        return this.request("/api/onboarding/picks");
    }
    async getMovieDetail(id) {
        return this.request(`/api/movies/${id}`);
    }
    async getAbout() {
        return this.request("/api/about");
    }
}
export const apiClient = new CineMatchClient();
