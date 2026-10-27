"use client";

import React from "react";
import { Film } from "lucide-react";

interface TickerMovie {
  title: string;
  year: number;
  genre: string;
}

const DEFAULT_FEATURED: TickerMovie[] = [
  { title: "Blade Runner 2049", year: 2017, genre: "Sci-Fi" },
  { title: "Spirited Away", year: 2001, genre: "Animation" },
  { title: "The Godfather", year: 1972, genre: "Crime" },
  { title: "Inception", year: 2010, genre: "Sci-Fi" },
  { title: "Pulp Fiction", year: 1994, genre: "Crime" },
  { title: "Parasite", year: 2019, genre: "Thriller" },
  { title: "Interstellar", year: 2014, genre: "Adventure" },
  { title: "Amélie", year: 2001, genre: "Romance" },
  { title: "The Grand Budapest Hotel", year: 2014, genre: "Comedy" },
  { title: "Whiplash", year: 2014, genre: "Drama" },
];

export default function MarqueeTicker({ items = DEFAULT_FEATURED }: { items?: TickerMovie[] }) {
  return (
    <div className="w-full bg-[#0e0e11] border-y border-zinc-800 py-3 overflow-hidden select-none">
      <div className="animate-marquee flex items-center gap-8 whitespace-nowrap">
        {/* Track 1 */}
        {items.map((item, idx) => (
          <div key={`t1-${idx}`} className="flex items-center gap-3 text-xs tracking-wider text-zinc-300">
            <Film className="w-3.5 h-3.5 text-amber-500" />
            <span className="font-semibold text-zinc-100">{item.title}</span>
            <span className="text-zinc-500 font-mono">({item.year})</span>
            <span className="px-2 py-0.5 rounded-full bg-zinc-800/80 text-[10px] text-amber-400 font-medium">
              {item.genre}
            </span>
          </div>
        ))}
        {/* Track 2 */}
        {items.map((item, idx) => (
          <div key={`t2-${idx}`} className="flex items-center gap-3 text-xs tracking-wider text-zinc-300">
            <Film className="w-3.5 h-3.5 text-amber-500" />
            <span className="font-semibold text-zinc-100">{item.title}</span>
            <span className="text-zinc-500 font-mono">({item.year})</span>
            <span className="px-2 py-0.5 rounded-full bg-zinc-800/80 text-[10px] text-amber-400 font-medium">
              {item.genre}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
