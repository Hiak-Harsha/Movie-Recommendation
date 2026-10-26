"use client";

import React, { useState, useEffect } from "react";
import { MovieCard as MovieCardType, apiClient } from "@cinematch/api-client";
import { useStore } from "@/lib/store";
import { Bookmark, Star, Sparkles, ChevronDown, ChevronUp, Eye } from "lucide-react";

interface Props {
  movie: MovieCardType;
  isWatchlisted?: boolean;
  userRating?: number;
  onRatingChanged?: (movieId: number, rating: number) => void;
  onWatchlistChanged?: (movieId: number, inWatchlist: boolean) => void;
}

export default function MovieCard({
  movie,
  isWatchlisted = false,
  userRating,
  onRatingChanged,
  onWatchlistChanged,
}: Props) {
  const { userId, setSelectedMovieId, setToast, incrementRatings, updateWatchlistCount } = useStore();

  const [inWatchlist, setInWatchlist] = useState(isWatchlisted);
  const [currentRating, setCurrentRating] = useState<number | undefined>(userRating);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [showExplanation, setShowExplanation] = useState(false);
  const [posterUrl, setPosterUrl] = useState<string | null>(movie.poster_url || null);
  const [isMediaLoaded, setIsMediaLoaded] = useState(false);

  useEffect(() => {
    setInWatchlist(isWatchlisted);
  }, [isWatchlisted]);

  useEffect(() => {
    setCurrentRating(userRating);
  }, [userRating]);

  // Lazy-load media details if poster is not pre-populated
  useEffect(() => {
    if (!posterUrl && !isMediaLoaded) {
      apiClient
        .getMediaDetails(movie.movieId)
        .then((media) => {
          if (media.poster_url) setPosterUrl(media.poster_url);
          setIsMediaLoaded(true);
        })
        .catch(() => setIsMediaLoaded(true));
    }
  }, [movie.movieId, posterUrl, isMediaLoaded]);

  const handleWatchlistToggle = async (e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (inWatchlist) {
        await apiClient.removeFromWatchlist(userId, movie.movieId);
        setInWatchlist(false);
        updateWatchlistCount(-1);
        setToast(`Removed "${movie.display_title}" from watchlist`);
        onWatchlistChanged?.(movie.movieId, false);
      } else {
        await apiClient.addToWatchlist(userId, movie.movieId);
        setInWatchlist(true);
        updateWatchlistCount(1);
        setToast(`Saved "${movie.display_title}" to watchlist`);
        onWatchlistChanged?.(movie.movieId, true);
      }
    } catch (err: any) {
      setToast(`Watchlist error: ${err.message}`);
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
      setToast(`Rating error: ${err.message}`);
    }
  };

  // Signal contributions calculation
  const c = movie.contributions || { mf: 0, knn: 0, content: 0, popularity: 0 };
  const totalWeight = Math.max(0.001, c.mf + c.knn + c.content + c.popularity);
  const mfPct = Math.round((c.mf / totalWeight) * 100);
  const knnPct = Math.round((c.knn / totalWeight) * 100);
  const contentPct = Math.round((c.content / totalWeight) * 100);
  const popPct = Math.max(0, 100 - (mfPct + knnPct + contentPct));

  return (
    <div
      onClick={() => setSelectedMovieId(movie.movieId)}
      className="group relative flex flex-col rounded-xl bg-[#141417] hover:bg-[#1a1a1f] border border-zinc-800/80 hover:border-zinc-700 transition-all duration-300 hover:shadow-xl hover:shadow-black/40 overflow-hidden cursor-pointer"
    >
      {/* Poster Frame / Visual Header */}
      <div className="relative aspect-[16/10] w-full bg-zinc-900 overflow-hidden">
        {posterUrl ? (
          <img
            src={posterUrl}
            alt={movie.display_title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
        ) : (
          /* Deterministic Typographic Card Art */
          <div className="w-full h-full flex flex-col justify-between p-4 bg-gradient-to-br from-zinc-850 via-[#18181d] to-[#101013] border-b border-zinc-800">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[10px] text-amber-500 uppercase tracking-widest font-semibold">
                MovieLens #{movie.movieId}
              </span>
              <span className="font-mono text-xs text-zinc-500">{movie.year || "Classic"}</span>
            </div>
            <div className="my-auto">
              <p className="text-sm font-bold text-zinc-200 line-clamp-2 leading-tight">
                {movie.display_title}
              </p>
              <p className="text-[11px] text-zinc-400 mt-1 line-clamp-1">
                {movie.genres?.slice(0, 2).join(" • ") || "Cinema"}
              </p>
            </div>
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-500">
              <Sparkles className="w-3 h-3 text-amber-400" />
              <span>Calibrated CF Representation</span>
            </div>
          </div>
        )}

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-[#141417] via-transparent to-transparent opacity-80" />

        {/* Floating Badges */}
        <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
          {movie.predicted_rating ? (
            <span className="px-2 py-0.5 rounded-full bg-black/80 backdrop-blur-md border border-amber-500/30 text-[11px] font-mono font-bold text-amber-400 flex items-center gap-1">
              <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
              {movie.predicted_rating.toFixed(2)}★
            </span>
          ) : movie.score > 0 ? (
            <span className="px-2 py-0.5 rounded-full bg-black/80 backdrop-blur-md border border-cyan-500/30 text-[11px] font-mono font-bold text-cyan-400">
              {Math.round(movie.score * 100)}% Sim
            </span>
          ) : null}
        </div>

        {/* Watchlist Bookmark Button */}
        <button
          onClick={handleWatchlistToggle}
          title={inWatchlist ? "Remove from watchlist" : "Add to watchlist"}
          className={`absolute top-2.5 right-2.5 p-1.5 rounded-full backdrop-blur-md transition-all ${
            inWatchlist
              ? "bg-amber-500 text-black shadow-md shadow-amber-500/30 scale-105"
              : "bg-black/60 text-zinc-400 hover:text-white hover:bg-black/80"
          }`}
        >
          <Bookmark className="w-3.5 h-3.5 fill-current" />
        </button>
      </div>

      {/* Card Content */}
      <div className="p-4 flex flex-col flex-1 justify-between">
        <div>
          {/* Title & Year */}
          <div className="flex items-start justify-between gap-2">
            <h3 className="font-semibold text-sm text-zinc-100 group-hover:text-amber-400 transition-colors line-clamp-1">
              {movie.display_title}
            </h3>
            {movie.year && (
              <span className="font-mono text-xs text-zinc-500 shrink-0">{movie.year}</span>
            )}
          </div>

          {/* Genre Badges */}
          <div className="flex flex-wrap gap-1 mt-2">
            {movie.genres?.slice(0, 3).map((g: string) => (
              <span
                key={g}
                className="px-1.5 py-0.5 rounded bg-zinc-800 text-[10px] font-medium text-zinc-400"
              >
                {g}
              </span>
            ))}
            {(movie.genres?.length || 0) > 3 && (
              <span className="px-1.5 py-0.5 rounded bg-zinc-850 text-[10px] text-zinc-500">
                +{movie.genres.length - 3}
              </span>
            )}
          </div>
        </div>

        {/* Interactive Ratings Row & Signal Bar */}
        <div className="mt-4 pt-3 border-t border-zinc-800/80">
          {/* Rate this Movie */}
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-zinc-500 font-medium">Your Rating:</span>
            <div className="flex items-center gap-0.5" onMouseLeave={() => setHoverRating(null)}>
              {[1, 2, 3, 4, 5].map((star) => {
                const filled = (hoverRating !== null ? hoverRating : currentRating || 0) >= star;
                return (
                  <button
                    key={star}
                    type="button"
                    onClick={(e) => handleRate(star, e)}
                    onMouseEnter={() => setHoverRating(star)}
                    className="p-0.5 text-zinc-600 hover:text-amber-400 transition-transform hover:scale-115"
                  >
                    <Star
                      className={`w-3.5 h-3.5 ${
                        filled ? "fill-amber-400 text-amber-400" : "text-zinc-600"
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </div>

          {/* Multi-Signal Breakdown Bar (MF, kNN, Content, Pop) */}
          <div className="mt-3">
            <div className="flex items-center justify-between text-[10px] font-mono text-zinc-500 mb-1">
              <span>Signals:</span>
              <span className="flex items-center gap-2">
                <span className="text-sky-400">MF {mfPct}%</span>
                <span className="text-purple-400">kNN {knnPct}%</span>
                <span className="text-emerald-400">Content {contentPct}%</span>
              </span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-zinc-800 overflow-hidden flex">
              <div style={{ width: `${mfPct}%` }} className="h-full signal-bar-mf" title={`MF ALS: ${mfPct}%`} />
              <div style={{ width: `${knnPct}%` }} className="h-full signal-bar-knn" title={`Item-kNN: ${knnPct}%`} />
              <div style={{ width: `${contentPct}%` }} className="h-full signal-bar-content" title={`TF-IDF: ${contentPct}%`} />
              <div style={{ width: `${popPct}%` }} className="h-full signal-bar-pop" title={`Bayesian Pop: ${popPct}%`} />
            </div>
          </div>

          {/* Structured Explanation Accordion */}
          {movie.signals && movie.signals.length > 0 && (
            <div className="mt-2.5">
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowExplanation(!showExplanation);
                }}
                className="flex items-center justify-between w-full text-[10px] font-mono text-zinc-400 hover:text-zinc-200 transition-colors"
              >
                <span>Why this pick?</span>
                {showExplanation ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>

              {showExplanation && (
                <div className="mt-2 p-2 rounded-lg bg-zinc-900/90 border border-zinc-800 space-y-1 text-[11px] text-zinc-300">
                  {movie.signals.map((sig: any, sIdx: number) => (
                    <div key={sIdx} className="flex items-start gap-1.5">
                      <span className="font-mono text-amber-500">•</span>
                      <span>
                        {sig.type === "neighbor" && (
                          <>
                            High co-rating affinity with <span className="text-zinc-100 font-medium">#{sig.details.target_movie_id}</span> (sim: {Number(sig.details.similarity).toFixed(2)})
                          </>
                        )}
                        {sig.type === "genre" && (
                          <>
                            Shared genres: <span className="text-emerald-400 font-medium">{sig.details.matching_genres?.join(", ")}</span>
                          </>
                        )}
                        {sig.type === "tags" && (
                          <>
                            Matched tags: <span className="text-sky-400">{sig.details.matching_tags?.join(", ")}</span>
                          </>
                        )}
                        {sig.type === "cf" && (
                          <>
                            ALS fold-in latent prediction: <span className="text-amber-400 font-mono font-medium">{Number(sig.details.raw_prediction).toFixed(2)}★</span>
                          </>
                        )}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
