"use client";
import React from "react";
import { ArrowDown, Sparkles, Search, ArrowRight } from "lucide-react";
import { useAppStore } from "../core/store";
import { surfaceCopy } from "../copy/en";
import { SplitText } from "../core/motion/SplitText";
import { scrollToScene } from "../core/motion/LenisProvider";

export const HeroScene: React.FC = () => {
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const picksCount = useAppStore((s) => s.picksCount);
  const hasPicks = useAppStore((s) => s.hasPicks);
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);

  const jumpToTaste = () => {
    scrollToScene("#taste");
  };

  const jumpToForYou = () => {
    scrollToScene("#for-you");
  };

  return (
    <div className="relative w-full flex flex-col items-center justify-center text-center px-4 select-none my-auto">
      {/* Localized dark contrast backing scrim behind hero typography */}
      <div
        aria-hidden="true"
        data-decor="true"
        className="absolute inset-0 max-w-3xl mx-auto rounded-3xl bg-[radial-gradient(circle_at_center,_rgba(11,11,12,0.9)_0%,_rgba(11,11,12,0.6)_50%,_transparent_100%)] pointer-events-none blur-xl -z-10"
      />

      {/* Hero Content Container */}
      <div className="relative z-10 flex flex-col items-center gap-4 sm:gap-6 max-w-4xl mx-auto py-4 sm:py-8">
        {/* Eyebrow */}
        <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#121316]/95 border border-[#26282e] text-xs font-mono text-[#f5a524] shadow-md">
          <Sparkles className="w-3.5 h-3.5" />
          <span>{surfaceCopy.scenes.s00.eyebrow}</span>
        </div>

        {/* Cinematic Animated Wordmark (Auto-fit on one line at all viewports) */}
        <div className="w-full max-w-4xl overflow-hidden px-2">
          <h1 className="font-display text-fluid-wordmark text-[#f2efe6] uppercase tracking-wider drop-shadow-2xl">
            <SplitText
              text="CINEMATCH"
              mode="chars"
              stagger={0.04}
              play={activeSceneIndex === 0}
            />
          </h1>
        </div>

        {/* Headline & Subtitle */}
        <div className="flex flex-col gap-2 sm:gap-3 max-w-2xl mx-auto px-4">
          <p className="font-display text-fluid-h2 font-bold text-[#f2efe6] tracking-tight">
            {surfaceCopy.brand.tagline}
          </p>
          <p className="text-sm sm:text-base text-[#9a9aa0] max-w-xl mx-auto text-fluid-body">
            {surfaceCopy.brand.subtitle}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-4 pt-2 sm:pt-4">
          {hasPicks || picksCount >= 5 ? (
            <button
              type="button"
              onClick={jumpToForYou}
              className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#f5a524] text-black font-bold hover:bg-[#e0941c] transition-all shadow-xl shadow-amber-500/20 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <span>Continue to picks ({picksCount})</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={jumpToTaste}
              className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#f5a524] text-black font-bold hover:bg-[#e0941c] transition-all shadow-xl shadow-amber-500/20 hover:scale-[1.02] active:scale-[0.98] cursor-pointer"
            >
              <span>{surfaceCopy.nav.startPicking}</span>
              <ArrowDown className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-6 py-3 rounded-full text-xs font-mono uppercase bg-[#121316]/95 hover:bg-[#1c1c21] text-[#f2efe6] border border-[#26282e] hover:border-[#f5a524]/50 transition-all hover:scale-[1.02] active:scale-[0.98] cursor-pointer shadow-lg"
          >
            <Search className="w-4 h-4 text-[#f5a524]" />
            <span>{surfaceCopy.nav.searchFilms}</span>
          </button>
        </div>

        {/* Scroll Prompt */}
        <div className="flex items-center gap-2 pt-4 sm:pt-6 text-[11px] font-mono text-[#9a9aa0] animate-pulse">
          <ArrowDown className="w-3.5 h-3.5 text-[#f5a524]" />
          <span>{surfaceCopy.scenes.s00.scrollPrompt}</span>
        </div>
      </div>
    </div>
  );
};
