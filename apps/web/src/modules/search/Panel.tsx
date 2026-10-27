"use client";
import React, { useState, useEffect, useRef } from "react";
import { Search, X, Star } from "lucide-react";
import { useAppStore } from "../../core/store";
import { api } from "../../core/client";
import type { SearchResult } from "@cinematch/api-client";

export const SearchPanel: React.FC = () => {
  const isSearchOpen = useAppStore((s) => s.isSearchOpen);
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const setSelectedMovieId = useAppStore((s) => s.setSelectedMovieId);

  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus input automatically on open
  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults([]);
    }
  }, [isSearchOpen]);

  // Debounced search query
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        const res = await api.searchMovies(query, 12);
        setResults(res.results || []);
        setSelectedIndex(0);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 180);

    return () => clearTimeout(timer);
  }, [query]);

  // Keyboard navigation: Escape closes, Arrows navigate, Enter selects
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setIsSearchOpen(false);
    } else if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % Math.max(1, results.length));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + results.length) % Math.max(1, results.length));
    } else if (e.key === "Enter" && results[selectedIndex]) {
      e.preventDefault();
      const chosen = results[selectedIndex];
      setIsSearchOpen(false);
      setSelectedMovieId(chosen.movieId);
    }
  };

  if (!isSearchOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Search movies"
      className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-[#0b0b0c]/80 backdrop-blur-md"
      onClick={() => setIsSearchOpen(false)}
      onKeyDown={handleKeyDown}
    >
      <div
        className="relative w-full max-w-xl rounded-2xl bg-[#121316] border border-[#26282e] shadow-2xl overflow-hidden flex flex-col max-h-[75vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-[#26282e]">
          <Search className="w-5 h-5 text-[#f5a524]" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search films by title..."
            className="flex-1 bg-transparent text-sm sm:text-base text-[#f2efe6] placeholder-[#9a9aa0] focus:outline-none"
            aria-autocomplete="list"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="p-1 rounded text-[#9a9aa0] hover:text-[#f2efe6]"
              aria-label="Clear search input"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Results List */}
        <div className="overflow-y-auto flex-1 p-2" data-lenis-prevent="true">
          {loading && (
            <div className="py-8 text-center font-mono text-xs text-[#9a9aa0]">
              Searching catalog...
            </div>
          )}

          {!loading && query && results.length === 0 && (
            <div className="py-8 text-center text-sm text-[#9a9aa0]">
              No titles matching &ldquo;{query}&rdquo;. Check spelling or try a broader term.
            </div>
          )}

          {!loading && results.map((item, idx) => {
            const isSelected = idx === selectedIndex;
            return (
              <div
                key={item.movieId}
                role="button"
                tabIndex={0}
                onClick={() => {
                  setIsSearchOpen(false);
                  setSelectedMovieId(item.movieId);
                }}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-colors ${
                  isSelected
                    ? "bg-[#26282e] text-[#f5a524]"
                    : "text-[#f2efe6] hover:bg-[#26282e]/50"
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <span className="text-xs sm:text-sm font-semibold">
                    {item.display_title || item.title}
                  </span>
                  <span className="text-[11px] font-mono text-[#9a9aa0]">
                    {item.year || "—"} • {item.genres.slice(0, 2).join(", ")}
                  </span>
                </div>

                {item.vote_average ? (
                  <span className="flex items-center gap-1 font-mono text-xs text-[#f5a524]">
                    <Star className="w-3 h-3 fill-current" />
                    {item.vote_average.toFixed(1)}
                  </span>
                ) : null}
              </div>
            );
          })}
        </div>

        {/* Footer shortcuts hint */}
        <div className="px-4 py-2 bg-[#0b0b0c]/60 border-t border-[#26282e] flex items-center justify-between text-[11px] font-mono text-[#9a9aa0]">
          <span>Use &uarr;&darr; to navigate, Enter to select</span>
          <span>Esc to close</span>
        </div>
      </div>
    </div>
  );
};
