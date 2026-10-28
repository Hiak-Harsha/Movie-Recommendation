"use client";
import React, { useState, useEffect } from "react";
import { Sparkles, RefreshCw } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { MoviePosterCard } from "../../core/MoviePosterCard";
import type { ShelfItem } from "@cinematch/api-client";

export const ForYouScene: React.FC = () => {
  const [shelves, setShelves] = useState<ShelfItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dismissedIds, setDismissedIds] = useState<Set<number>>(new Set());
  const [reloadKey, setReloadKey] = useState(0);

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
        if (mounted) {
          setError("Unable to load recommendation shelves. Tap to retry.");
          setLoading(false);
        }
      });

    return () => {
      mounted = false;
    };
  }, [picksCount, reloadKey]);

  const handleDismiss = (movieId: number, title: string) => {
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
    <div className="w-full max-w-7xl mx-auto flex flex-col gap-8 px-4 py-6">
      {/* Eyebrow and Headline */}
      <div className="flex flex-col gap-2">
        <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
          03/ For You
        </span>
        <h2 className="text-fluid-h2 font-display font-bold text-[#f2efe6] tracking-tight">
          Curated for your evening
        </h2>
        <p className="text-sm text-[#9a9aa0] max-w-xl text-fluid-body">
          Films chosen to match your active taste profile, films that resemble your top ratings, and critically acclaimed gems.
        </p>
      </div>

      {/* Error State */}
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

      {/* Skeletons while loading */}
      {loading ? (
        <div className="flex flex-col gap-8">
          {[1, 2].map((i) => (
            <div key={i} className="flex flex-col gap-3 animate-pulse">
              <div className="h-5 w-48 rounded bg-[#1c1c21]" />
              <div className="flex gap-4 overflow-hidden pt-1">
                {[1, 2, 3, 4, 5].map((j) => (
                  <div key={j} className="shrink-0 w-36 sm:w-44 md:w-48 aspect-[2/3] rounded-lg bg-[#121316] border border-[#26282e]/50" />
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : shelves.length === 0 ? (
        <div className="py-16 text-center text-sm text-[#9a9aa0] glass-panel rounded-2xl p-8 max-w-md mx-auto">
          Pick a few films in the Taste section to unlock personalized shelves.
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {shelves.map((shelf) => {
            const activeMovies = shelf.movies.filter(
              (m) => !dismissedIds.has(m.movieId)
            );
            if (activeMovies.length === 0) return null;

            return (
              <div key={shelf.id} className="flex flex-col gap-3">
                {/* Shelf Title & Reason (Stacks safely on narrow widths) */}
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-1 border-b border-[#26282e]/50 pb-2">
                  <h3 className="text-base sm:text-lg font-bold text-[#f2efe6] flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[#f5a524]" />
                    <span>{shelf.title}</span>
                  </h3>
                  <span className="text-xs text-[#9a9aa0] italic truncate max-w-md">
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
                      className="shrink-0 w-36 sm:w-44 md:w-48 snap-start transition-all duration-200"
                    >
                      <MoviePosterCard
                        movie={movie}
                        onDismiss={() =>
                          handleDismiss(
                            movie.movieId,
                            movie.display_title || movie.title
                          )
                        }
                      />
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
