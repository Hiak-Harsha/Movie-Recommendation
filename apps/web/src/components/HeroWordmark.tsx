"use client";

import React from "react";
import { useStore } from "@/lib/store";
import { Sparkles, BarChart2, ShieldCheck } from "lucide-react";

export default function HeroWordmark() {
  const { setActiveTab } = useStore();

  const letters = ["C", "I", "N", "E", "M", "A", "T", "C", "H"];

  return (
    <section className="relative pt-12 pb-16 overflow-hidden border-b border-zinc-900 bg-radial from-zinc-950 via-[#0b0b0c] to-[#0b0b0c]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        {/* Eyebrow Label (01 / pattern from getartcraft.com audit) */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900/80 border border-zinc-800 text-[11px] font-mono tracking-widest text-zinc-400 mb-8 uppercase shadow-sm">
          <span className="text-amber-500 font-bold">01 /</span>
          <span>Dual-Engine Cinema Intelligence</span>
        </div>

        {/* Oversized Dynamic Wordmark with per-letter choreography */}
        <div className="flex justify-center items-center gap-1 sm:gap-2 md:gap-3 my-4 select-none">
          {letters.map((letter, idx) => (
            <span
              key={idx}
              className={`font-mono text-4xl sm:text-6xl md:text-8xl lg:text-9xl font-black tracking-tighter transition-all duration-500 hover:scale-110 hover:-translate-y-2 cursor-default ${
                idx === 0
                  ? "text-transparent bg-clip-text bg-gradient-to-br from-amber-400 via-amber-500 to-amber-700"
                  : "text-zinc-100 hover:text-amber-300"
              }`}
            >
              {letter}
            </span>
          ))}
        </div>

        {/* Editorial Subtitle */}
        <h1 className="text-xl sm:text-3xl md:text-4xl font-semibold text-zinc-200 tracking-tight max-w-3xl mx-auto mt-4 mb-4">
          Vectorized ALS collaborative filtering and TF-IDF content vectors, calibrated for honest discovery.
        </h1>

        <p className="text-sm sm:text-base text-zinc-400 max-w-2xl mx-auto leading-relaxed mb-8">
          Trained on MovieLens verified user histories with zero synthetic fillers. Precomputed $O(1)$ item neighbour graphs, closed-form fold-in for new visitors, and multi-signal transparency.
        </p>

        {/* Primary and Secondary Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4">
          <button
            onClick={() => setActiveTab("foryou")}
            className="flex items-center gap-2.5 px-6 py-3 rounded-full bg-amber-500 hover:bg-amber-400 text-black font-semibold text-sm transition-all duration-200 shadow-lg shadow-amber-500/25 hover:shadow-amber-500/40 hover:-translate-y-0.5 cursor-pointer"
          >
            <Sparkles className="w-4 h-4 stroke-[2.5]" />
            <span>Tune Personalized Feed</span>
          </button>

          <button
            onClick={() => setActiveTab("insights")}
            className="flex items-center gap-2 px-6 py-3 rounded-full bg-[#18181c] hover:bg-[#232328] border border-white/10 text-zinc-200 text-sm font-medium transition-all duration-200 hover:-translate-y-0.5 cursor-pointer shadow-sm"
          >
            <BarChart2 className="w-4 h-4 text-amber-400" />
            <span>Inspect 591-User Model Proof</span>
          </button>
        </div>

        {/* Quality Gate Badge (Evidence Over Claims) */}
        <div className="mt-10 flex items-center justify-center gap-6 text-xs font-mono text-zinc-500">
          <div className="flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>9,742 Catalog Movies</span>
          </div>
          <div className="hidden sm:inline-block">•</div>
          <div className="hidden sm:flex items-center gap-1.5">
            <span>20,706 Held-Out Pairs</span>
          </div>
          <div className="hidden sm:inline-block">•</div>
          <div className="flex items-center gap-1.5">
            <span className="text-amber-400">p95 Latency 35 ms</span>
          </div>
        </div>
      </div>
    </section>
  );
}
