"use client";
import React, { useEffect, useState, useCallback, useRef } from "react";
import { X, Star, Bookmark, Clock, RefreshCw } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { ProceduralPoster } from "../../core/motion/ProceduralPoster";
import type { MovieDetailResponse } from "@cinematch/api-client";

export const DetailOverlay: React.FC = () => {
  const selectedMovieId = useAppStore((s) => s.selectedMovieId);
  const setSelectedMovieId = useAppStore((s) => s.setSelectedMovieId);
  const incrementPicks = useAppStore((s) => s.incrementPicks);
  const updateLibraryCount = useAppStore((s) => s.updateLibraryCount);
  const setToast = useAppStore((s) => s.setToast);

  const [detail, setDetail] = useState<MovieDetailResponse | null>(null);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [inWatchlist, setInWatchlist] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const previousFocusRef = useRef<HTMLElement | null>(null);

  const loading = Boolean(selectedMovieId && detail?.movie?.movieId !== selectedMovieId && !error);

  // Close on Esc and restore focus
  const handleClose = useCallback(() => {
    setSelectedMovieId(null);
    setDetail(null);
    setError(null);
    if (previousFocusRef.current) {
      previousFocusRef.current.focus();
    }
  }, [setSelectedMovieId]);

  useEffect(() => {
    if (selectedMovieId) {
      previousFocusRef.current = document.activeElement as HTMLElement | null;

      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === "Escape") {
          handleClose();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }
  }, [selectedMovieId, handleClose]);

  useEffect(() => {
    if (!selectedMovieId) return;

    let mounted = true;

    fetch(`/api/movies/${selectedMovieId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Movie not found");
        return res.json() as Promise<MovieDetailResponse>;
      })
      .then((data) => {
        if (mounted) {
          setDetail(data);
        }
      })
      .catch((err) => {
        console.error("Failed to load movie detail:", err);
        if (mounted) setError("Could not load movie information.");
      });

    // Check rating & watchlist status
    api.getMyWatchlist().then((items) => {
      if (mounted) {
        setInWatchlist(items.some((i) => i.movieId === selectedMovieId));
      }
    });

    api.getMyRatings().then((ratings) => {
      if (mounted) {
        const match = ratings.find((r) => r.movieId === selectedMovieId);
        setUserRating(match ? match.rating : null);
      }
    });

    return () => {
      mounted = false;
    };
  }, [selectedMovieId]);

  if (!selectedMovieId) return null;

  const movie = detail?.movie;
  const media = detail?.media;

  const handleRate = async (star: number) => {
    if (!movie) return;
    try {
      await api.submitMyRating(movie.movieId, star);
      setUserRating(star);
      incrementPicks();
      setToast({ message: `Rated "${movie.title}" ${star}★` });
    } catch (e: unknown) {
      setToast({ message: (e as Error).message || "Failed to submit rating" });
    }
  };

  const handleWatchlistToggle = async () => {
    if (!movie) return;
    try {
      if (inWatchlist) {
        await api.removeFromMyWatchlist(movie.movieId);
        setInWatchlist(false);
        updateLibraryCount(-1);
        setToast({ message: `Removed from your cinema lineup` });
      } else {
        await api.addToMyWatchlist(movie.movieId);
        setInWatchlist(true);
        updateLibraryCount(1);
        setToast({ message: `Saved "${movie.title}" to your cinema lineup` });
      }
    } catch (e: unknown) {
      setToast({ message: (e as Error).message || "Watchlist update failed" });
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={movie?.title || "Film details"}
      className="fixed inset-0 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md transition-opacity duration-200"
      style={{ zIndex: 60 }}
      onClick={handleClose}
    >
      <div
        className="relative w-full max-w-4xl max-h-[94vh] sm:max-h-[90vh] overflow-y-auto rounded-3xl bg-[#121316] border border-[#26282e] shadow-2xl flex flex-col transition-all duration-200"
        data-lenis-prevent="true"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          onClick={handleClose}
          className="absolute top-4 right-4 z-30 p-2.5 rounded-full bg-black/60 hover:bg-black text-[#9a9aa0] hover:text-[#f2efe6] transition-colors cursor-pointer"
          aria-label="Close details"
        >
          <X className="w-5 h-5" />
        </button>

        {error ? (
          <div className="p-16 flex flex-col items-center gap-3 text-center">
            <p className="text-sm font-mono text-red-400">{error}</p>
            <button
              type="button"
              onClick={handleClose}
              className="px-4 py-2 rounded-full bg-[#1c1c21] border border-[#26282e] text-xs font-mono text-[#f2efe6] hover:border-[#f5a524]"
            >
              Close
            </button>
          </div>
        ) : loading ? (
          <div className="p-20 text-center font-mono text-xs text-[#9a9aa0] flex flex-col items-center gap-3">
            <RefreshCw className="w-6 h-6 animate-spin text-[#f5a524]" />
            <span>Loading movie universe...</span>
          </div>
        ) : movie ? (
          <>
            {/* Backdrop / Header Banner */}
            <div className="relative w-full h-52 sm:h-72 overflow-hidden bg-gradient-to-b from-[#1b1c20] to-[#121316]">
              {media?.backdrop_url ? (
                /* eslint-disable-next-line @next/next/no-img-element */
                <img
                  src={media.backdrop_url}
                  alt={movie.title}
                  className="w-full h-full object-cover opacity-35"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-r from-amber-950/20 via-zinc-900 to-black/60" />
              )}
              {/* Bottom Scrim */}
              <div className="absolute inset-0 bg-gradient-to-t from-[#121316] via-[#121316]/60 to-transparent" />
            </div>

            {/* Content Body */}
            <div className="relative px-5 sm:px-10 pb-8 -mt-24 sm:-mt-36 z-10 flex flex-col gap-6">
              <div className="flex flex-col sm:flex-row gap-5 items-start">
                {/* 2:3 Poster Frame */}
                <div className="w-32 sm:w-44 shrink-0 aspect-[2/3] rounded-2xl overflow-hidden shadow-2xl border border-[#26282e] bg-[#0b0b0c]">
                  {media?.poster_url ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={media.poster_url}
                      alt={movie.title}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <ProceduralPoster
                      movieId={movie.movieId}
                      title={movie.title}
                      year={movie.year}
                      genres={movie.genres}
                      className="w-full h-full object-cover"
                    />
                  )}
                </div>

                {/* Metadata Column */}
                <div className="flex-1 flex flex-col gap-2.5 pt-2">
                  <div className="flex flex-wrap items-center gap-1.5">
                    {movie.genres?.map((g: string) => (
                      <span
                        key={g}
                        className="px-2.5 py-0.5 rounded-full text-xs font-mono bg-[#26282e]/60 text-[#f5a524]"
                      >
                        {g}
                      </span>
                    ))}
                  </div>

                  <h1 className="text-xl sm:text-3xl font-bold text-[#f2efe6] tracking-tight">
                    {movie.title}
                  </h1>

                  <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-[#9a9aa0]">
                    {movie.year && <span>{movie.year}</span>}
                    {media?.runtime && (
                      <span className="flex items-center gap-1">
                        <Clock className="w-3.5 h-3.5" />
                        {media.runtime}m
                      </span>
                    )}
                    <span className="text-amber-400 font-semibold">
                      ★ {movie.vote_average ? movie.vote_average.toFixed(1) : "4.0"} avg
                    </span>
                  </div>

                  {/* Star Rating & Watchlist Actions */}
                  <div className="flex flex-wrap items-center gap-3 pt-2">
                    <div className="flex items-center gap-1 bg-[#1b1c20] px-3 py-1.5 rounded-xl border border-[#26282e]">
                      <span className="text-xs font-mono text-[#9a9aa0] mr-1">Your rating:</span>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          onClick={() => handleRate(star)}
                          className="p-1 hover:scale-110 transition-transform cursor-pointer"
                          aria-label={`Rate ${star} stars`}
                        >
                          <Star
                            className={`w-4 h-4 ${
                              userRating && userRating >= star
                                ? "text-[#f5a524] fill-[#f5a524]"
                                : "text-zinc-600 hover:text-amber-400"
                            }`}
                          />
                        </button>
                      ))}
                    </div>

                    <button
                      type="button"
                      onClick={handleWatchlistToggle}
                      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono transition-all cursor-pointer ${
                        inWatchlist
                          ? "bg-amber-500 text-black font-semibold shadow-lg shadow-amber-500/20"
                          : "bg-[#1b1c20] hover:bg-[#26282e] text-[#f2efe6] border border-[#26282e]"
                      }`}
                    >
                      <Bookmark className="w-3.5 h-3.5" />
                      <span>{inWatchlist ? "Saved in lineup" : "Save to lineup"}</span>
                    </button>
                  </div>
                </div>
              </div>

              {/* Synopsis / Overview */}
              {media?.overview && (
                <div className="flex flex-col gap-1.5">
                  <h3 className="text-xs font-mono uppercase tracking-wider text-[#f5a524]">
                    Synopsis
                  </h3>
                  <p className="text-xs sm:text-sm text-[#f2efe6]/85 leading-relaxed max-w-3xl">
                    {media.overview}
                  </p>
                </div>
              )}

              {/* Cast & Director */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-3 border-t border-[#26282e]">
                {media?.director && (
                  <div className="flex flex-col gap-1">
                    <span className="text-xs font-mono uppercase text-[#9a9aa0]">Director</span>
                    <span className="text-sm font-semibold text-[#f2efe6]">{media.director}</span>
                  </div>
                )}

                {media?.cast && media.cast.length > 0 && (
                  <div className="flex flex-col gap-1 sm:col-span-2">
                    <span className="text-xs font-mono uppercase text-[#9a9aa0]">Cast</span>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {media.cast.slice(0, 6).map((c: { name: string; character?: string }, idx: number) => (
                        <span
                          key={idx}
                          className="px-2.5 py-1 rounded-lg text-xs bg-[#1b1c20] border border-[#26282e] text-[#f2efe6]"
                        >
                          <span className="font-semibold">{c.name}</span>
                          {c.character && (
                            <span className="text-[#9a9aa0] ml-1">as {c.character}</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Streaming Providers */}
              {media?.streaming_providers && media.streaming_providers.length > 0 && (
                <div className="flex flex-col gap-2 pt-3 border-t border-[#26282e]">
                  <span className="text-xs font-mono uppercase text-[#9a9aa0]">Where to watch</span>
                  <div className="flex flex-wrap gap-2">
                    {media.streaming_providers.map((p: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1 rounded-full text-xs font-mono bg-emerald-950/40 border border-emerald-500/30 text-emerald-300"
                      >
                        {p}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Trailer Embed */}
              {media?.trailer_key && (
                <div className="flex flex-col gap-2 pt-3 border-t border-[#26282e]">
                  <span className="text-xs font-mono uppercase text-[#9a9aa0]">Official Trailer</span>
                  <div className="aspect-video w-full max-w-2xl rounded-2xl overflow-hidden border border-[#26282e]">
                    <iframe
                      src={`https://www.youtube-nocookie.com/embed/${media.trailer_key}`}
                      title={`${movie.title} Trailer`}
                      className="w-full h-full"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                      allowFullScreen
                    />
                  </div>
                </div>
              )}
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
};
