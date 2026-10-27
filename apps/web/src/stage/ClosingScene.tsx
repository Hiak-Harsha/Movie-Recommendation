"use client";
import React from "react";
import { Film, ArrowUp, Heart } from "lucide-react";
import { useAppStore } from "../core/store";
import { surfaceCopy } from "../copy/en";

export const ClosingScene: React.FC<{ progress?: number }> = () => {
  const setIsAboutOpen = useAppStore((s) => s.setIsAboutOpen);
  const setAboutTab = useAppStore((s) => s.setAboutTab);

  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openAbout = (tab: "howToUse" | "howItWorks" | "dataCredits" | "terms" | "modelReport") => {
    setAboutTab(tab);
    setIsAboutOpen(true);
  };

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center justify-between min-h-[80svh] px-4 py-16 text-center select-none">
      {/* Closing Headline */}
      <div className="flex-1 flex flex-col items-center justify-center gap-6 max-w-2xl mx-auto">
        <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
          {surfaceCopy.scenes.s06.eyebrow}
        </span>

        <h2 className="text-3xl sm:text-5xl font-bold text-[#f2efe6] tracking-tight leading-tight">
          {surfaceCopy.scenes.s06.heading}
        </h2>

        <p className="text-sm sm:text-base text-[#9a9aa0] max-w-lg">
          {surfaceCopy.scenes.s06.subheading}
        </p>

        <button
          type="button"
          onClick={scrollToTop}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-mono uppercase bg-[#121316] hover:bg-[#1b1c20] text-[#f2efe6] border border-[#26282e] hover:border-[#f5a524]/40 transition-colors cursor-pointer mt-4"
        >
          <ArrowUp className="w-4 h-4 text-[#f5a524]" />
          <span>{surfaceCopy.scenes.s06.backToTop}</span>
        </button>
      </div>

      {/* Clean Visitor Footer */}
      <footer className="w-full pt-12 border-t border-[#26282e]/80 flex flex-col sm:flex-row items-center justify-between gap-6 text-xs text-[#9a9aa0] font-mono">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-md bg-[#f5a524] flex items-center justify-center">
            <Film className="w-3.5 h-3.5 text-black" />
          </div>
          <span className="font-bold text-[#f2efe6]">{surfaceCopy.brand.name}</span>
          <span>•</span>
          <span className="text-[11px] text-[#9a9aa0]">{surfaceCopy.brand.tagline}</span>
        </div>

        {/* Footer Navigation Links */}
        <div className="flex flex-wrap items-center justify-center gap-6">
          <button
            type="button"
            onClick={() => openAbout("howToUse")}
            className="hover:text-[#f5a524] transition-colors cursor-pointer"
          >
            {surfaceCopy.nav.about}
          </button>
          <button
            type="button"
            onClick={() => openAbout("dataCredits")}
            className="hover:text-[#f5a524] transition-colors cursor-pointer"
          >
            Data & Credits
          </button>
          <button
            type="button"
            onClick={() => openAbout("terms")}
            className="hover:text-[#f5a524] transition-colors cursor-pointer"
          >
            Terms & Privacy
          </button>
          <button
            type="button"
            onClick={() => openAbout("modelReport")}
            className="hover:text-[#f5a524] transition-colors cursor-pointer text-amber-500/80 hover:text-amber-400"
          >
            Model Report
          </button>
        </div>

        {/* TMDB Attribution notice */}
        <div className="text-[10px] text-zinc-500">
          Movie data and posters by TMDB
        </div>
      </footer>
    </div>
  );
};
