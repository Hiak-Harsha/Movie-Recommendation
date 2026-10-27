import type { paths, components } from "./schema";

declare const process: any;

export type MovieCard = components["schemas"]["MovieCard"];
export type RecommendationRequest = components["schemas"]["RecommendationRequest"];
export type RecommendationResponse = components["schemas"]["RecommendationResponse"];
export type SimilarMoviesResponse = components["schemas"]["SimilarMoviesResponse"];
export type SearchResponse = components["schemas"]["SearchResponse"];
export type SearchResult = components["schemas"]["SearchResult"];
export type UserResponse = components["schemas"]["UserResponse"];
export type RatingItem = components["schemas"]["RatingItem"];
export type WatchlistItem = components["schemas"]["WatchlistItem"];
export type MediaDetails = components["schemas"]["MediaDetails"];
export type DemoProfile = components["schemas"]["DemoProfile"];
export type ModelMetaResponse = components["schemas"]["ModelMetaResponse"];

export interface MeResponse {
  user_id: string;
  username: string;
  picks_count: number;
  library_count: number;
  has_picks: boolean;
  created_at: string;
}

export interface ShelfItem {
  id: string;
  title: string;
  reason: string;
  movies: MovieCard[];
}

export interface ShelvesResponse {
  shelves: ShelfItem[];
}

export interface ShowcaseResponse {
  movies: MovieCard[];
}

export interface OnboardingPicksResponse {
  movies: MovieCard[];
}

export interface MovieDetailResponse {
  movie: MovieCard;
  media: MediaDetails;
  similar_ids: number[];
}

export interface AboutResponse {
  dataset: {
    name: string;
    citation: string;
    clean_ratings: number;
    clean_users: number;
    clean_movies: number;
    sparsity_pct: number;
    terms: string;
  };
  evaluation: Record<string, any>;
  active_strategy: {
    strategy: string;
    data: Record<string, any>;
  };
  versions: Record<string, string>;
  licenses: Record<string, string>;
}

export class CineMatchClient {
  private baseUrl: string;

