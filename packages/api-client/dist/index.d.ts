import type { components } from "./schema";
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
export declare class CineMatchClient {
    private baseUrl;
    constructor(baseUrl?: string);
    private request;
    getHealth(): Promise<{
        status: string;
        dataset_fingerprint: string;
        is_loaded: boolean;
    }>;
    searchMovies(query: string, limit?: number): Promise<SearchResponse>;
    getSimilarMovies(movieId: number, topN?: number, filters?: {
        genres?: string[];
        genreMode?: "OR" | "AND";
        yearMin?: number;
        yearMax?: number;
    }): Promise<SimilarMoviesResponse>;
    getRecommendations(req: RecommendationRequest): Promise<RecommendationResponse>;
    getOrCreateUser(username?: string, userId?: string): Promise<UserResponse>;
    getUserProfile(userId: string): Promise<UserResponse>;
    loadDemoRatings(demoUserId: number, userId: string): Promise<{
        loaded_ratings: number;
    }>;
    getUserRatings(userId: string): Promise<RatingItem[]>;
    submitRating(userId: string, movieId: number, rating: number): Promise<RatingItem>;
    deleteRating(userId: string, movieId: number): Promise<{
        status: string;
    }>;
    getUserWatchlist(userId: string): Promise<WatchlistItem[]>;
    addToWatchlist(userId: string, movieId: number, notes?: string): Promise<WatchlistItem>;
    removeFromWatchlist(userId: string, movieId: number): Promise<{
        status: string;
    }>;
    getWatchlistExportUrl(userId: string): string;
    getUserPersonalizedRecommendations(userId: string, topN?: number, filters?: {
        genres?: string[];
        genreMode?: "OR" | "AND";
        yearMin?: number;
        yearMax?: number;
        minSupport?: number;
        diversityLambda?: number;
        noveltyBoost?: number;
        recencyPrior?: number;
    }): Promise<RecommendationResponse>;
    getMediaDetails(movieId: number): Promise<MediaDetails>;
    getMe(): Promise<MeResponse>;
    getMyRatings(): Promise<RatingItem[]>;
    submitMyRating(movieId: number, rating: number): Promise<RatingItem>;
    deleteMyRating(movieId: number): Promise<{
        status: string;
    }>;
    getMyWatchlist(): Promise<WatchlistItem[]>;
    addToMyWatchlist(movieId: number): Promise<WatchlistItem>;
    removeFromMyWatchlist(movieId: number): Promise<{
        status: string;
    }>;
    getMyShelves(): Promise<ShelvesResponse>;
    getMyRecommendations(filters?: {
        novelty?: number;
        diversity?: number;
        recency?: number;
        genres?: string;
        decades?: string;
        topN?: number;
    }): Promise<RecommendationResponse>;
    recordEvent(movieId: number, interactionType: "impression" | "click" | "dismiss"): Promise<{
        status: string;
    }>;
    getExportDataUrl(): string;
    eraseMyData(): Promise<{
        status: string;
        message: string;
    }>;
    getShowcase(): Promise<ShowcaseResponse>;
    getShowcaseMovies(): Promise<ShowcaseResponse>;
    getOnboardingPicks(): Promise<OnboardingPicksResponse>;
    getMovieDetail(id: number): Promise<MovieDetailResponse>;
    getAbout(): Promise<AboutResponse>;
}
export declare const apiClient: CineMatchClient;
