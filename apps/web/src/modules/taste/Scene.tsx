"use client";
import React, { useState, useEffect } from "react";
import { Sparkles, ArrowRight } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { MoviePosterCard } from "../../core/MoviePosterCard";
import type { MovieCard } from "@cinematch/api-client";

export const TasteScene: React.FC<{ progress?: number }> = () => {
  const [picks, setPicks] = useState<MovieCard[]>([]);
  const [loading, setLoading] = useState(true);

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
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const jumpToForYou = () => {
    const el = document.querySelector("#for-you");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col items-center gap-6 px-4 py-8">
      {/* Header and Progress Indicator */}
      <div className="flex flex-col sm:flex-row items-center justify-between w-full border-b border-[#26282e] pb-4 gap-4">
        <div className="flex flex-col text-center sm:text-left gap-1">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            02/ Taste
          </span>
          <h2 className="text-xl sm:text-2xl font-bold text-[#f2efe6]">
            Pick a few movies you love
          </h2>
          <p className="text-xs sm:text-sm text-[#9a9aa0]">
            Rate five films across genres to calibrate your personal recommendations.
          </p>
        </div>

        {/* Dynamic Progress Ring & Action Button */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 font-mono text-xs text-[#f2efe6] bg-[#121316] px-3.5 py-1.5 rounded-full border border-[#26282e]">
            <Sparkles className="w-3.5 h-3.5 text-[#f5a524]" />
            <span>
              {picksCount >= 5 ? "5 of 5 picks" : `${picksCount} of 5 picked`}
            </span>
          </div>

          {picksCount >= 5 ? (
            <button
              type="button"
              onClick={jumpToForYou}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-[#f5a524] text-[#0b0b0c] font-bold text-xs uppercase tracking-wider hover:brightness-110 shadow-lg transition-all"
            >
              <span>Your picks are ready</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={jumpToForYou}
              className="text-xs font-mono uppercase tracking-wider text-[#9a9aa0] hover:text-[#f2efe6] transition-colors"
            >
              Skip to popular
            </button>
          )}
        </div>
      </div>

      {/* 18-Poster Grid */}
      {loading ? (
        <div className="py-20 text-center font-mono text-xs text-[#9a9aa0]">
          Loading curated films...
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
