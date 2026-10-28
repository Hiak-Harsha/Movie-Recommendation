"use client";
import React, { useState, useEffect } from "react";
import { Bookmark, Trash2, CheckCircle2, Download, Ticket, ArrowRight } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import { ProceduralPoster } from "../../core/motion/ProceduralPoster";
import type { WatchlistItem } from "@cinematch/api-client";

export const LibraryScene: React.FC<{ progress?: number }> = () => {
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  const libraryCount = useAppStore((s) => s.libraryCount);
  const updateLibraryCount = useAppStore((s) => s.updateLibraryCount);
  const setToast = useAppStore((s) => s.setToast);
  const setSelectedMovieId = useAppStore((s) => s.setSelectedMovieId);

  useEffect(() => {
    let mounted = true;
    api.getMyWatchlist()
      .then((items) => {
        if (mounted) {
          setWatchlist(items || []);
          setLoading(false);
        }
      })
      .catch((err) => {
        console.error("Failed to load watchlist:", err);
        if (mounted) setLoading(false);
      });

    return () => {
      mounted = false;
    };
  }, [libraryCount]);

  const handleRemove = async (movieId: number, title: string) => {
    const itemToRemove = watchlist.find((w) => w.movieId === movieId);
    setWatchlist((prev) => prev.filter((w) => w.movieId !== movieId));
    updateLibraryCount(-1);

    try {
      await api.removeFromMyWatchlist(movieId);
      setToast({
        message: `Torn ticket: "${title}" removed from lineup`,
        undoAction: async () => {
          await api.addToMyWatchlist(movieId);
          updateLibraryCount(1);
          if (itemToRemove) {
            setWatchlist((prev) => [...prev, itemToRemove]);
          }
        },
      });
    } catch (e) {
      console.error(e);
      if (itemToRemove) {
        setWatchlist((prev) => [...prev, itemToRemove]);
        updateLibraryCount(1);
      }
    }
  };

  const handleMarkWatched = async (movieId: number, title: string) => {
    // Prompt user rating by opening detail or submitting positive rating
    try {
      await api.submitMyRating(movieId, 5.0);
      await api.removeFromMyWatchlist(movieId);
      setWatchlist((prev) => prev.filter((w) => w.movieId !== movieId));
      updateLibraryCount(-1);
      setToast({
        message: `Marked "${title}" as watched with 5 stars!`,
      });
    } catch (e) {
      console.error(e);
    }
  };

  const jumpToSearch = () => {
    const el = document.querySelector("#search");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col gap-8 px-4 py-8">
      {/* Eyebrow & Title */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between border-b border-[#26282e] pb-4 gap-4">
        <div className="flex flex-col gap-1">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            05/ Library
          </span>
          <h2 className="text-fluid-h2 font-display font-bold text-[#f2efe6] tracking-tight">
            Tonight&apos;s Cinema Lineup
          </h2>
          <p className="text-xs sm:text-sm text-[#9a9aa0]">
            Your personal saved tickets for the big screen.
          </p>
        </div>

        {/* Lineup Count & Export Link */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 font-mono text-xs text-[#f2efe6] bg-[#121316] px-3.5 py-1.5 rounded-full border border-[#26282e]">
            <Ticket className="w-3.5 h-3.5 text-[#f5a524]" />
            <span>{watchlist.length} {watchlist.length === 1 ? "ticket" : "tickets"} saved</span>
          </div>

          <a
            href="/api/me/export"
            download="cinematch-lineup.json"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] bg-[#121316] border border-[#26282e] hover:border-[#f5a524]/40 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Export</span>
          </a>
        </div>
      </div>

      {/* Ticket Stubs Stack */}
      {loading ? (
        <div className="p-12 text-center text-xs font-mono text-[#9a9aa0]">
          Gathering your cinema tickets...
        </div>
      ) : watchlist.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 sm:p-16 rounded-3xl bg-[#121316] border border-[#26282e] text-center gap-4">
          <div className="w-12 h-12 rounded-full bg-[#1b1c20] border border-[#26282e] flex items-center justify-center text-[#f5a524]">
            <Bookmark className="w-6 h-6" />
          </div>
          <div className="flex flex-col gap-1 max-w-sm">
            <h3 className="text-lg font-bold text-[#f2efe6]">Your lineup is empty</h3>
            <p className="text-xs text-[#9a9aa0]">
              Save films using the bookmark icon on any card to build your evening schedule.
            </p>
          </div>
          <button
            type="button"
            onClick={jumpToSearch}
            className="flex items-center gap-2 px-4 py-2 rounded-full text-xs font-mono uppercase bg-[#f5a524] text-black font-semibold hover:bg-[#e0941c] transition-colors cursor-pointer"
          >
            <span>Explore films</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {watchlist.map((item, idx) => (
            <div
              key={item.movieId}
              className="relative group flex flex-col rounded-2xl bg-[#121316] border border-[#26282e] hover:border-[#f5a524]/40 shadow-xl overflow-hidden transition-all duration-300"
            >
              {/* Top Section: Ticket Header & Film Poster */}
              <div className="flex p-4 gap-4">
                {/* 2:3 Poster Thumbnail */}
                <div
                  className="w-20 shrink-0 aspect-[2/3] rounded-lg overflow-hidden border border-[#26282e] cursor-pointer"
                  onClick={() => setSelectedMovieId(item.movieId)}
                >
                  <ProceduralPoster
                    movieId={item.movieId}
                    title={item.display_title || item.title}
                    year={item.year}
                    genres={item.genres}
                    className="w-full h-full object-cover"
                  />
                </div>

                {/* Ticket Details */}
                <div className="flex-1 flex flex-col justify-between overflow-hidden">
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-[#f5a524] uppercase tracking-wider">
                      <span>ADMIT ONE</span>
                      <span>STUB #{String(idx + 1).padStart(3, "0")}</span>
                    </div>

                    <h4
                      className="text-sm font-bold text-[#f2efe6] truncate cursor-pointer hover:text-[#f5a524] transition-colors"
                      onClick={() => setSelectedMovieId(item.movieId)}
                      title={item.display_title || item.title}
                    >
                      {item.display_title || item.title}
                    </h4>

                    <div className="flex items-center gap-2 text-xs text-[#9a9aa0] font-mono">
                      <span>{item.year || "Classic"}</span>
                      {item.genres && item.genres[0] && (
                        <>
                          <span>•</span>
                          <span>{item.genres[0]}</span>
                        </>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 pt-2">
                    <span className="text-[11px] font-mono text-amber-400">
                      ★ {item.vote_average ? item.vote_average.toFixed(1) : "4.0"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Perforated Stub Tear Line */}
              <div className="relative w-full h-[12px] flex items-center justify-between px-2">
                <div className="w-3 h-3 rounded-full bg-[#0b0b0c] -ml-3.5 border-r border-[#26282e]" />
                <div className="flex-1 border-b border-dashed border-[#26282e] mx-2" />
                <div className="w-3 h-3 rounded-full bg-[#0b0b0c] -mr-3.5 border-l border-[#26282e]" />
              </div>

              {/* Bottom Stub Actions */}
              <div className="flex items-center justify-between px-4 py-3 bg-[#0e0e11] text-xs font-mono">
                <button
                  type="button"
                  onClick={() => handleMarkWatched(item.movieId, item.display_title || item.title)}
                  className="flex items-center gap-1.5 text-emerald-400 hover:text-emerald-300 transition-colors cursor-pointer"
                  title="Mark as watched and rate"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>Watched</span>
                </button>

                <button
                  type="button"
                  onClick={() => handleRemove(item.movieId, item.display_title || item.title)}
                  className="flex items-center gap-1.5 text-zinc-500 hover:text-red-400 transition-colors cursor-pointer"
                  title="Tear ticket and remove from lineup"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Tear stub</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
