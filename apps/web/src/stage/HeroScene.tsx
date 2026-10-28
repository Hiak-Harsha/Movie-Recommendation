"use client";
import React from "react";
import { ArrowDown, Sparkles, Search, ArrowRight } from "lucide-react";
import { useAppStore } from "../core/store";
import { surfaceCopy } from "../copy/en";
import { SplitText } from "../core/motion/SplitText";

export const HeroScene: React.FC<{ progress?: number }> = ({ progress = 0 }) => {
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const picksCount = useAppStore((s) => s.picksCount);
  const hasPicks = useAppStore((s) => s.hasPicks);

  // Letterbox retracts over the first 25vh (progress 0 to 0.035 in 700vh)
  const letterboxProgress = Math.min(1, progress * 15);
  const letterboxScale = Math.max(0, 1 - letterboxProgress);

  const jumpToTaste = () => {
    const el = document.querySelector("#taste");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  const jumpToForYou = () => {
    const el = document.querySelector("#for-you");
    if (el) el.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="relative w-full h-full flex flex-col items-center justify-center text-center px-4 overflow-hidden select-none">
      {/* Cinematic Letterbox Bars */}
      <div
        aria-hidden="true"
        data-decor="true"
        className="fixed top-0 left-0 right-0 h-[12vh] bg-black z-40 origin-top pointer-events-none transition-transform duration-75"
        style={{ transform: `scaleY(${letterboxScale})` }}
      />
      <div
        aria-hidden="true"
        data-decor="true"
        className="fixed bottom-0 left-0 right-0 h-[12vh] bg-black z-40 origin-bottom pointer-events-none transition-transform duration-75"
        style={{ transform: `scaleY(${letterboxScale})` }}
      />

      {/* Hero Content Container */}
      <div className="relative z-10 flex flex-col items-center gap-6 max-w-4xl mx-auto py-12">
        {/* Eyebrow */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#121316]/90 border border-[#26282e] text-xs font-mono text-[#f5a524] shadow-md">
          <Sparkles className="w-3.5 h-3.5" />
          <span>{surfaceCopy.scenes.s00.eyebrow}</span>
        </div>

        {/* Cinematic Animated Wordmark */}
        <h1 className="font-display text-fluid-wordmark text-[#f2efe6] uppercase tracking-wider drop-shadow-2xl">
          <SplitText text="CINEMATCH" mode="chars" stagger={0.04} />
        </h1>

        {/* Headline & Subtitle */}
        <div className="flex flex-col gap-3 max-w-2xl mx-auto">
          <p className="font-display text-fluid-h2 font-bold text-[#f2efe6] tracking-tight">
            {surfaceCopy.brand.tagline}
          </p>
          <p className="text-sm sm:text-base text-[#9a9aa0] max-w-xl mx-auto text-fluid-body">
            {surfaceCopy.brand.subtitle}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
          {hasPicks || picksCount >= 5 ? (
            <button
              type="button"
              onClick={jumpToForYou}
              className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#f5a524] text-black font-bold hover:bg-[#e0941c] transition-all shadow-xl shadow-amber-500/20 hover:scale-[1.02] cursor-pointer"
            >
              <span>Continue to picks ({picksCount})</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={jumpToTaste}
              className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#f5a524] text-black font-bold hover:bg-[#e0941c] transition-all shadow-xl shadow-amber-500/20 hover:scale-[1.02] cursor-pointer"
            >
              <span>{surfaceCopy.nav.startPicking}</span>
              <ArrowDown className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#121316]/90 hover:bg-[#1c1c21] text-[#f2efe6] border border-[#26282e] hover:border-[#f5a524]/50 transition-all hover:scale-[1.02] cursor-pointer shadow-lg"
          >
            <Search className="w-4 h-4 text-[#f5a524]" />
            <span>{surfaceCopy.nav.searchFilms}</span>
          </button>
        </div>

        {/* Scroll Prompt */}
        <div className="flex items-center gap-2 pt-8 text-[11px] font-mono text-[#9a9aa0] animate-pulse">
          <ArrowDown className="w-3.5 h-3.5 text-[#f5a524]" />
          <span>{surfaceCopy.scenes.s00.scrollPrompt}</span>
        </div>
      </div>
    </div>
  );
};
