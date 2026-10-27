"use client";
import React, { useState, useEffect } from "react";
import { Sparkles, EyeOff } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { MoviePosterCard } from "../../core/MoviePosterCard";
import type { ShelfItem } from "@cinematch/api-client";

export const ForYouScene: React.FC<{ progress?: number }> = () => {
  const [shelves, setShelves] = useState<ShelfItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());

  const setToast = useAppStore((s) => s.setToast);
  const picksCount = useAppStore((s) => s.picksCount);

  useEffect(() => {
    let mounted = true;
    api.getMyShelves()
      .then((res) => {
        if (mounted) {
          setShelves(res.shelves || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load shelves:", err);
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [picksCount]);

  const handleDismiss = async (movieId: number, title: string) => {
    setDismissedIds((prev) => new Set(prev).add(movieId));
    api.recordEvent(movieId, "dismiss");

    setToast({
      message: `Hidden "${title}" from recommendations`,
      undoAction: () => {
        setDismissedIds((prev) => {
          const next = new Set(prev);
          next.delete(movieId);
          return next;
        });
      },
    });
  };

  return (
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-10 px-4 py-8">
      {/* Eyebrow and Headline */}
      <div className="flex flex-col gap-2">
        <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
          03/ For You
        </span>
        <h2 className="text-2xl sm:text-3xl font-bold text-[#f2efe6] tracking-tight">
          Curated for your evening
        </h2>
        <p className="text-sm text-[#9a9aa0] max-w-xl">
          Films chosen to match your active taste profile, films that resemble your top ratings, and critically acclaimed gems.
        </p>
      </div>

      {loading ? (
        <div className="py-24 text-center font-mono text-xs text-[#9a9aa0]">
          Curating your personalized lineup...
        </div>
      ) : shelves.length === 0 ? (
        <div className="py-16 text-center text-sm text-[#9a9aa0]">
          Pick a few films in the Taste section to unlock personalized shelves.
        </div>
      ) : (
        <div className="flex flex-col gap-10">
          {shelves.map((shelf) => {
            const activeMovies = shelf.movies.filter(
              (m) => !dismissedIds.has(m.movieId)
            );
            if (activeMovies.length === 0) return null;

            return (
              <div key={shelf.id} className="flex flex-col gap-3">
                {/* Shelf Title & Plain Reason */}
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 border-b border-[#26282e]/50 pb-2">
                  <h3 className="text-base sm:text-lg font-bold text-[#f2efe6] flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#f5a524]" />
                    {shelf.title}
                  </h3>
                  <span className="text-xs text-[#9a9aa0] italic">
                    {shelf.reason}
                  </span>
                </div>

                {/* Film-Strip Horizontal Scroll Rail */}
                <div
                  className="flex gap-4 overflow-x-auto pb-4 pt-1 snap-x scrollbar-thin scrollbar-thumb-[#26282e]"
                  data-lenis-prevent="true"
                >
                  {activeMovies.map((movie) => (
                    <div
                      key={movie.movieId}
                      className="flex-shrink-0 w-36 sm:w-44 md:w-48 snap-start relative group/item"
                    >
                      <MoviePosterCard movie={movie} />

                      {/* Not Interested Hover Button */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDismiss(movie.movieId, movie.display_title || movie.title);
                        }}
                        className="opacity-0 group-hover/item:opacity-100 transition-opacity absolute top-2 left-2 z-20 p-1 rounded-full bg-[#0b0b0c]/80 text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#b3202a]"
                        title="Not interested"
                        aria-label={`Not interested in ${movie.display_title || movie.title}`}
                      >
                        <EyeOff className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
