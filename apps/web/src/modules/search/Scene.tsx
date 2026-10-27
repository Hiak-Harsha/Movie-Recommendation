"use client";
import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";
import { useAppStore } from "../../core/store";
import { ProjectorBeam } from "../../core/motion/ProjectorBeam";

const SAMPLE_TITLES = [
  "Blade Runner 2049",
  "Spirited Away",
  "The Godfather",
  "Pulp Fiction",
  "Parasite",
  "Interstellar",
  "Alien",
];

export const SearchScene: React.FC<{ progress?: number }> = () => {
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const [typedTitle, setTypedTitle] = useState("");
  const [titleIdx, setTitleIdx] = useState(0);

  // Typing effect cycling real movie titles
  useEffect(() => {
    const target = SAMPLE_TITLES[titleIdx % SAMPLE_TITLES.length];
    let charIdx = 0;
    setTypedTitle("");

    const interval = setInterval(() => {
      charIdx++;
      setTypedTitle(target.slice(0, charIdx));
      if (charIdx >= target.length) {
        clearInterval(interval);
        setTimeout(() => {
          setTitleIdx((prev) => prev + 1);
        }, 1800);
      }
    }, 65);

    return () => clearInterval(interval);
  }, [titleIdx]);

  return (
    <div className="relative w-full max-w-2xl mx-auto flex flex-col items-center justify-center text-center px-4">
      {/* Projector Light Cone */}
      <ProjectorBeam active={true} />

      <div className="relative z-10 w-full flex flex-col items-center gap-6">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            01/ Search
          </span>
          <h2 className="text-2xl sm:text-3xl font-bold text-[#f2efe6] tracking-tight">
            Looking for something specific?
          </h2>
          <p className="text-sm text-[#9a9aa0] max-w-md mx-auto">
            Find any title across ten thousand films. Typo-tolerant with instant previews.
          </p>
        </div>

        {/* Big Search Input Trigger */}
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="w-full flex items-center justify-between px-5 py-4 rounded-xl bg-[#121316]/90 border border-[#26282e] hover:border-[#f5a524]/60 shadow-2xl backdrop-blur-md transition-all text-left group focus:outline-none focus:ring-2 focus:ring-[#f5a524]"
          aria-label="Open film search modal"
        >
          <div className="flex items-center gap-3">
            <Search className="w-5 h-5 text-[#f5a524] group-hover:scale-110 transition-transform" />
            <span className="text-sm sm:text-base text-[#9a9aa0] font-medium">
              Try searching <span className="text-[#f2efe6] font-semibold">"{typedTitle}"</span>
              <span className="inline-block w-1.5 h-4 ml-0.5 bg-[#f5a524] animate-pulse align-middle" />
            </span>
          </div>

          <div className="flex items-center gap-1 font-mono text-[11px] text-[#9a9aa0] bg-[#26282e]/60 px-2.5 py-1 rounded-md">
            <span>Press</span>
            <kbd className="text-[#f2efe6] font-bold">/</kbd>
          </div>
        </button>
      </div>
    </div>
  );
};
