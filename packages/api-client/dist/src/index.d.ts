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
    getModelMeta(): Promise<ModelMetaResponse>;
    getDemoProfiles(): Promise<DemoProfile[]>;
}
export declare const apiClient: CineMatchClient;
