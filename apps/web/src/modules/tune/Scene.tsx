"use client";
import React, { useState, useEffect, useCallback, useTransition } from "react";
import { SlidersHorizontal, RotateCcw } from "lucide-react";
import { api } from "../../core/client";
import { MoviePosterCard } from "../../core/MoviePosterCard";
import type { MovieCard } from "@cinematch/api-client";

const GENRES = ["Action", "Sci-Fi", "Drama", "Comedy", "Thriller", "Horror", "Romance", "Animation", "Crime", "Adventure"];
const DECADES = ["2020s", "2010s", "2000s", "1990s", "1980s", "Classics"];

export const TuneScene: React.FC<{ progress?: number }> = () => {
  const [novelty, setNovelty] = useState(0.05);
  const [diversity, setDiversity] = useState(0.15);
  const [recency, setRecency] = useState(0.0);
  const [selectedGenre, setSelectedGenre] = useState<string | null>(null);
  const [selectedDecade, setSelectedDecade] = useState<string | null>(null);

  const [movies, setMovies] = useState<MovieCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [, startTransition] = useTransition();

  const fetchRecommendations = useCallback(() => {
    setLoading(true);
    api.getMyRecommendations({
      novelty,
      diversity,
      recency,
      genres: selectedGenre || undefined,
      decades: selectedDecade || undefined,
      topN: 18,
    })
      .then((res) => {
        startTransition(() => {
          setMovies(res.recommendations || []);
          setLoading(false);
        });
      })
      .catch((err) => {
        console.error("Tune recommendations failed:", err);
        setLoading(false);
      });
  }, [novelty, diversity, recency, selectedGenre, selectedDecade]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchRecommendations();
    }, 150);
    return () => clearTimeout(timer);
  }, [fetchRecommendations]);

  const handleReset = () => {
    setNovelty(0.05);
    setDiversity(0.15);
    setRecency(0.0);
    setSelectedGenre(null);
    setSelectedDecade(null);
  };

  return (
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 px-4 py-8">
      {/* Eyebrow & Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-[#26282e] pb-4 gap-4">
        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            04/ Tune
          </span>
          <h2 className="text-fluid-h2 font-display font-bold text-[#f2efe6] tracking-tight">
            Fine-tune your recommendations
          </h2>
          <p className="text-xs sm:text-sm text-[#9a9aa0]">
            Dial in novelty, diversity, and release eras in real time.
          </p>
        </div>

        <button
          type="button"
          onClick={handleReset}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] bg-[#121316] border border-[#26282e] hover:border-[#f5a524]/40 transition-colors cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Reset to default</span>
        </button>
      </div>

      {/* Main Grid: Controls on Left, Live Posters on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Controls Column */}
        <div className="lg:col-span-4 flex flex-col gap-6 p-6 rounded-2xl bg-[#121316] border border-[#26282e] shadow-xl">
          <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-wider text-[#f5a524]">
            <SlidersHorizontal className="w-4 h-4" />
            <span>Tuning Faders</span>
          </div>

          {/* Fader 1: Novelty */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#f2efe6] font-medium">Discovery Style</span>
              <span className="font-mono text-[#f5a524]">{Math.round(novelty * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={novelty}
              onChange={(e) => setNovelty(parseFloat(e.target.value))}
              className="w-full accent-[#f5a524] cursor-pointer"
              aria-label="Discovery style novelty fader"
            />
            <div className="flex justify-between text-[11px] text-[#9a9aa0]">
              <span className={novelty < 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Familiar classics
              </span>
              <span className={novelty >= 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Hidden gems
              </span>
            </div>
          </div>

          {/* Fader 2: Diversity */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#f2efe6] font-medium">Genre Variety</span>
              <span className="font-mono text-[#f5a524]">{Math.round(diversity * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={diversity}
              onChange={(e) => setDiversity(parseFloat(e.target.value))}
              className="w-full accent-[#f5a524] cursor-pointer"
              aria-label="Genre variety diversity fader"
            />
            <div className="flex justify-between text-[11px] text-[#9a9aa0]">
              <span className={diversity < 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Focused match
              </span>
              <span className={diversity >= 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Eclectic mix
              </span>
            </div>
          </div>

          {/* Fader 3: Recency */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-[#f2efe6] font-medium">Release Era</span>
              <span className="font-mono text-[#f5a524]">{Math.round(recency * 100)}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={recency}
              onChange={(e) => setRecency(parseFloat(e.target.value))}
              className="w-full accent-[#f5a524] cursor-pointer"
              aria-label="Release era recency fader"
            />
            <div className="flex justify-between text-[11px] text-[#9a9aa0]">
              <span className={recency < 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Timeless
              </span>
              <span className={recency >= 0.5 ? "text-[#f2efe6] font-semibold" : ""}>
                Recent releases
              </span>
            </div>
          </div>

          {/* Genre Filter Chips */}
          <div className="flex flex-col gap-2 pt-2 border-t border-[#26282e]">
            <span className="text-xs text-[#f2efe6] font-medium">Genre Filter</span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setSelectedGenre(null)}
                className={`px-2.5 py-1 rounded-full text-xs font-mono transition-colors cursor-pointer ${
                  selectedGenre === null
                    ? "bg-[#f5a524] text-black font-semibold"
                    : "bg-[#26282e]/40 text-[#9a9aa0] hover:text-[#f2efe6]"
                }`}
              >
                All
              </button>
              {GENRES.map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setSelectedGenre(selectedGenre === g ? null : g)}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono transition-colors cursor-pointer ${
                    selectedGenre === g
                      ? "bg-[#f5a524] text-black font-semibold"
                      : "bg-[#26282e]/40 text-[#9a9aa0] hover:text-[#f2efe6]"
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          {/* Decade Filter Chips */}
          <div className="flex flex-col gap-2 pt-2 border-t border-[#26282e]">
            <span className="text-xs text-[#f2efe6] font-medium">Decade Filter</span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setSelectedDecade(null)}
                className={`px-2.5 py-1 rounded-full text-xs font-mono transition-colors cursor-pointer ${
                  selectedDecade === null
                    ? "bg-[#f5a524] text-black font-semibold"
                    : "bg-[#26282e]/40 text-[#9a9aa0] hover:text-[#f2efe6]"
                }`}
              >
                All
              </button>
              {DECADES.map((d) => (
                <button
                  key={d}
                  type="button"
                  onClick={() => setSelectedDecade(selectedDecade === d ? null : d)}
                  className={`px-2.5 py-1 rounded-full text-xs font-mono transition-colors cursor-pointer ${
                    selectedDecade === d
                      ? "bg-[#f5a524] text-black font-semibold"
                      : "bg-[#26282e]/40 text-[#9a9aa0] hover:text-[#f2efe6]"
                  }`}
                >
                  {d}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Live Posters Grid */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          <div className="flex items-center justify-between text-xs text-[#9a9aa0] font-mono">
            <span>
              {loading ? "Reordering films..." : `Showing ${movies.length} tuned films`}
            </span>
          </div>

          {loading && movies.length === 0 ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="w-full aspect-[2/3] rounded-lg bg-[#1c1c21] border border-[#26282e] animate-pulse" />
                  <div className="w-3/4 h-3 rounded bg-[#1c1c21] animate-pulse" />
                  <div className="w-1/2 h-2.5 rounded bg-[#1c1c21] animate-pulse" />
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {movies.map((m) => (
                <MoviePosterCard key={m.movieId} movie={m} />
              ))}
            </div>
          )}

          {movies.length === 0 && !loading && (
            <div className="p-12 text-center rounded-2xl bg-[#121316] border border-[#26282e] text-[#9a9aa0]">
              <p className="text-sm">No films match your active filters. Try broadening your criteria.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
