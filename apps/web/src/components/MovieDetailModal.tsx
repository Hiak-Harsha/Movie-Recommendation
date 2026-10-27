"use client";

import React, { useEffect, useState } from "react";
import { useStore } from "@/lib/store";
import { apiClient, MediaDetails } from "@cinematch/api-client";
import { X, Star, Bookmark, Film, Play, Clock, Sparkles } from "lucide-react";

export default function MovieDetailModal() {
  const {
    selectedMovieId,
    setSelectedMovieId,
    userId,
    setToast,
    incrementRatings,
    updateWatchlistCount,
    setSeedMovieId,
    setActiveTab,
  } = useStore();

  const [media, setMedia] = useState<MediaDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [userRating, setUserRating] = useState<number | null>(null);
  const [inWatchlist, setInWatchlist] = useState(false);

  useEffect(() => {
    if (!selectedMovieId) {
      setMedia(null);
      return;
    }

    setLoading(true);
    apiClient
      .getMediaDetails(selectedMovieId)
      .then((data) => {
        setMedia(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    // Check user watchlist & rating
    apiClient.getUserWatchlist(userId).then((items) => {
      setInWatchlist(items.some((i) => i.movieId === selectedMovieId));
    });

    apiClient.getUserRatings(userId).then((ratings) => {
      const match = ratings.find((r) => r.movieId === selectedMovieId);
      setUserRating(match ? match.rating : null);
    });
  }, [selectedMovieId, userId]);

  if (!selectedMovieId) return null;

  const handleRate = async (star: number) => {
    try {
      await apiClient.submitRating(userId, selectedMovieId, star);
      setUserRating(star);
      incrementRatings();
      setToast(`Rated "${media?.title}" ${star}★`);
    } catch (e: any) {
      setToast(e.message);
    }
  };

  const handleWatchlistToggle = async () => {
    try {
      if (inWatchlist) {
        await apiClient.removeFromWatchlist(userId, selectedMovieId);
        setInWatchlist(false);
        updateWatchlistCount(-1);
        setToast(`Removed from watchlist`);
      } else {
        await apiClient.addToWatchlist(userId, selectedMovieId);
        setInWatchlist(true);
        updateWatchlistCount(1);
        setToast(`Added to watchlist`);
      }
    } catch (e: any) {
      setToast(e.message);
    }
  };

  const handleExploreSimilar = () => {
    setSeedMovieId(selectedMovieId);
    setSelectedMovieId(null);
    setActiveTab("similar");
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-black/80 backdrop-blur-md">
      <div
        className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-[#121215] border border-zinc-800 shadow-2xl flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={() => setSelectedMovieId(null)}
          className="absolute top-4 right-4 z-20 p-2 rounded-full bg-black/60 hover:bg-black text-zinc-400 hover:text-white transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Media Backdrop / Hero Header */}
        <div className="relative aspect-[21/9] w-full bg-zinc-900 overflow-hidden">
          {media?.backdrop_url ? (
            <img
              src={media.backdrop_url}
              alt={media.title}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-r from-zinc-900 via-zinc-850 to-zinc-900 flex items-center justify-center">
              <Film className="w-12 h-12 text-zinc-700" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-[#121215] via-[#121215]/50 to-transparent" />
        </div>

        {/* Body Info */}
        <div className="p-6 -mt-12 relative z-10 space-y-6">
          <div className="flex flex-col sm:flex-row items-start gap-5">
            {/* Poster Thumbnail */}
            {media?.poster_url && (
              <img
                src={media.poster_url}
                alt={media.title}
                className="w-24 sm:w-32 aspect-[2/3] rounded-lg shadow-xl border border-zinc-700 object-cover shrink-0"
              />
            )}

            <div className="flex-1">
              <div className="flex items-center gap-2 text-xs font-mono text-amber-500 mb-1">
                <span>{media?.genres?.slice(0, 2).join(" • ") || "Cinema Selection"}</span>
                {media?.year && <span>• {media.year}</span>}
              </div>

              <h2 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {media?.title}
              </h2>

              <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-400 mt-2">
                {media?.runtime && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-zinc-500" />
                    <span>{media.runtime} mins</span>
                  </div>
                )}
                {media?.director && (
                  <div>
                    <span className="text-zinc-500">Director: </span>
                    <span className="text-zinc-200 font-medium">{media.director}</span>
                  </div>
                )}
                {media?.vote_average && (
                  <div className="flex items-center gap-1 text-amber-400 font-mono">
                    <Star className="w-3.5 h-3.5 fill-current" />
                    <span>{media.vote_average.toFixed(1)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Row */}
          <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-zinc-900/60 border border-zinc-800">
            {/* Rating Stars */}
            <div className="flex items-center gap-3">
              <span className="text-xs text-zinc-400 font-medium">Your Rating:</span>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => handleRate(star)}
                    className="p-1 hover:scale-125 transition-transform"
                  >
                    <Star
                      className={`w-4 h-4 ${
                        (userRating || 0) >= star
                          ? "fill-amber-400 text-amber-400"
                          : "text-zinc-600 hover:text-amber-400"
                      }`}
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Watchlist & Similar Actions */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleWatchlistToggle}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                  inWatchlist
                    ? "bg-amber-500 text-black shadow-md shadow-amber-500/20"
                    : "bg-zinc-800 hover:bg-zinc-700 text-zinc-200"
                }`}
              >
                <Bookmark className="w-3.5 h-3.5 fill-current" />
                <span>{inWatchlist ? "Watchlisted" : "Add to Watchlist"}</span>
              </button>

              <button
                onClick={handleExploreSimilar}
                className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-semibold transition-all cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>Find Similar</span>
              </button>
            </div>
          </div>

          {/* Overview / Plot */}
          <div>
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-2">
              Overview
            </h3>
            <p className="text-sm text-zinc-300 leading-relaxed">
              {media?.overview || "No synopsis available in catalog."}
            </p>
          </div>

          {/* Top Cast */}
          {media?.cast && media.cast.length > 0 && (
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-2">
                Top Cast
              </h3>
              <div className="flex flex-wrap gap-2">
                {media.cast.map((actor: any, idx: number) => (
                  <div
                    key={idx}
                    className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 text-xs text-zinc-300"
                  >
                    <span className="font-medium text-white">{actor.name}</span>
                    {actor.character && (
                      <span className="text-zinc-500 text-[11px] ml-1.5">as {actor.character}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* YouTube Trailer Embed (if available) */}
          {media?.trailer_key && (
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-2 flex items-center gap-1.5">
                <Play className="w-3 h-3 text-red-500 fill-current" />
                <span>Official Trailer</span>
              </h3>
              <div className="relative aspect-[16/9] w-full rounded-xl overflow-hidden border border-zinc-800 bg-black">
                <iframe
                  src={`https://www.youtube-nocookie.com/embed/${media.trailer_key}`}
                  title={`${media.title} Trailer`}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                  className="w-full h-full"
                />
              </div>
            </div>
          )}

          {/* Streaming Availability (US) */}
          {media?.streaming_providers && media.streaming_providers.length > 0 && (
            <div>
              <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-500 mb-2">
                Where to Watch
              </h3>
              <div className="flex flex-wrap gap-2">
                {media.streaming_providers.map((provider: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-full bg-zinc-800/80 border border-zinc-700/80 text-xs text-zinc-200"
                  >
                    {provider}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
