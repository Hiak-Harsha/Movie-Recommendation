"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useStore } from "@/lib/store";
import { apiClient, WatchlistItem } from "@cinematch/api-client";
import { Bookmark, Download, Trash2, Edit3, Film, Star, Loader2 } from "lucide-react";

export default function WatchlistView() {
  const { userId, setToast, updateWatchlistCount, setSelectedMovieId } = useStore();

  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingNotesId, setEditingNotesId] = useState<number | null>(null);
  const [noteText, setNoteText] = useState("");

  const fetchWatchlist = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiClient.getUserWatchlist(userId);
      setItems(data);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchWatchlist();
  }, [fetchWatchlist]);

  const handleRemove = async (movieId: number, title: string) => {
    try {
      await apiClient.removeFromWatchlist(userId, movieId);
      setItems(items.filter((i) => i.movieId !== movieId));
      updateWatchlistCount(-1);
      setToast(`Removed "${title}" from watchlist`);
    } catch (e: any) {
      setToast(e.message);
    }
  };

  const handleSaveNote = async (movieId: number) => {
    try {
      await apiClient.addToWatchlist(userId, movieId, noteText);
      setItems(
        items.map((i) => (i.movieId === movieId ? { ...i, notes: noteText } : i))
      );
      setEditingNotesId(null);
      setToast("Note updated");
    } catch (e: any) {
      setToast(e.message);
    }
  };

  const exportUrl = apiClient.getWatchlistExportUrl(userId);

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Header Bar */}
      <div className="p-6 rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <span className="font-mono text-xs font-bold text-amber-500 uppercase tracking-widest">
            05 / Persistent Collection
          </span>
          <h2 className="text-xl font-bold text-white tracking-tight mt-1">
            Personal Watchlist & Curations
          </h2>
          <p className="text-xs text-zinc-400 mt-1">
            Stored persistently in SQLite database across tab closures and sessions.
          </p>
        </div>

        {items.length > 0 && (
          <a
            href={exportUrl}
            download={`cinematch_watchlist_${userId}.csv`}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-semibold text-xs transition-all shadow-md shadow-amber-500/20 cursor-pointer self-start sm:self-auto"
          >
            <Download className="w-4 h-4 stroke-[2.5]" />
            <span>Export Watchlist CSV</span>
          </a>
        )}
      </div>

      {/* Watchlist Content */}
      {loading ? (
        <div className="py-24 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 text-amber-500 animate-spin" />
          <p className="text-xs font-mono text-zinc-400">Loading saved titles from database...</p>
        </div>
      ) : items.length > 0 ? (
        <div className="rounded-2xl bg-[#141417] border border-zinc-800 shadow-xl overflow-hidden divide-y divide-zinc-800/80">
          {items.map((item) => (
            <div
              key={item.movieId}
              className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-zinc-800/40 transition-colors"
            >
              {/* Left Title Info */}
              <div
                onClick={() => setSelectedMovieId(item.movieId)}
                className="flex items-start gap-4 cursor-pointer flex-1"
              >
                <div className="w-10 h-10 rounded-lg bg-zinc-800 border border-zinc-700 flex items-center justify-center shrink-0">
                  <Film className="w-5 h-5 text-amber-400" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-semibold text-white hover:text-amber-400 transition-colors">
                      {item.display_title}
                    </h3>
                    {item.year && (
                      <span className="font-mono text-xs text-zinc-500">({item.year})</span>
                    )}
                  </div>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-zinc-400 mt-1">
                    <span>{item.genres.join(", ")}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1 font-mono text-amber-400">
                      <Star className="w-3 h-3 fill-current" />
                      {item.vote_average.toFixed(1)} ({item.vote_count} reviews)
                    </span>
                  </div>

                  {/* Note Section */}
                  {editingNotesId === item.movieId ? (
                    <div className="mt-3 flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="text"
                        value={noteText}
                        onChange={(e) => setNoteText(e.target.value)}
                        placeholder="Add personal note..."
                        className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-700 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-amber-500"
                      />
                      <button
                        onClick={() => handleSaveNote(item.movieId)}
                        className="px-3 py-1.5 rounded-lg bg-amber-500 text-black font-semibold text-xs"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => setEditingNotesId(null)}
                        className="text-xs text-zinc-400 hover:text-zinc-200"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : item.notes ? (
                    <p className="mt-2 text-xs text-amber-200/90 bg-amber-950/30 border border-amber-500/20 px-2.5 py-1 rounded-md inline-block">
                      Note: {item.notes}
                    </p>
                  ) : null}
                </div>
              </div>

              {/* Right Side Actions */}
              <div className="flex items-center gap-2 self-end sm:self-auto shrink-0">
                <button
                  onClick={() => {
                    setEditingNotesId(item.movieId);
                    setNoteText(item.notes || "");
                  }}
                  className="p-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white transition-colors cursor-pointer"
                  title="Edit note"
                >
                  <Edit3 className="w-4 h-4" />
                </button>

                <button
                  onClick={() => handleRemove(item.movieId, item.display_title)}
                  className="p-2 rounded-lg bg-zinc-800 hover:bg-red-950/60 text-zinc-400 hover:text-red-400 transition-colors cursor-pointer"
                  title="Remove from watchlist"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="py-24 text-center rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/40">
          <Bookmark className="w-8 h-8 text-zinc-600 mx-auto mb-3" />
          <p className="text-zinc-300 font-medium text-sm">Your watchlist is currently empty.</p>
          <p className="text-zinc-500 text-xs mt-1">
            Browse &quot;For You&quot; or &quot;Discover&quot; and click the bookmark icon on any movie to save it.
          </p>
        </div>
      )}
    </div>
  );
}
