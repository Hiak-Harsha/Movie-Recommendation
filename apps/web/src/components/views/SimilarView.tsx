"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useStore } from "@/lib/store";
import { apiClient, MovieCard as MovieCardType, SimilarMoviesResponse } from "@cinematch/api-client";
import MovieCard from "@/components/MovieCard";
import { Film, Sparkles, Loader2, Search, ArrowRight } from "lucide-react";

export default function SimilarView() {
  const { seedMovieId, setSeedMovieId, setIsSearchOpen } = useStore();

  const [seedMovie, setSeedMovie] = useState<MovieCardType | null>(null);
  const [similarMovies, setSimilarMovies] = useState<MovieCardType[]>([]);
  const [loading, setLoading] = useState(false);
  const [latencyMs, setLatencyMs] = useState(0);

  const featuredSeeds = [
    { id: 1, title: "Toy Story (1995)" },
    { id: 79132, title: "Inception (2010)" },
    { id: 2571, title: "The Matrix (1999)" },
    { id: 296, title: "Pulp Fiction (1994)" },
    { id: 109487, title: "Interstellar (2014)" },
    { id: 858, title: "The Godfather (1972)" },
    { id: 5618, title: "Spirited Away (2001)" },
    { id: 260, title: "Star Wars: Ep. IV (1977)" },
  ];

  const fetchSimilar = useCallback(async () => {
    setLoading(true);
    try {
      const res: SimilarMoviesResponse = await apiClient.getSimilarMovies(seedMovieId, 20);
      setSeedMovie(res.seed_movie);
      setSimilarMovies(res.similar_movies);
      setLatencyMs(res.latency_ms);
    } catch (e: any) {
      console.error("Failed to fetch similar movies:", e);
    } finally {
      setLoading(false);
    }
  }, [seedMovieId]);

  useEffect(() => {
    fetchSimilar();
  }, [fetchSimilar]);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Seed Selection Bar */}
      <div className="p-6 rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
          <div>
            <span className="font-mono text-xs font-bold text-amber-500 uppercase tracking-widest">
              04 / Item-to-Item Similarity Graph
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight mt-1">
              Seed-Based Kinship Discovery
            </h2>
            <p className="text-xs text-zinc-400 mt-1">
              $O(1)$ precomputed array lookup combining shrunk Item-kNN co-ratings and TF-IDF content vectors.
            </p>
          </div>

          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium transition-colors cursor-pointer self-start md:self-auto"
          >
            <Search className="w-3.5 h-3.5 text-amber-400" />
            <span>Pick Another Seed Movie</span>
          </button>
        </div>

        {/* Featured Seeds Pills */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-zinc-500 mr-1">Popular Seeds:</span>
          {featuredSeeds.map((seed) => (
            <button
              key={seed.id}
              onClick={() => setSeedMovieId(seed.id)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                seedMovieId === seed.id
                  ? "bg-amber-500 text-black font-semibold shadow-md shadow-amber-500/20"
                  : "bg-zinc-850 text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {seed.title}
            </button>
          ))}
        </div>

        {/* Active Seed Hero Banner */}
        {seedMovie && (
          <div className="p-4 rounded-xl bg-gradient-to-r from-zinc-900 via-zinc-850 to-zinc-900 border border-zinc-750 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0">
                <Film className="w-6 h-6 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono text-amber-400 uppercase tracking-widest font-bold">
                    Active Seed Movie
                  </span>
                  <span className="text-zinc-600">•</span>
                  <span className="text-xs font-mono text-zinc-400">MovieLens #{seedMovie.movieId}</span>
                </div>
                <h3 className="text-base sm:text-lg font-bold text-white mt-0.5">
                  {seedMovie.display_title}
                </h3>
                <p className="text-xs text-zinc-400 mt-0.5">
                  {seedMovie.genres.join(" • ")} {seedMovie.year ? `(${seedMovie.year})` : ""}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 shrink-0">
              <div className="text-right">
                <p className="text-[10px] font-mono text-zinc-500">Query Time</p>
                <p className="text-xs font-mono text-emerald-400 font-bold">{latencyMs} ms</p>
              </div>
              <div className="w-px h-8 bg-zinc-800" />
              <div className="text-right">
                <p className="text-[10px] font-mono text-zinc-500">Top Matches</p>
                <p className="text-xs font-mono text-white font-bold">{similarMovies.length}</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Similar Movies Grid */}
      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-xs font-mono text-zinc-400">Querying top-100 precomputed nearest neighbours...</p>
        </div>
      ) : similarMovies.length > 0 ? (
        <div className="space-y-4">
          <div className="flex items-center justify-between px-2">
            <h3 className="text-sm font-semibold text-zinc-200">
              Movies Most Similar to &quot;{seedMovie?.display_title}&quot;
            </h3>
            <span className="text-xs font-mono text-zinc-500">
              Ranked by hybrid cosine similarity
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {similarMovies.map((m) => (
              <MovieCard key={m.movieId} movie={m} />
            ))}
          </div>
        </div>
      ) : (
        <div className="py-24 text-center text-zinc-500">
          No similar movies found for this seed.
        </div>
      )}
    </div>
  );
}
