"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useStore } from "@/lib/store";
import { apiClient, MovieCard as MovieCardType, RecommendationResponse } from "@cinematch/api-client";
import MovieCard from "@/components/MovieCard";
import { surfaceCopy } from "@/copy/en";
import { Sliders, Sparkles, RefreshCw, Zap, ShieldCheck } from "lucide-react";

export default function ForYouView() {
  const { userId, username, ratingCount } = useStore();

  const [recommendations, setRecommendations] = useState<MovieCardType[]>([]);
  const [coldTier, setColdTier] = useState<string>("zero_ratings");
  const [summary, setSummary] = useState<string>("");
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [loading, setLoading] = useState(false);

  // Re-ranking Controls
  const [diversityLambda, setDiversityLambda] = useState(0.15);
  const [noveltyBoost, setNoveltyBoost] = useState(0.05);
  const [recencyPrior, setRecencyPrior] = useState(0.0);
  const [minSupport, setMinSupport] = useState(5);
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    try {
      const res: RecommendationResponse = await apiClient.getUserPersonalizedRecommendations(
        userId,
        20,
        {
          genres: selectedGenre ? [selectedGenre] : undefined,
          minSupport,
          diversityLambda,
          noveltyBoost,
          recencyPrior,
        }
      );
      setRecommendations(res.recommendations);
      setColdTier(res.cold_start_tier);
      setSummary(res.explanation_summary);
      setLatencyMs(res.latency_ms);
    } catch (e: any) {
      console.error("Failed to load recommendations:", e);
    } finally {
      setLoading(false);
    }
  }, [userId, selectedGenre, minSupport, diversityLambda, noveltyBoost, recencyPrior]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const genres = [
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Drama",
    "Horror",
    "Sci-Fi",
    "Thriller",
  ];

  return (
    <div className="space-y-8">
      {/* Studio Control Rail */}
      <div className="p-6 rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-amber-500 uppercase tracking-widest">
                02 / Personalized Discovery
              </span>
              <span className="text-zinc-600">•</span>
              <span className="text-xs text-zinc-400 font-mono">
                {ratingCount} films rated
              </span>
            </div>
            <h2 className="text-xl font-bold text-white tracking-tight mt-1">
              {surfaceCopy.scenes.s03.heading}
            </h2>
            <p className="text-xs text-zinc-400 mt-1 max-w-xl">
              {surfaceCopy.scenes.s03.subheading}
            </p>
          </div>

          <div className="flex items-center gap-3">
            {/* Taste Calibration Badge */}
            <div className="px-3 py-1.5 rounded-full border text-xs font-mono font-medium flex items-center gap-1.5 bg-zinc-900 border-zinc-750 text-amber-400">
              <Zap className="w-3.5 h-3.5" />
              <span>
                {ratingCount >= 5
                  ? "Refined Taste Profile"
                  : ratingCount >= 1
                  ? "Early Taste Profile"
                  : "Community Favorites"}
              </span>
            </div>

            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="p-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white transition-colors cursor-pointer"
              title="Refresh recommendations"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Sliders Grid (Variety, Discovery, Release Era) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          {/* Genre Variety Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-400">Genre Variety</span>
              <span className="text-amber-400 font-bold">{diversityLambda.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.8"
              step="0.05"
              value={diversityLambda}
              onChange={(e) => setDiversityLambda(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[10px] text-zinc-500">
              Balances closely matched films with eclectic surprises.
            </p>
          </div>

          {/* Discovery Style Slider */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-400">Discovery Style</span>
              <span className="text-amber-400 font-bold">{noveltyBoost.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.4"
              step="0.05"
              value={noveltyBoost}
              onChange={(e) => setNoveltyBoost(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[10px] text-zinc-500">
              Surfaces high-quality hidden gems over mainstream hits.
            </p>
          </div>

          {/* Recency Prior */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-400">Era Bias</span>
              <span className="text-amber-400 font-bold">
                {recencyPrior < 0 ? "Classic" : recencyPrior > 0 ? "Modern" : "Neutral"}
              </span>
            </div>
            <input
              type="range"
              min="-0.5"
              max="0.5"
              step="0.1"
              value={recencyPrior}
              onChange={(e) => setRecencyPrior(parseFloat(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[10px] text-zinc-500">
              Weights release year distribution (1930s vs 2010s).
            </p>
          </div>

          {/* Min Support */}
          <div className="space-y-2">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-zinc-400">Min Ratings Support</span>
              <span className="text-amber-400 font-bold">{minSupport}</span>
            </div>
            <input
              type="range"
              min="1"
              max="25"
              step="1"
              value={minSupport}
              onChange={(e) => setMinSupport(parseInt(e.target.value))}
              className="w-full accent-amber-500 cursor-pointer"
            />
            <p className="text-[10px] text-zinc-500">
              Filter movies with at least {minSupport} community ratings.
            </p>
          </div>
        </div>

        {/* Quick Genre Chips */}
        <div className="flex flex-wrap items-center gap-1.5 pt-2">
          <span className="text-xs font-mono text-zinc-500 mr-2">Focus Genre:</span>
          <button
            onClick={() => setSelectedGenre(null)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer ${
              selectedGenre === null
                ? "bg-amber-500 text-black font-semibold"
                : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
            }`}
          >
            All Genres
          </button>
          {genres.map((g) => (
            <button
              key={g}
              onClick={() => setSelectedGenre(selectedGenre === g ? null : g)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                selectedGenre === g
                  ? "bg-amber-500 text-black font-semibold"
                  : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {g}
            </button>
          ))}
        </div>
      </div>

      {/* Summary Bar */}
      <div className="flex flex-wrap items-center justify-between text-xs font-mono text-zinc-500 px-2">
        <p className="truncate max-w-xl">{summary}</p>
        <div className="flex items-center gap-3">
          <span className="text-amber-400 font-semibold">{recommendations.length} films curated</span>
        </div>
      </div>

      {/* Recommendations Cards Grid */}
      {recommendations.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {recommendations.map((movie) => (
            <MovieCard
              key={movie.movieId}
              movie={movie}
              onRatingChanged={fetchRecommendations}
            />
          ))}
        </div>
      ) : (
        <div className="py-24 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/40">
          <Sparkles className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
          <p className="text-zinc-400 text-sm">No recommendations generated for current filters.</p>
          <button
            onClick={() => {
              setSelectedGenre(null);
              setMinSupport(5);
            }}
            className="mt-4 px-4 py-2 rounded-lg bg-zinc-800 text-xs text-zinc-200 hover:bg-zinc-700"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}
