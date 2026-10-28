"use client";
import React from "react";
import { Film, ArrowUp } from "lucide-react";
import { useAppStore } from "../core/store";
import { surfaceCopy } from "../copy/en";
import { scrollToScene } from "../core/motion/LenisProvider";

export const ClosingScene: React.FC = () => {
  const setIsAboutOpen = useAppStore((s) => s.setIsAboutOpen);
  const setAboutTab = useAppStore((s) => s.setAboutTab);

  const scrollToTop = () => {
    scrollToScene("#showcase");
  };

  const openAbout = (tab: "howToUse" | "howItWorks" | "dataCredits" | "terms" | "modelReport") => {
    setAboutTab(tab);
    setIsAboutOpen(true);
  };

  const words = surfaceCopy.scenes.s06.heading.split(" ");

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col items-center justify-between py-8 px-4 text-center select-none my-auto">
      {/* Closing Headline with Word Scrubbing */}
      <div className="flex-1 flex flex-col items-center justify-center gap-5 max-w-2xl mx-auto py-8">
        <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
          {surfaceCopy.scenes.s06.eyebrow}
        </span>

        <h2 className="text-fluid-h1 font-display font-bold text-[#f2efe6] tracking-tight leading-tight">
          {words.map((word, i) => (
            <span
              key={i}
              className="inline-block mx-1 transition-opacity duration-300"
              style={{
                opacity: "clamp(0.4, calc(var(--story-progress, 0.9) * 1.2), 1)",
              }}
            >
              {word}
            </span>
          ))}
        </h2>

        <p className="text-sm sm:text-base text-[#9a9aa0] max-w-lg text-fluid-body">
          {surfaceCopy.scenes.s06.subheading}
        </p>

        <button
          type="button"
          onClick={scrollToTop}
          className="flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-mono uppercase bg-[#121316] hover:bg-[#1b1c20] text-[#f2efe6] border border-[#26282e] hover:border-[#f5a524]/40 active:scale-95 transition-all cursor-pointer mt-2 shadow-lg"
        >
          <ArrowUp className="w-4 h-4 text-[#f5a524]" />
          <span>{surfaceCopy.scenes.s06.backToTop}</span>
        </button>
      </div>

      {/* Clean Visitor Footer (Never collides with dock) */}
      <footer className="w-full pt-8 pb-4 border-t border-[#26282e]/80 flex flex-col md:flex-row items-center justify-between gap-4 text-xs text-[#9a9aa0] font-mono">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-md bg-[#f5a524] flex items-center justify-center">
            <Film className="w-3.5 h-3.5 text-black" />
          </div>
          <span className="font-bold text-[#f2efe6]">{surfaceCopy.brand.name}</span>
          <span>•</span>
          <span className="text-[11px] text-[#9a9aa0] hidden sm:inline">{surfaceCopy.brand.tagline}</span>
        </div>

        {/* Footer Navigation Links */}
        <div className="flex flex-wrap items-center justify-center gap-4 sm:gap-6">
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
            className="hover:text-[#f5a524] transition-colors cursor-pointer text-amber-500/80 hover:text-amber-400 font-semibold"
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
