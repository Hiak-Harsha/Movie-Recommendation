"use client";

import React, { useState } from "react";
import { useStore } from "@/lib/store";
import { apiClient, MovieCard as MovieCardType } from "@cinematch/api-client";
import { surfaceCopy } from "@/copy/en";
import { Bookmark, Star, Sparkles, Film } from "lucide-react";

interface MovieCardProps {
  movie: MovieCardType;
  onRatingChanged?: (movieId: number, rating: number) => void;
  onWatchlistToggled?: (movieId: number, saved: boolean) => void;
  reasonBadge?: string;
}

export default function MovieCard({
  movie,
  onRatingChanged,
  onWatchlistToggled,
  reasonBadge,
}: MovieCardProps) {
  const { userId, setSelectedMovieId, setToast, incrementRatings, updateWatchlistCount } = useStore();
  const [isSaved, setIsSaved] = useState(movie.is_watchlist || false);
  const [currentRating, setCurrentRating] = useState<number | null>(movie.user_rating || null);
  const [hoverRating, setHoverRating] = useState<number | null>(null);

  const posterUrl = movie.poster_path
    ? `https://image.tmdb.org/t/p/w342${movie.poster_path}`
    : null;

  const handleToggleWatchlist = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (isSaved) {
        await apiClient.removeFromWatchlist(userId, movie.movieId);
        setIsSaved(false);
        updateWatchlistCount(-1);
        setToast(`Removed "${movie.display_title}" from lineup`);
        onWatchlistToggled?.(movie.movieId, false);
      } else {
        await apiClient.addToWatchlist(userId, movie.movieId);
        setIsSaved(true);
        updateWatchlistCount(1);
        setToast(`Saved "${movie.display_title}" to lineup`);
        onWatchlistToggled?.(movie.movieId, true);
      }
    } catch (err: any) {
      setToast(`Error saving movie: ${err.message}`);
    }
  };

  const handleRate = async (ratingVal: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiClient.submitRating(userId, movie.movieId, ratingVal);
      setCurrentRating(ratingVal);
      incrementRatings();
      setToast(`Rated "${movie.display_title}" ${ratingVal}★`);
      onRatingChanged?.(movie.movieId, ratingVal);
    } catch (err: any) {
      setToast(`Error rating movie: ${err.message}`);
    }
  };

  // Determine label
  const displayBadge = reasonBadge || (
    movie.explanation?.dominant_signal?.startsWith("collab")
      ? surfaceCopy.card.badges.topPick
      : movie.explanation?.dominant_signal?.startsWith("content")
      ? surfaceCopy.card.badges.fanFavorite
      : movie.vote_average && movie.vote_average >= 4.0
      ? surfaceCopy.card.badges.topPick
      : null
  );

  return (
    <div
      onClick={() => setSelectedMovieId(movie.movieId)}
      className="group relative flex flex-col rounded-xl bg-[#121316] hover:bg-[#1a1b20] border border-[#26282e] hover:border-zinc-700 transition-all duration-300 hover:shadow-2xl hover:shadow-black/60 overflow-hidden cursor-pointer"
      title={movie.display_title}
      aria-label={`${movie.display_title} (${movie.year || "Classic"})`}
    >
      {/* 2:3 Portrait Poster Area */}
      <div className="relative aspect-[2/3] w-full bg-zinc-950 overflow-hidden select-none">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={movie.display_title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          /* Deterministic 2:3 Fallback Art */
          <div className="w-full h-full flex flex-col justify-between p-4 bg-gradient-to-b from-[#18191f] via-[#121316] to-[#0b0b0c] text-center border-b border-[#26282e]">
            <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500">
              <Film className="w-3.5 h-3.5 text-amber-500" />
              <span>{movie.year || "Cinema"}</span>
            </div>
            <div className="my-auto py-2">
              <p className="text-base font-bold text-zinc-100 line-clamp-3 leading-snug">
                {movie.display_title}
              </p>
              <p className="text-xs text-amber-400/90 mt-2 line-clamp-1 font-medium">
                {movie.genres?.slice(0, 2).join(" • ") || "Feature Film"}
              </p>
            </div>
            <div className="text-[10px] font-mono text-zinc-600">
              CINEMATCH SELECTION
            </div>
          </div>
        )}

        {/* Poster Top Badge (on Scrim) */}
        {displayBadge && (
          <div className="absolute top-2.5 left-2.5 z-10">
            <span className="px-2 py-0.5 rounded-md bg-black/80 backdrop-blur-md border border-amber-500/30 text-[10px] font-medium text-amber-400 flex items-center gap-1 shadow-md">
              <Sparkles className="w-3 h-3 text-amber-400" />
              {displayBadge}
            </span>
          </div>
        )}

        {/* Quick Save Bookmark on Poster */}
        <button
          onClick={handleToggleWatchlist}
          className={`absolute top-2.5 right-2.5 z-10 w-7 h-7 rounded-full flex items-center justify-center backdrop-blur-md transition-all duration-200 cursor-pointer shadow-md ${
            isSaved
              ? "bg-amber-500 text-black shadow-amber-500/30"
              : "bg-black/60 text-zinc-300 hover:text-white hover:bg-black/90 border border-white/10"
          }`}
          title={isSaved ? "Saved in lineup" : "Save to lineup"}
          aria-label={isSaved ? "Saved" : "Save"}
        >
          <Bookmark className={`w-3.5 h-3.5 ${isSaved ? "fill-black" : ""}`} />
        </button>
      </div>

      {/* Card Info Below Poster (Card Anatomy: Never over poster) */}
      <div className="p-3.5 flex flex-col justify-between flex-1 gap-2">
        <div>
          {/* Title and Year */}
          <h3 className="text-sm font-semibold text-zinc-100 group-hover:text-amber-400 transition-colors line-clamp-2 leading-snug">
            {movie.display_title}
          </h3>
          <div className="flex items-center gap-2 mt-1 text-xs text-zinc-400 font-mono">
            <span>{movie.year || "Classic"}</span>
            {movie.vote_average && (
              <>
                <span>•</span>
                <span className="flex items-center gap-1 text-amber-400 font-semibold">
                  <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                  {movie.vote_average.toFixed(1)}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Reserved Action Strip: Star Rating (Never shifts text on hover) */}
        <div className="pt-2 border-t border-[#26282e]/80 flex items-center justify-between text-xs text-zinc-500">
          <div className="flex items-center gap-0.5">
            {[1, 2, 3, 4, 5].map((star) => {
              const active = hoverRating !== null ? star <= hoverRating : (currentRating || 0) >= star;
              return (
                <button
                  key={star}
                  type="button"
                  onMouseEnter={() => setHoverRating(star)}
                  onMouseLeave={() => setHoverRating(null)}
                  onClick={(e) => handleRate(star, e)}
                  className="p-0.5 hover:scale-125 transition-transform cursor-pointer"
                  title={`Rate ${star} stars`}
                  aria-label={`Rate ${star} stars`}
                >
                  <Star
                    className={`w-3.5 h-3.5 ${
                      active
                        ? "fill-amber-400 text-amber-400"
                        : "text-zinc-600 hover:text-zinc-400"
                    }`}
                  />
                </button>
              );
            })}
          </div>

          <span className="text-[11px] font-mono text-zinc-500 truncate max-w-[90px]">
            {movie.genres?.[0] || "Film"}
          </span>
        </div>
      </div>
    </div>
  );
}
