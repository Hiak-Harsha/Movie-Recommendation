"use client";

import React, { useState, useEffect, useRef } from "react";
import { useStore } from "@/lib/store";
import { apiClient, SearchResult } from "@cinematch/api-client";
import { Search, X, Star, Film, Loader2 } from "lucide-react";

export default function SearchModal() {
  const { isSearchOpen, setIsSearchOpen, setSelectedMovieId } = useStore();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global shortcut: press '/' or 'Cmd+K' to open search
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
        e.preventDefault();
        setIsSearchOpen(true);
      }
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsSearchOpen(true);
      }
      if (e.key === "Escape" && isSearchOpen) {
        setIsSearchOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isSearchOpen, setIsSearchOpen]);

  useEffect(() => {
    if (isSearchOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setResults([]);
    }
  }, [isSearchOpen]);

  // Debounced search
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    setLoading(true);
    const handler = setTimeout(() => {
      apiClient
        .searchMovies(query, 20)
        .then((res) => {
          setResults(res.results);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }, 150);

    return () => clearTimeout(handler);
  }, [query]);

  if (!isSearchOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4 bg-black/80 backdrop-blur-md">
      <div
        className="relative w-full max-w-2xl rounded-2xl bg-[#141417] border border-zinc-700 shadow-2xl overflow-hidden flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Input Bar */}
        <div className="flex items-center px-4 py-3.5 border-b border-zinc-800 gap-3">
          <Search className="w-5 h-5 text-amber-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search films by title, year (e.g. Inception 2010), or genre..."
            className="w-full bg-transparent text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none"
          />
          {loading ? (
            <Loader2 className="w-4 h-4 text-amber-500 animate-spin shrink-0" />
          ) : query ? (
            <button
              onClick={() => setQuery("")}
              className="text-zinc-500 hover:text-zinc-300"
            >
              <X className="w-4 h-4" />
            </button>
          ) : (
            <kbd className="px-1.5 py-0.5 rounded bg-zinc-800 border border-zinc-700 text-[10px] font-mono text-zinc-400">
              ESC
            </kbd>
          )}
        </div>

        {/* Results List */}
        <div className="max-h-[60vh] overflow-y-auto p-2 divide-y divide-zinc-850">
          {results.length > 0 ? (
            results.map((item) => (
              <div
                key={item.movieId}
                onClick={() => {
                  setSelectedMovieId(item.movieId);
                  setIsSearchOpen(false);
                }}
                className="flex items-center justify-between p-3 rounded-xl hover:bg-zinc-800/60 cursor-pointer transition-colors group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-zinc-850 border border-zinc-750 flex items-center justify-center shrink-0 group-hover:border-amber-500/40">
                    <Film className="w-4 h-4 text-zinc-400 group-hover:text-amber-400" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-zinc-200 group-hover:text-amber-400 transition-colors">
                      {item.display_title}
                    </h4>
                    <div className="flex items-center gap-2 text-xs text-zinc-500 mt-0.5">
                      {item.year && <span className="font-mono">{item.year}</span>}
                      <span>•</span>
                      <span className="truncate max-w-[280px]">
                        {item.genres.join(", ")}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 font-mono text-xs text-amber-400 shrink-0">
                  <Star className="w-3.5 h-3.5 fill-current" />
                  <span>{item.vote_average.toFixed(1)}</span>
                </div>
              </div>
            ))
          ) : query ? (
            !loading && (
              <div className="py-12 text-center text-zinc-500 text-sm">
                No matching movies found for &quot;{query}&quot;
              </div>
            )
          ) : (
            <div className="py-8 text-center text-zinc-500 text-xs font-mono">
              Type movie titles with typo tolerance (e.g. &quot;matrx&quot; or &quot;godfathr 1972&quot;)
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
