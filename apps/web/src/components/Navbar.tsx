"use client";

import React, { useEffect, useState } from "react";
import { useStore, WorkspaceTab } from "@/lib/store";
import { apiClient, DemoProfile } from "@cinematch/api-client";
import { surfaceCopy } from "@/copy/en";
import { Search, Film, Sparkles, Compass, Bookmark, HelpCircle, Check, User as UserIcon } from "lucide-react";

export default function Navbar() {
  const {
    activeTab,
    setActiveTab,
    userId,
    username,
    watchlistCount,
    setUser,
    setIsSearchOpen,
    setIsAboutOpen,
    setToast,
  } = useStore();

  const [demoProfiles, setDemoProfiles] = useState<DemoProfile[]>([]);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    // Initialize session
    const savedUserId = localStorage.getItem("cinematch_user_id");
    apiClient
      .getOrCreateUser(undefined, savedUserId || undefined)
      .then((user) => {
        localStorage.setItem("cinematch_user_id", user.id);
        setUser(user.id, user.username, user.rating_count, user.watchlist_count);
      })
      .catch(() => {});

    // Fetch demo profiles
    apiClient
      .getDemoProfiles()
      .then((profiles) => setDemoProfiles(profiles))
      .catch(() => {});
  }, [setUser]);

  const handleSelectDemo = async (demoUserId: number) => {
    try {
      setShowUserMenu(false);
      setToast(`Loading taste profile...`);
      await apiClient.loadDemoRatings(demoUserId, userId);
      const updated = await apiClient.getUserProfile(userId);
      setUser(updated.id, `Demo #${demoUserId}`, updated.rating_count, updated.watchlist_count);
      setToast(`Loaded picks for Demo #${demoUserId}!`);
    } catch (e: any) {
      setToast(`Failed to load profile: ${e.message}`);
    }
  };

  const navItems: { tab: WorkspaceTab; label: string; icon: React.ElementType; count?: number }[] = [
    { tab: "foryou", label: "For You", icon: Sparkles },
    { tab: "discover", label: "Discover", icon: Compass },
    { tab: "similar", label: "Similar", icon: Film },
    { tab: "watchlist", label: surfaceCopy.nav.library, icon: Bookmark, count: watchlistCount },
  ];

  return (
    <header className="sticky top-0 z-40 w-full glass-nav transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Wordmark */}
        <div className="flex items-center gap-3">
          <div
            onClick={() => setActiveTab("foryou")}
            className="cursor-pointer flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform duration-300">
              <Film className="w-4 h-4 text-black stroke-[2.5]" />
            </div>
            <span className="font-mono text-lg font-bold tracking-tight text-white group-hover:text-amber-400 transition-colors">
              {surfaceCopy.brand.name}
            </span>
          </div>
        </div>

        {/* Studio Workspace Nav Pills */}
        <nav className="hidden lg:flex items-center gap-1 p-1 rounded-full bg-[#161619] border border-white/5 shadow-inner">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.tab;
            return (
              <button
                key={item.tab}
                onClick={() => setActiveTab(item.tab)}
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 cursor-pointer ${
                  isActive
                    ? "bg-amber-500 text-black font-semibold shadow-md shadow-amber-500/20"
                    : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-black" : "text-zinc-400"}`} />
                <span>{item.label}</span>
                {item.count !== undefined && item.count > 0 && (
                  <span
                    className={`ml-0.5 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                      isActive ? "bg-black text-amber-400" : "bg-zinc-800 text-zinc-300"
                    }`}
                  >
                    {item.count}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right Side Actions: Search, About & Profile */}
        <div className="flex items-center gap-2.5">
          {/* Quick Search Trigger */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#18181c] hover:bg-[#222228] border border-white/10 text-xs text-zinc-400 hover:text-zinc-200 transition-all cursor-pointer shadow-sm"
          >
            <Search className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline">{surfaceCopy.nav.searchFilms}</span>
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-black/40 border border-white/10 text-[10px] font-mono text-zinc-500">
              /
            </kbd>
          </button>

          {/* About Drawer Trigger */}
          <button
            onClick={() => setIsAboutOpen(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#18181c] hover:bg-[#222228] border border-white/10 text-xs text-zinc-400 hover:text-amber-400 transition-all cursor-pointer shadow-sm"
            title="About CineMatch (?)"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span className="hidden md:inline">{surfaceCopy.nav.about}</span>
          </button>

          {/* User Profile Pill */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#18181c] hover:bg-[#222228] border border-white/10 text-xs font-medium text-zinc-300 transition-all cursor-pointer shadow-sm"
            >
              <div className="w-5 h-5 rounded-full bg-gradient-to-tr from-amber-500 to-amber-300 flex items-center justify-center text-[10px] font-bold text-black font-mono">
                {username ? username.charAt(0).toUpperCase() : "U"}
              </div>
              <span className="max-w-[80px] sm:max-w-[120px] truncate">{username}</span>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-64 rounded-xl bg-[#18181c] border border-white/10 shadow-2xl p-2 z-50 transition-all">
                <div className="px-3 py-2 border-b border-white/5">
                  <p className="text-xs font-semibold text-zinc-200">{username}</p>
                  <p className="text-[10px] text-zinc-500 font-mono mt-0.5">Taste Profile Active</p>
                </div>

                <div className="py-2">
                  <p className="px-3 text-[10px] font-mono uppercase tracking-wider text-zinc-500 mb-1">
                    Preset Tastes
                  </p>
                  {demoProfiles.map((p) => (
                    <button
                      key={p.userId}
                      onClick={() => handleSelectDemo(p.userId)}
                      className="w-full flex items-center justify-between px-3 py-1.5 text-xs text-left rounded-lg text-zinc-300 hover:bg-white/5 hover:text-amber-400 transition-colors cursor-pointer"
                    >
                      <span className="truncate">{p.username}</span>
                      <span className="text-[10px] text-zinc-500 font-mono">#{p.userId}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
