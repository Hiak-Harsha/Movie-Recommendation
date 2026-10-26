"use client";

import React, { useState, useEffect, useCallback } from "react";
import { apiClient, MovieCard as MovieCardType, RecommendationResponse } from "@cinematch/api-client";
import MovieCard from "@/components/MovieCard";
import { Search, Filter, Loader2, Sparkles } from "lucide-react";

export default function DiscoverView() {
  const [movies, setMovies] = useState<MovieCardType[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [genreMode, setGenreMode] = useState<"OR" | "AND">("OR");
  const [selectedDecade, setSelectedDecade] = useState<string>("all");
  const [minSupport, setMinSupport] = useState<number>(10);

  const genresList = [
    "Action", "Adventure", "Animation", "Comedy", "Crime",
    "Drama", "Fantasy", "Horror", "Mystery", "Romance",
    "Sci-Fi", "Thriller", "Western"
  ];

  const decades = [
    { label: "All Eras", value: "all", min: undefined, max: undefined },
    { label: "2010s", value: "2010s", min: 2010, max: 2018 },
    { label: "2000s", value: "2000s", min: 2000, max: 2009 },
    { label: "1990s", value: "1990s", min: 1990, max: 1999 },
    { label: "1980s", value: "1980s", min: 1980, max: 1989 },
    { label: "Classics", value: "classics", min: 1920, max: 1979 },
  ];

  const activeDecade = decades.find((d) => d.value === selectedDecade) || decades[0];

  const fetchCatalogMovies = useCallback(async () => {
    setLoading(true);
    try {
      if (searchQuery.trim().length >= 2) {
        const searchRes = await apiClient.searchMovies(searchQuery, 24);
        const mapped: MovieCardType[] = searchRes.results.map((r: any) => ({
          movieId: r.movieId,
          title: r.title,
          display_title: r.display_title,
          year: r.year,
          genres: r.genres,
          vote_count: r.vote_count,
          vote_average: r.vote_average,
          weighted_rating: r.weighted_rating,
          score: r.score,
          predicted_rating: r.vote_average,
          signals: [],
          contributions: { mf: 0, knn: 0, content: 0, popularity: 1 },
          imdbId: r.imdbId,
          tmdbId: r.tmdbId,
        }));
        setMovies(mapped);
      } else {
        // Query via recommendations endpoint with empty ratings (Bayesian Popularity catalog exploration)
        const recRes: RecommendationResponse = await apiClient.getRecommendations({
          user_ratings: {},
          top_n: 24,
          genres: selectedGenres.length > 0 ? selectedGenres : undefined,
          genre_mode: genreMode,
          year_min: activeDecade.min,
          year_max: activeDecade.max,
          min_support: minSupport,
          diversity_lambda: 0.2,
          novelty_boost: 0.1,
          recency_prior: 0.0,
        });
        setMovies(recRes.recommendations);
      }
    } catch (e: any) {
      console.error("Error discovering movies:", e);
    } finally {
      setLoading(false);
    }
  }, [searchQuery, selectedGenres, genreMode, activeDecade.min, activeDecade.max, minSupport]);

  useEffect(() => {
    fetchCatalogMovies();
  }, [fetchCatalogMovies]);

  const toggleGenre = (g: string) => {
    if (selectedGenres.includes(g)) {
      setSelectedGenres(selectedGenres.filter((item) => item !== g));
    } else {
      setSelectedGenres([...selectedGenres, g]);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header & Filter Bar */}
      <div className="p-6 rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-zinc-800">
          <div>
            <span className="font-mono text-xs font-bold text-amber-500 uppercase tracking-widest">
              03 / Catalog Exploration
            </span>
            <h2 className="text-xl font-bold text-white tracking-tight mt-1">
              Explore 9,742 Verified Titles
            </h2>
            <p className="text-xs text-zinc-400 mt-1">
              Filter by genre intersections, release era, and community review volume.
            </p>
          </div>

          {/* Search bar inside discover */}
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter by title..."
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-zinc-900 border border-zinc-750 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500/50"
            />
          </div>
        </div>

        {/* Filter Controls Row */}
        <div className="space-y-4">
          {/* Era Chips */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-mono text-zinc-500 mr-2">Era:</span>
            {decades.map((d) => (
              <button
                key={d.value}
                onClick={() => setSelectedDecade(d.value)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                  selectedDecade === d.value
                    ? "bg-amber-500 text-black font-semibold"
                    : "bg-zinc-800 text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {d.label}
              </button>
            ))}
          </div>

          {/* Genre Chips */}
          <div className="flex flex-wrap items-center gap-1.5">
            <div className="flex items-center gap-2 mr-2">
              <span className="text-xs font-mono text-zinc-500">Genres:</span>
              <button
                onClick={() => setGenreMode(genreMode === "OR" ? "AND" : "OR")}
                className="px-2 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-[10px] font-mono text-amber-400 font-bold"
                title="Toggle OR / AND genre combination mode"
              >
                MODE: {genreMode}
              </button>
            </div>
            {genresList.map((g) => {
              const active = selectedGenres.includes(g);
              return (
                <button
                  key={g}
                  onClick={() => toggleGenre(g)}
                  className={`px-2.5 py-1 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                    active
                      ? "bg-amber-500 text-black font-semibold"
                      : "bg-zinc-850 text-zinc-400 hover:text-zinc-200"
                  }`}
                >
                  {g}
                </button>
              );
            })}
            {selectedGenres.length > 0 && (
              <button
                onClick={() => setSelectedGenres([])}
                className="text-xs text-zinc-500 hover:text-zinc-300 underline ml-2 cursor-pointer"
              >
                Clear all
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Grid */}
      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-xs font-mono text-zinc-400">Scanning catalog and applying masks...</p>
        </div>
      ) : movies.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {movies.map((m) => (
            <MovieCard key={m.movieId} movie={m} />
          ))}
        </div>
      ) : (
        <div className="py-24 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/40">
          <p className="text-zinc-400 text-sm">No catalog titles match your filter criteria.</p>
        </div>
      )}
    </div>
  );
}
