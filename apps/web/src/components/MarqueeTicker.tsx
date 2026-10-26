"use client";

import React from "react";

export default function MarqueeTicker() {
  const items = [
    "EXPLICIT ALS MATRIX FACTORIZATION",
    "SHRUNK ITEM-KNN CO-RATINGS",
    "TF-IDF GENRE & TAG VECTOR EMBEDDINGS",
    "ISOTONIC CALIBRATION [0.5, 5.0]★",
    "MAXIMAL MARGINAL RELEVANCE (MMR)",
    "CLOSED-FORM NEW VISITOR FOLD-IN",
    "PRECOMPUTED TOP-100 NEIGHBOURS",
    "20,706 HELD-OUT TEST RATINGS",
    "ZERO SYNTHETIC DATA",
    "STATISTICALLY DEFENDED BENCHMARK",
  ];

  return (
    <div className="w-full bg-[#0e0e11] border-y border-zinc-850 py-3 overflow-hidden select-none">
      <div className="animate-marquee flex items-center gap-8 whitespace-nowrap">
        {/* First track */}
        {items.map((item, idx) => (
          <div key={`track1-${idx}`} className="flex items-center gap-3 text-xs font-mono tracking-wider text-zinc-400">
            <span className="w-1.5 h-1.5 rounded-sm bg-amber-500/80" />
            <span>{item}</span>
          </div>
        ))}
        {/* Second identical track for seamless infinite loop */}
        {items.map((item, idx) => (
          <div key={`track2-${idx}`} className="flex items-center gap-3 text-xs font-mono tracking-wider text-zinc-400">
            <span className="w-1.5 h-1.5 rounded-sm bg-amber-500/80" />
            <span>{item}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
