"use client";

import React from "react";
import { useStore } from "@/lib/store";
import Navbar from "@/components/Navbar";
import HeroWordmark from "@/components/HeroWordmark";
import MarqueeTicker from "@/components/MarqueeTicker";
import PinnedStudioWorkflow from "@/components/PinnedStudioWorkflow";
import SearchModal from "@/components/SearchModal";
import MovieDetailModal from "@/components/MovieDetailModal";
import ForYouView from "@/components/views/ForYouView";
import DiscoverView from "@/components/views/DiscoverView";
import SimilarView from "@/components/views/SimilarView";
import WatchlistView from "@/components/views/WatchlistView";
import InsightsView from "@/components/views/InsightsView";
import { Film, CheckCircle2 } from "lucide-react";

export default function Home() {
  const { activeTab, toastMessage } = useStore();

  return (
    <div className="min-h-screen flex flex-col bg-[#0b0b0c] text-zinc-100">
      {/* Sticky Navigation */}
      <Navbar />

      {/* Hero Presentation */}
      <HeroWordmark />

      {/* Marquee Ticker */}
      <MarqueeTicker />

      {/* Main Studio Workspace Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {activeTab === "foryou" && <ForYouView />}
        {activeTab === "discover" && <DiscoverView />}
        {activeTab === "similar" && <SimilarView />}
        {activeTab === "watchlist" && <WatchlistView />}
        {activeTab === "insights" && <InsightsView />}
      </main>

      {/* Pinned Engine Choreography Section */}
      <PinnedStudioWorkflow />

      {/* Global Modals & Drawers */}
      <SearchModal />
      <MovieDetailModal />

      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 border border-amber-500/40 text-amber-300 text-xs font-mono shadow-2xl animate-in slide-in-from-bottom-5 duration-200">
          <CheckCircle2 className="w-4 h-4 text-amber-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-zinc-900 bg-[#0a0a0c] py-12 text-xs text-zinc-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-6 h-6 rounded-md bg-amber-500 flex items-center justify-center">
              <Film className="w-3.5 h-3.5 text-black" />
            </div>
            <span className="font-mono font-bold text-zinc-300">
              CINEMATCH v2
            </span>
            <span>•</span>
            <span>Production Movie Recommendation Product</span>
          </div>

          <div className="text-center sm:text-right space-y-1">
            <p>GroupLens MovieLens ml-latest-small • 100,836 ratings • 610 users • 9,742 movies</p>
            <p className="font-mono text-[11px] text-zinc-600">
              Harper and Konstan (2015) Citation • Research & Development License
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
