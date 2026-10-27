"use client";

import React from "react";
import dynamic from "next/dynamic";
import { useStore } from "@/lib/store";
import Navbar from "@/components/Navbar";
import HeroWordmark from "@/components/HeroWordmark";
import MarqueeTicker from "@/components/MarqueeTicker";
import SearchModal from "@/components/SearchModal";
import MovieDetailModal from "@/components/MovieDetailModal";
import ForYouView from "@/components/views/ForYouView";
import DiscoverView from "@/components/views/DiscoverView";
import SimilarView from "@/components/views/SimilarView";
import WatchlistView from "@/components/views/WatchlistView";
import { surfaceCopy } from "@/copy/en";
import { Film, CheckCircle2 } from "lucide-react";

// Code-split About Drawer so none of it is in the first-load bundle
const AboutDrawer = dynamic(() => import("@/modules/about/AboutDrawer"), {
  ssr: false,
});

export default function Home() {
  const { activeTab, setActiveTab, setIsSearchOpen, setIsAboutOpen, setAboutTab, toastMessage } = useStore();

  const openAboutSection = (tab: string) => {
    setAboutTab(tab);
    setIsAboutOpen(true);
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0b0c] text-zinc-100">
      {/* Sticky Navigation */}
      <Navbar />

      {/* Hero Presentation */}
      <HeroWordmark
        onStartPicking={() => setActiveTab("foryou")}
        onSearchFilms={() => setIsSearchOpen(true)}
      />

      {/* Marquee Ticker */}
      <MarqueeTicker />

      {/* Main Studio Workspace Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {activeTab === "foryou" && <ForYouView />}
        {activeTab === "discover" && <DiscoverView />}
        {activeTab === "similar" && <SimilarView />}
        {activeTab === "watchlist" && <WatchlistView />}
      </main>

      {/* Global Modals & Drawers */}
      <SearchModal />
      <MovieDetailModal />
      <AboutDrawer />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 border border-amber-500/40 text-amber-300 text-xs font-mono shadow-2xl transition-all">
          <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Clean Visitor Footer */}
      <footer className="border-t border-zinc-900 bg-[#0a0a0c] py-12 text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-md bg-amber-500 flex items-center justify-center">
              <Film className="w-3.5 h-3.5 text-black" />
            </div>
            <span className="font-mono font-bold text-zinc-300">
              {surfaceCopy.brand.name}
            </span>
            <span>•</span>
            <span>{surfaceCopy.brand.tagline}</span>
          </div>

          <div className="flex items-center gap-6">
            <button
              onClick={() => openAboutSection("howToUse")}
              className="hover:text-amber-400 transition-colors cursor-pointer"
            >
              {surfaceCopy.footer.about}
            </button>
            <button
              onClick={() => openAboutSection("terms")}
              className="hover:text-amber-400 transition-colors cursor-pointer"
            >
              {surfaceCopy.footer.terms}
            </button>
            <button
              onClick={() => openAboutSection("dataCredits")}
              className="hover:text-amber-400 transition-colors cursor-pointer"
            >
              {surfaceCopy.footer.credits}
            </button>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mt-6 pt-6 border-t border-zinc-900/60 text-center sm:text-left text-[11px] text-zinc-600">
          <p>{surfaceCopy.footer.tmdbNotice}</p>
        </div>
      </footer>
    </div>
  );
}
