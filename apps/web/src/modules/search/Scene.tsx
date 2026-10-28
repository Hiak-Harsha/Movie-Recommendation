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

export const SearchScene: React.FC = () => {
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  const [typedTitle, setTypedTitle] = useState(SAMPLE_TITLES[0]);
  const [titleIdx, setTitleIdx] = useState(0);

  const isActive = activeSceneIndex === 1;

  // Typing effect cycling real movie titles (pauses when scene is inactive or reduced motion)
  useEffect(() => {
    if (!isActive || reducedMotion) {
      return;
    }

    const target = SAMPLE_TITLES[titleIdx % SAMPLE_TITLES.length];
    let charIdx = 0;

    const interval = setInterval(() => {
      charIdx++;
      setTypedTitle(target.slice(0, charIdx));
      if (charIdx >= target.length) {
        clearInterval(interval);
        const timeout = setTimeout(() => {
          setTitleIdx((prev) => prev + 1);
        }, 1800);
        return () => clearTimeout(timeout);
      }
    }, 65);

    return () => clearInterval(interval);
  }, [titleIdx, isActive, reducedMotion]);

  return (
    <div className="relative w-full max-w-2xl mx-auto flex flex-col items-center justify-center text-center px-4 my-auto select-none">
      {/* Projector Light Cone */}
      <ProjectorBeam active={isActive} />

      <div className="relative z-10 w-full flex flex-col items-center gap-6">
        <div className="flex flex-col gap-2">
          <span className="font-mono text-xs uppercase tracking-widest text-[#f5a524]">
            01/ Search
          </span>
          <h2 className="text-fluid-h2 font-display font-bold text-[#f2efe6] tracking-tight">
            Looking for something specific?
          </h2>
          <p className="text-sm text-[#9a9aa0] max-w-md mx-auto text-fluid-body">
            Find any title across ten thousand films. Typo-tolerant with instant previews.
          </p>
        </div>

        {/* Big Search Input Trigger */}
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="w-full flex items-center justify-between px-5 py-4 rounded-xl bg-[#121316]/95 border border-[#26282e] hover:border-[#f5a524]/60 shadow-2xl backdrop-blur-md transition-all text-left group focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f5a524] cursor-pointer"
          aria-label="Open film search modal"
        >
          <div className="flex items-center gap-3 overflow-hidden min-w-0">
            <Search className="w-5 h-5 text-[#f5a524] group-hover:scale-110 transition-transform shrink-0" />
            <span className="text-sm sm:text-base text-[#9a9aa0] font-medium truncate">
              Try searching <span className="text-[#f2efe6] font-semibold">&ldquo;{typedTitle}&rdquo;</span>
              {!reducedMotion && (
                <span className="inline-block w-1.5 h-4 ml-0.5 bg-[#f5a524] animate-pulse align-middle" />
              )}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1 font-mono text-[11px] text-[#9a9aa0] bg-[#26282e]/60 px-2.5 py-1 rounded-md shrink-0">
            <span>Press</span>
            <kbd className="text-[#f2efe6] font-bold">/</kbd>
          </div>
        </button>
      </div>
    </div>
  );
};