  constructor(baseUrl: string = process.env.NEXT_PUBLIC_API_URL || "") {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
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
        if (errorJson.detail) errorMsg = errorJson.detail;
      } catch {}
      throw new Error(errorMsg);
    }

    return res.json() as Promise<T>;
  }

  // Health
  async getHealth() {
    return this.request<{ status: string; dataset_fingerprint: string; is_loaded: boolean }>("/health");
  }

  // Search
  async searchMovies(query: string, limit: number = 20): Promise<SearchResponse> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    return this.request<SearchResponse>(`/api/search?${params.toString()}`);
  }

  // Similar Movies
  async getSimilarMovies(
    movieId: number,
    topN: number = 20,
    filters?: {
      genres?: string[];
      genreMode?: "OR" | "AND";
      yearMin?: number;
      yearMax?: number;
    }
  ): Promise<SimilarMoviesResponse> {
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
    return this.request<SimilarMoviesResponse>(`/api/similar?${params.toString()}`);
  }

  // Hybrid Recommendations
  async getRecommendations(req: RecommendationRequest): Promise<RecommendationResponse> {
    return this.request<RecommendationResponse>("/api/recommendations", {
      method: "POST",
      body: JSON.stringify(req),
    });
  }

  // Users & Persistence
  async getOrCreateUser(username?: string, userId?: string): Promise<UserResponse> {
    const params = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    return this.request<UserResponse>(`/api/users${params}`, {
      method: "POST",
      body: JSON.stringify({ username }),
    });
  }

  async getUserProfile(userId: string): Promise<UserResponse> {
    return this.request<UserResponse>(`/api/users/${encodeURIComponent(userId)}`);
  }

  async loadDemoRatings(demoUserId: number, userId: string): Promise<{ loaded_ratings: number }> {
    return this.request<{ loaded_ratings: number }>(
      `/api/users/demo/${demoUserId}/load/${encodeURIComponent(userId)}`,
      { method: "POST" }
    );
  }

  // User Ratings
  async getUserRatings(userId: string): Promise<RatingItem[]> {
    return this.request<RatingItem[]>(`/api/users/${encodeURIComponent(userId)}/ratings`);
  }

  async submitRating(userId: string, movieId: number, rating: number): Promise<RatingItem> {
    return this.request<RatingItem>(`/api/users/${encodeURIComponent(userId)}/ratings`, {
      method: "POST",
      body: JSON.stringify({ movieId, rating }),
    });
  }

  async deleteRating(userId: string, movieId: number): Promise<{ status: string }> {
    return this.request<{ status: string }>(
      `/api/users/${encodeURIComponent(userId)}/ratings/${movieId}`,
      { method: "DELETE" }
    );
  }

  // Watchlist
  async getUserWatchlist(userId: string): Promise<WatchlistItem[]> {
    return this.request<WatchlistItem[]>(`/api/users/${encodeURIComponent(userId)}/watchlist`);
  }

  async addToWatchlist(userId: string, movieId: number, notes?: string): Promise<WatchlistItem> {
    return this.request<WatchlistItem>(`/api/users/${encodeURIComponent(userId)}/watchlist`, {
      method: "POST",
      body: JSON.stringify({ movieId, notes }),
    });
  }

  async removeFromWatchlist(userId: string, movieId: number): Promise<{ status: string }> {
    return this.request<{ status: string }>(
      `/api/users/${encodeURIComponent(userId)}/watchlist/${movieId}`,
      { method: "DELETE" }
    );
  }

  getWatchlistExportUrl(userId: string): string {
    return `${this.baseUrl}/api/users/${encodeURIComponent(userId)}/watchlist/export`;
  }

  // User Recommendations (Persistent)
  async getUserPersonalizedRecommendations(
    userId: string,
    topN: number = 20,
    filters?: {
      genres?: string[];
      genreMode?: "OR" | "AND";
      yearMin?: number;
      yearMax?: number;
      minSupport?: number;
      diversityLambda?: number;
      noveltyBoost?: number;
      recencyPrior?: number;
    }
  ): Promise<RecommendationResponse> {
    const params = new URLSearchParams({ top_n: topN.toString() });
    if (filters?.genres?.length) params.set("genres", filters.genres.join(","));
    if (filters?.genreMode) params.set("genre_mode", filters.genreMode);
    if (filters?.yearMin !== undefined) params.set("year_min", filters.yearMin.toString());
    if (filters?.yearMax !== undefined) params.set("year_max", filters.yearMax.toString());
    if (filters?.minSupport !== undefined) params.set("min_support", filters.minSupport.toString());
    if (filters?.diversityLambda !== undefined) params.set("diversity_lambda", filters.diversityLambda.toString());
    if (filters?.noveltyBoost !== undefined) params.set("novelty_boost", filters.noveltyBoost.toString());
    if (filters?.recencyPrior !== undefined) params.set("recency_prior", filters.recencyPrior.toString());

    return this.request<RecommendationResponse>(
      `/api/users/${encodeURIComponent(userId)}/recommendations?${params.toString()}`
    );
  }

  // Media Details
  async getMediaDetails(movieId: number): Promise<MediaDetails> {
    return this.request<MediaDetails>(`/api/media/movie/${movieId}`);
  }

  // --- Visitor Session Endpoints (/api/me/*, showcase, onboarding, about) ---

  async getMe(): Promise<MeResponse> {
    return this.request<MeResponse>("/api/me");
  }

  async getMyRatings(): Promise<RatingItem[]> {
    return this.request<RatingItem[]>("/api/me/ratings");
  }

  async submitMyRating(movieId: number, rating: number): Promise<RatingItem> {
    return this.request<RatingItem>("/api/me/ratings", {
      method: "POST",
      body: JSON.stringify({ movieId, rating }),
    });
  }

  async deleteMyRating(movieId: number): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/me/ratings/${movieId}`, {
      method: "DELETE",
    });
  }

  async getMyWatchlist(): Promise<WatchlistItem[]> {
    return this.request<WatchlistItem[]>("/api/me/watchlist");
  }

  async addToMyWatchlist(movieId: number): Promise<WatchlistItem> {
    return this.request<WatchlistItem>(`/api/me/watchlist/${movieId}`, {
      method: "PUT",
    });
  }

  async removeFromMyWatchlist(movieId: number): Promise<{ status: string }> {
    return this.request<{ status: string }>(`/api/me/watchlist/${movieId}`, {
      method: "DELETE",
    });
  }

  async getMyShelves(): Promise<ShelvesResponse> {
    return this.request<ShelvesResponse>("/api/me/shelves");
  }

  async getMyRecommendations(filters?: {
    novelty?: number;
    diversity?: number;
    recency?: number;
    genres?: string;
    decades?: string;
    topN?: number;
  }): Promise<RecommendationResponse> {
    const params = new URLSearchParams();
    if (filters?.novelty !== undefined) params.set("novelty", filters.novelty.toString());
    if (filters?.diversity !== undefined) params.set("diversity", filters.diversity.toString());
    if (filters?.recency !== undefined) params.set("recency", filters.recency.toString());
    if (filters?.genres) params.set("genres", filters.genres);
    if (filters?.decades) params.set("decades", filters.decades);
    if (filters?.topN !== undefined) params.set("top_n", filters.topN.toString());
    return this.request<RecommendationResponse>(`/api/me/recommendations?${params.toString()}`);
  }

  async recordEvent(movieId: number, interactionType: "impression" | "click" | "dismiss"): Promise<{ status: string }> {
    return this.request<{ status: string }>("/api/me/events", {
      method: "POST",
      body: JSON.stringify({ movieId, interaction_type: interactionType }),
    });
  }

  getExportDataUrl(): string {
    return `${this.baseUrl}/api/me/export`;
  }

  async eraseMyData(): Promise<{ status: string; message: string }> {
    return this.request<{ status: string; message: string }>("/api/me", {
      method: "DELETE",
    });
  }

  async getShowcase(): Promise<ShowcaseResponse> {
    return this.request<ShowcaseResponse>("/api/showcase");
  }

  async getOnboardingPicks(): Promise<OnboardingPicksResponse> {
    return this.request<OnboardingPicksResponse>("/api/onboarding/picks");
  }

  async getMovieDetail(id: number): Promise<MovieDetailResponse> {
    return this.request<MovieDetailResponse>(`/api/movies/${id}`);
  }

  async getAbout(): Promise<AboutResponse> {
    return this.request<AboutResponse>("/api/about");
  }
}

export const apiClient = new CineMatchClient();

