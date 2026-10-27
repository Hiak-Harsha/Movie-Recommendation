"use client";
import React from "react";
import { Search, Sparkles, SlidersHorizontal, Bookmark, HelpCircle } from "lucide-react";
import { SCENES } from "./scenes.config";
import { useAppStore } from "../core/store";

export const Dock: React.FC = () => {
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const picksCount = useAppStore((s) => s.picksCount);
  const libraryCount = useAppStore((s) => s.libraryCount);
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const setIsAboutOpen = useAppStore((s) => s.setIsAboutOpen);

  const jumpToScene = (hash: string) => {
    const el = document.querySelector(hash);
    if (el) {
      el.scrollIntoView({ behavior: "smooth" });
    }
  };

  return (
    <>
      {/* Desktop Floating Pill Dock (Bottom Center, z-30) */}
      <nav
        aria-label="Quick navigation dock"
        className="hidden md:flex fixed bottom-6 left-1/2 -translate-x-1/2 z-30 items-center gap-1.5 px-4 py-2 rounded-full bg-[#121316]/85 backdrop-blur-md border border-[#26282e] shadow-2xl transition-all select-none"
      >
        {/* Search Action */}
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-mono uppercase text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#26282e]/50 transition-colors focus:outline-none focus:ring-1 focus:ring-[#f5a524]"
          aria-label="Open search dialog (Press / or Cmd+K)"
        >
          <Search className="w-3.5 h-3.5 text-[#f5a524]" />
          <span>Search</span>
          <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-[#26282e]/60 text-[#f2efe6]">
            /
          </kbd>
        </button>

        <div className="w-[1px] h-4 bg-[#26282e] mx-1" />

        {/* 7 Scene Navigation Dots */}
        <div className="flex items-center gap-1 px-1">
          {SCENES.map((scene, idx) => {
            const isActive = idx === activeSceneIndex;
            return (
              <button
                key={scene.id}
                type="button"
                onClick={() => jumpToScene(scene.hash)}
                title={`${scene.number}/ ${scene.label}`}
                aria-label={`Jump to ${scene.label}`}
                aria-current={isActive ? "true" : undefined}
                className="relative group p-1.5 rounded-full focus:outline-none"
              >
                <div
                  className={`rounded-full transition-all duration-300 ${
                    isActive
                      ? "w-4 h-2 bg-[#f5a524]"
                      : "w-2 h-2 bg-[#9a9aa0]/40 group-hover:bg-[#9a9aa0]"
                  }`}
                />
              </button>
            );
          })}
        </div>

        <div className="w-[1px] h-4 bg-[#26282e] mx-1" />

        {/* Picks Pill */}
        <button
          type="button"
          onClick={() => jumpToScene("#taste")}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#26282e]/50 transition-colors focus:outline-none focus:ring-1 focus:ring-[#f5a524]"
          aria-label={`View your ${picksCount} picks`}
        >
          <Sparkles className="w-3.5 h-3.5 text-[#f5a524]" />
          <span>Picks</span>
          <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[#f5a524]/20 text-[#f5a524] font-bold">
            {picksCount}
          </span>
        </button>

        {/* Library Pill */}
        <button
          type="button"
          onClick={() => jumpToScene("#library")}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#26282e]/50 transition-colors focus:outline-none focus:ring-1 focus:ring-[#f5a524]"
          aria-label={`View your library with ${libraryCount} saved films`}
        >
          <Bookmark className="w-3.5 h-3.5 text-[#f5a524]" />
          <span>Library</span>
          {libraryCount > 0 && (
            <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-[#26282e] text-[#f2efe6]">
              {libraryCount}
            </span>
          )}
        </button>

        <div className="w-[1px] h-4 bg-[#26282e] mx-1" />

        {/* About Button */}
        <button
          type="button"
          onClick={() => setIsAboutOpen(true)}
          className="p-1.5 rounded-full text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#26282e]/50 transition-colors focus:outline-none focus:ring-1 focus:ring-[#f5a524]"
          title="About & credits (Press ?)"
          aria-label="Open About drawer"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </nav>

      {/* Mobile Fixed Bottom Tab Bar (< 768px) */}
      <nav
        aria-label="Mobile navigation"
        className="flex md:hidden fixed bottom-0 left-0 right-0 z-30 h-14 bg-[#0b0b0c]/95 backdrop-blur-md border-t border-[#26282e] items-center justify-around px-2 pb-[env(safe-area-inset-bottom)]"
      >
        <button
          type="button"
          onClick={() => setIsSearchOpen(true)}
          className="flex flex-col items-center gap-1 text-[#9a9aa0] hover:text-[#f2efe6] focus:outline-none"
          aria-label="Search"
        >
          <Search className="w-4 h-4" />
          <span className="text-[10px] font-mono">Search</span>
        </button>

        <button
          type="button"
          onClick={() => jumpToScene("#taste")}
          className="flex flex-col items-center gap-1 text-[#9a9aa0] hover:text-[#f2efe6] focus:outline-none"
          aria-label="Picks"
        >
          <div className="relative">
            <Sparkles className="w-4 h-4" />
            {picksCount > 0 && (
              <span className="absolute -top-1 -right-2 w-3.5 h-3.5 text-[9px] rounded-full bg-[#f5a524] text-[#0b0b0c] font-bold flex items-center justify-center">
                {picksCount}
              </span>
            )}
          </div>
          <span className="text-[10px] font-mono">Picks</span>
        </button>

        <button
          type="button"
          onClick={() => jumpToScene("#for-you")}
          className="flex flex-col items-center gap-1 text-[#f5a524] focus:outline-none"
          aria-label="For You"
        >
          <div className="w-2 h-2 rounded-full bg-[#f5a524]" />
          <span className="text-[10px] font-mono font-bold">For You</span>
        </button>

        <button
          type="button"
          onClick={() => jumpToScene("#tune")}
          className="flex flex-col items-center gap-1 text-[#9a9aa0] hover:text-[#f2efe6] focus:outline-none"
          aria-label="Tune"
        >
          <SlidersHorizontal className="w-4 h-4" />
          <span className="text-[10px] font-mono">Tune</span>
        </button>

        <button
          type="button"
          onClick={() => jumpToScene("#library")}
          className="flex flex-col items-center gap-1 text-[#9a9aa0] hover:text-[#f2efe6] focus:outline-none"
          aria-label="Library"
        >
          <Bookmark className="w-4 h-4" />
          <span className="text-[10px] font-mono">Library</span>
        </button>

        <button
          type="button"
          onClick={() => setIsAboutOpen(true)}
          className="flex flex-col items-center gap-1 text-[#9a9aa0] hover:text-[#f2efe6] focus:outline-none"
          aria-label="About"
        >
          <HelpCircle className="w-4 h-4" />
          <span className="text-[10px] font-mono">About</span>
        </button>
      </nav>
    </>
  );
};
