"use client";
import React, { useEffect } from "react";
import dynamic from "next/dynamic";
import { Film, Search, Info, EyeOff } from "lucide-react";
import { useAppStore } from "@/core/store";
import { api } from "@/core/client";
import { surfaceCopy } from "@/copy/en";
import { LenisProvider, scrollToScene } from "@/core/motion/LenisProvider";
import { Story } from "@/stage";
import { SearchPanel } from "@/modules/search";
import { DetailOverlay } from "@/modules/detail";
import { Toast } from "@/core/Toast";
import { useOverlapDebugger } from "@/core/motion/overlapDebug";

// Code-split About Drawer so zero technical copy or code is in first-load JS bundle
const AboutDrawer = dynamic(() => import("@/modules/about").then((m) => m.AboutDrawer), {
  ssr: false,
});

export default function HomePage() {
  useOverlapDebugger();
  const setIsSearchOpen = useAppStore((s) => s.setIsSearchOpen);
  const setIsAboutOpen = useAppStore((s) => s.setIsAboutOpen);
  const setAboutTab = useAppStore((s) => s.setAboutTab);
  const setSession = useAppStore((s) => s.setSession);
  const reducedMotion = useAppStore((s) => s.reducedMotion);
  const setReducedMotion = useAppStore((s) => s.setReducedMotion);

  // Initialize server-issued session via /api/me
  useEffect(() => {
    api.getMe()
      .then((me) => {
        setSession({
          userId: me.user_id,
          picksCount: me.picks_count,
          libraryCount: me.library_count,
          hasPicks: me.has_picks,
        });
      })
      .catch((err) => {
        console.error("Session fetch failed:", err);
      });
  }, [setSession]);

  // Global Keyboard Shortcuts (/ for search, ? for about, Esc for close)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if user is typing in an input or textarea
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA"
      ) {
        return;
      }

      if ((e.key === "k" && (e.metaKey || e.ctrlKey)) || e.key === "/") {
        e.preventDefault();
        setIsSearchOpen(true);
      } else if (e.key === "?") {
        e.preventDefault();
        setAboutTab("howToUse");
        setIsAboutOpen(true);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setIsSearchOpen, setIsAboutOpen, setAboutTab]);

  const openAbout = (tab: "howToUse" | "howItWorks" | "dataCredits" | "terms" | "modelReport") => {
    setAboutTab(tab);
    setIsAboutOpen(true);
  };

  const jumpToPicks = () => {
    scrollToScene("#taste");
  };

  return (
    <LenisProvider>
      <div className="relative min-h-screen bg-[#0b0b0c] text-[#f2efe6] selection:bg-[#f5a524]/30">
        {/* Skip to Content Accessibility Link */}
        <a
          href="#showcase"
          className="sr-only focus:not-sr-only fixed top-4 left-4 z-50 px-4 py-2 rounded-lg bg-[#f5a524] text-black font-mono text-xs font-bold"
        >
          Skip to main cinema showcase
        </a>

        {/* Minimalist Floating Header with Scrim (z-30) */}
        <header
          className="fixed top-0 left-0 right-0 flex items-center justify-between px-4 sm:px-6 py-3 sm:py-4 pointer-events-none transition-all"
          style={{
            zIndex: 30,
            background: "linear-gradient(180deg, rgba(11, 11, 12, 0.95) 0%, rgba(11, 11, 12, 0.75) 60%, transparent 100%)",
            backdropFilter: "blur(12px)",
            WebkitBackdropFilter: "blur(12px)",
          }}
        >
          {/* Logo */}
          <div className="pointer-events-auto flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-[#f5a524] flex items-center justify-center shadow-lg shadow-amber-500/20">
              <Film className="w-4 h-4 text-black" />
            </div>
            <span className="font-mono font-black tracking-widest text-sm text-[#f2efe6]">
              {surfaceCopy.brand.name}
            </span>
          </div>

          {/* Header Controls */}
          <nav aria-label="Main Navigation" className="pointer-events-auto flex items-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={jumpToPicks}
              className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#121316] border border-transparent hover:border-[#26282e] transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#f5a524]"
            >
              <span>{surfaceCopy.nav.startPicking}</span>
            </button>

            <button
              type="button"
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#121316] border border-transparent hover:border-[#26282e] transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#f5a524]"
              aria-label="Search films (Press /)"
            >
              <Search className="w-3.5 h-3.5 text-[#f5a524]" />
              <span className="hidden sm:inline">{surfaceCopy.nav.searchFilms}</span>
            </button>

            <button
              type="button"
              onClick={() => openAbout("howToUse")}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-mono text-[#9a9aa0] hover:text-[#f2efe6] hover:bg-[#121316] border border-transparent hover:border-[#26282e] transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#f5a524]"
              aria-label="Open About and Methodology (Press ?)"
            >
              <Info className="w-3.5 h-3.5 text-[#f5a524]" />
              <span className="hidden sm:inline">{surfaceCopy.nav.about}</span>
            </button>

            <button
              type="button"
              onClick={() => setReducedMotion(!reducedMotion)}
              title={reducedMotion ? "Enable animations" : "Reduce motion"}
              className={`p-1.5 rounded-full border transition-colors cursor-pointer focus-visible:ring-2 focus-visible:ring-[#f5a524] ${
                reducedMotion
                  ? "bg-amber-500/20 border-amber-500/40 text-amber-300"
                  : "bg-transparent border-transparent text-[#9a9aa0] hover:text-[#f2efe6]"
              }`}
              aria-label="Toggle reduced motion"
            >
              <EyeOff className="w-3.5 h-3.5" />
            </button>
          </nav>
        </header>

        {/* Pinned 700vh Living Story / Stage */}
        <main id="main-content">
          <Story />
        </main>

        {/* Global Overlays & Modals (Single instances with focus trap and enter/exit motion) */}
        <SearchPanel />
        <DetailOverlay />
        <AboutDrawer />

        {/* Dedicated Toast Notification (z-40, above dock) */}
        <Toast />
      </div>
    </LenisProvider>
  );
}
