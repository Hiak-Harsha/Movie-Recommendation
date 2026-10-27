"use client";
import React, { useState } from "react";
import Image from "next/image";
import { Bookmark, Star, Check } from "lucide-react";
import { TiltCard } from "./motion/TiltCard";
import { ProceduralPoster } from "./motion/ProceduralPoster";
import { useAppStore } from "./store";
import { api } from "./client";
import type { MovieCard } from "@cinematch/api-client";

interface MoviePosterCardProps {
  movie: MovieCard;
  badge?: string;
  reason?: string;
  onSelect?: () => void;
  className?: string;
}

export const MoviePosterCard: React.FC<MoviePosterCardProps> = ({
  movie,
  badge,
  reason,
  onSelect,
  className = "",
}) => {
  const [imageError, setImageError] = useState(false);
  const [isSaved, setIsSaved] = useState(false);
  const [activeRating, setActiveRating] = useState<number | null>(null);
  const [isRatingOpen, setIsRatingOpen] = useState(false);

  const setSelectedMovieId = useAppStore((s) => s.setSelectedMovieId);
  const updateLibraryCount = useAppStore((s) => s.updateLibraryCount);
  const incrementPicks = useAppStore((s) => s.incrementPicks);
  const setToast = useAppStore((s) => s.setToast);

  const handleCardClick = () => {
    if (onSelect) {
      onSelect();
    } else {
      setSelectedMovieId(movie.movieId);
    }
  };

  const handleSaveToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (isSaved) {
        setIsSaved(false);
        updateLibraryCount(-1);
        await api.removeFromMyWatchlist(movie.movieId);
        setToast({
          message: `Removed ${movie.display_title || movie.title} from library`,
          undoAction: () => {
            setIsSaved(true);
            updateLibraryCount(1);
            api.addToMyWatchlist(movie.movieId);
          },
        });
      } else {
        setIsSaved(true);
        updateLibraryCount(1);
        await api.addToMyWatchlist(movie.movieId);
        setToast({
          message: `Saved ${movie.display_title || movie.title} to library`,
          undoAction: () => {
            setIsSaved(false);
            updateLibraryCount(-1);
            api.removeFromMyWatchlist(movie.movieId);
          },
        });
      }
    } catch {
      // Revert optimistic state
      setIsSaved((prev) => !prev);
    }
  };

  const handleRate = async (stars: number, e: React.MouseEvent) => {
    e.stopPropagation();
    setActiveRating(stars);
    setIsRatingOpen(false);
    incrementPicks();
    try {
      await api.submitMyRating(movie.movieId, stars);
      setToast({
        message: `Rated ${movie.display_title || movie.title} ${stars} stars`,
      });
    } catch (err) {
      console.error(err);
    }
  };

  const posterUrl = movie.poster_path
    ? (movie.poster_path.startsWith("http")
        ? movie.poster_path
        : `https://image.tmdb.org/t/p/w342${movie.poster_path}`)
    : null;

  return (
    <div className={`group flex flex-col w-full max-w-[220px] select-none ${className}`}>
      {/* 2:3 Portrait Poster Box with Scrim and Badge */}
      <TiltCard className="w-full aspect-[2/3] rounded-lg overflow-hidden bg-[#121316] border border-[#26282e] shadow-md group-hover:border-[#f5a524]/60 transition-colors">
        <div
          role="button"
          tabIndex={0}
          onClick={handleCardClick}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              handleCardClick();
            }
          }}
          className="w-full h-full cursor-pointer relative block focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f5a524]"
          aria-label={`View details for ${movie.display_title || movie.title}`}
        >
          {posterUrl && !imageError ? (
            <Image
              src={posterUrl}
              alt={movie.display_title || movie.title}
              fill
              sizes="(max-width: 640px) 160px, (max-width: 1024px) 200px, 240px"
              className="object-cover object-center group-hover:scale-105 transition-transform duration-500"
              onError={() => setImageError(true)}
              loading="lazy"
            />
          ) : (
            <ProceduralPoster
              movieId={movie.movieId}
              title={movie.display_title || movie.title}
              year={movie.year}
              genres={movie.genres}
            />
          )}

          {/* Corner Badge on Scrim */}
          {badge && (
            <div
              aria-label={badge}
              className="absolute top-2 left-2 z-10 px-2 py-0.5 rounded text-[10px] font-mono tracking-wider uppercase font-semibold bg-[#0b0b0c]/80 backdrop-blur-sm text-[#f5a524] border border-[#f5a524]/30"
            >
              {badge}
            </div>
          )}

          {/* Quick Save Pill on Poster */}
          <button
            type="button"
            onClick={handleSaveToggle}
            className={`absolute top-2 right-2 z-10 p-1.5 rounded-full backdrop-blur-md transition-all ${
              isSaved
                ? "bg-[#f5a524] text-[#0b0b0c]"
                : "bg-[#0b0b0c]/70 text-[#f2efe6] hover:bg-[#f5a524] hover:text-[#0b0b0c] opacity-80 group-hover:opacity-100"
            }`}
            aria-label={isSaved ? "Remove from watchlist" : "Save to watchlist"}
          >
            {isSaved ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : <Bookmark className="w-3.5 h-3.5" />}
          </button>
        </div>
      </TiltCard>

      {/* Reserved Typography & Metadata Area (Below poster, never overlapping) */}
      <div className="pt-2.5 flex flex-col gap-1">
        <h3
          title={movie.display_title || movie.title}
          className="text-xs font-semibold text-[#f2efe6] line-clamp-2 leading-tight group-hover:text-[#f5a524] transition-colors"
        >
          {movie.display_title || movie.title}
        </h3>

        <div className="flex items-center justify-between text-[11px] font-mono text-[#9a9aa0]">
          <span>{movie.year || "—"}</span>
          {movie.vote_average ? (
            <span className="flex items-center gap-1 text-[#f2efe6]">
              <Star className="w-3 h-3 fill-[#f5a524] text-[#f5a524]" />
              {movie.vote_average.toFixed(1)}
            </span>
          ) : null}
        </div>

        {/* Structured Reason (Plain words) */}
        {reason && (
          <p className="text-[10px] text-[#9a9aa0] line-clamp-1 italic">
            {reason}
          </p>
        )}

        {/* Reserved Action Strip: Star rating on card */}
        <div className="flex items-center justify-between pt-1 border-t border-[#26282e]/40">
          <div className="flex items-center gap-0.5" role="group" aria-label="Rate movie">
            {[1, 2, 3, 4, 5].map((s) => (
              <button
                key={s}
                type="button"
                onClick={(e) => handleRate(s, e)}
                className="p-0.5 text-[#9a9aa0] hover:text-[#f5a524] transition-colors focus:outline-none focus:text-[#f5a524]"
                aria-label={`Rate ${s} stars`}
              >
                <Star
                  className={`w-3 h-3 ${
                    activeRating && activeRating >= s
                      ? "fill-[#f5a524] text-[#f5a524]"
                      : "text-current"
                  }`}
                />
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={handleSaveToggle}
            className="text-[10px] font-mono uppercase tracking-wider text-[#9a9aa0] hover:text-[#f2efe6] transition-colors"
          >
            {isSaved ? "Saved" : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
};
