"use client";
import React, { useState, useEffect } from "react";
import { Sparkles, ArrowRight, RefreshCw } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { MoviePosterCard } from "../../core/MoviePosterCard";
import { scrollToScene } from "../../core/motion/LenisProvider";
import type { MovieCard } from "@cinematch/api-client";

export const TasteScene: React.FC = () => {
  const [picks, setPicks] = useState<MovieCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const picksCount = useAppStore((s) => s.picksCount);

  useEffect(() => {
    let mounted = true;

    api.getOnboardingPicks()
      .then((res) => {
        if (mounted) {
          setPicks(res.movies || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load onboarding picks:", err);
        if (mounted) {
          setError("Failed to load curated films. Tap below to retry.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [reloadKey]);

  const jumpToForYou = () => {
    scrollToScene("#for-you");
  };

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col items-center gap-6 px-4 py-6">
      {/* Header and Progress Indicator */}
      <div className="flex flex-col sm:flex-row items-center justify-between w-full border-b border-[#26282e] pb-4 gap-4">
        <div className="flex flex-col text-center sm:text-left gap-1">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            02/ Taste
          </span>
          <h2 className="text-fluid-h2 font-display font-bold text-[#f2efe6]">
            Pick a few movies you love
          </h2>
          <p className="text-xs sm:text-sm text-[#9a9aa0] text-fluid-body">
            Rate five films across genres to calibrate your personal recommendations.
          </p>
        </div>

        {/* Dynamic Progress Ring & Action Button with reserved width */}
        <div className="flex items-center gap-3 shrink-0">
          <div className="flex items-center gap-2 font-mono text-xs text-[#f2efe6] bg-[#121316] px-3.5 py-1.5 rounded-full border border-[#26282e]">
            <Sparkles className="w-3.5 h-3.5 text-[#f5a524]" />
            <span className="tabular-nums">
              {picksCount >= 5 ? "5 of 5 picks" : `${picksCount} of 5 picked`}
            </span>
          </div>

          <div className="min-w-[150px] flex justify-end">
            {picksCount >= 5 ? (
              <button
                type="button"
                onClick={jumpToForYou}
                className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#f5a524] text-[#0b0b0c] font-bold text-xs uppercase tracking-wider hover:brightness-110 shadow-lg shadow-amber-500/20 active:scale-95 transition-all cursor-pointer"
              >
                <span>Picks ready</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                type="button"
                onClick={jumpToForYou}
                className="text-xs font-mono uppercase tracking-wider text-[#9a9aa0] hover:text-[#f2efe6] transition-colors cursor-pointer py-2 px-3"
              >
                Skip to popular
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error state with retry */}
      {error && !loading && (
        <div className="py-12 flex flex-col items-center gap-3 text-center">
          <p className="text-sm font-mono text-[#9a9aa0]">{error}</p>
          <button
            type="button"
            onClick={() => {
              setLoading(true);
              setError(null);
              setReloadKey((k) => k + 1);
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#121316] border border-[#26282e] hover:border-[#f5a524] text-xs font-mono text-[#f2efe6] transition-all cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5 text-[#f5a524]" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* 18-Poster Grid with Layout-Matched Skeletons */}
      {loading ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 w-full">
          {Array.from({ length: 18 }).map((_, i) => (
            <div key={i} className="flex flex-col gap-2 w-full max-w-[220px] mx-auto animate-pulse">
              <div className="w-full aspect-[2/3] rounded-lg bg-[#121316] border border-[#26282e]/50" />
              <div className="h-3 w-3/4 rounded bg-[#1c1c21]" />
              <div className="h-2 w-1/2 rounded bg-[#1c1c21]/70" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 w-full">
          {picks.slice(0, 18).map((movie) => (
            <MoviePosterCard
              key={movie.movieId}
              movie={movie}
              className="mx-auto"
            />
          ))}
        </div>
      )}
    </div>
  );
};
