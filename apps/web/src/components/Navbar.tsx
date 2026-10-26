"use client";

import React, { useEffect, useState } from "react";
import { useStore, WorkspaceTab } from "@/lib/store";
import { apiClient, DemoProfile } from "@cinematch/api-client";
import { Search, Film, Sparkles, Compass, Bookmark, BarChart2, User as UserIcon, Check } from "lucide-react";

export default function Navbar() {
  const {
    activeTab,
    setActiveTab,
    userId,
    username,
    ratingCount,
    watchlistCount,
    setUser,
    setIsSearchOpen,
    setToast,
  } = useStore();

  const [demoProfiles, setDemoProfiles] = useState<DemoProfile[]>([]);
  const [showUserMenu, setShowUserMenu] = useState(false);

  useEffect(() => {
    // Initialize guest user session in DB if needed
    const savedUserId = localStorage.getItem("cinematch_user_id");
    apiClient
      .getOrCreateUser(undefined, savedUserId || undefined)
      .then((user) => {
        localStorage.setItem("cinematch_user_id", user.id);
        setUser(user.id, user.username, user.rating_count, user.watchlist_count);
      })
      .catch(() => {});

    // Fetch demo profiles for quick user switching
    apiClient
      .getDemoProfiles()
      .then((profiles) => setDemoProfiles(profiles))
      .catch(() => {});
  }, [setUser]);

  const handleSelectDemo = async (demoUserId: number) => {
    try {
      setShowUserMenu(false);
      setToast(`Loading demo user #${demoUserId} taste profile...`);
      await apiClient.loadDemoRatings(demoUserId, userId);
      const updated = await apiClient.getUserProfile(userId);
      setUser(updated.id, `Demo #${demoUserId} Profile`, updated.rating_count, updated.watchlist_count);
      setToast(`Loaded ${updated.rating_count} real ratings for Demo #${demoUserId}!`);
    } catch (e: any) {
      setToast(`Failed to load demo profile: ${e.message}`);
    }
  };

  const navItems: { tab: WorkspaceTab; label: string; icon: React.ElementType; count?: number }[] = [
    { tab: "foryou", label: "For You", icon: Sparkles },
    { tab: "discover", label: "Discover", icon: Compass },
    { tab: "similar", label: "Similar Movies", icon: Film },
    { tab: "watchlist", label: "Watchlist", icon: Bookmark, count: watchlistCount },
    { tab: "insights", label: "Model Insights", icon: BarChart2 },
  ];

  return (
    <header className="sticky top-0 z-40 w-full glass-nav transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Wordmark & Status Indicator */}
        <div className="flex items-center gap-3">
          <div
            onClick={() => setActiveTab("foryou")}
            className="cursor-pointer flex items-center gap-2 group"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-500 to-amber-700 flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:scale-105 transition-transform duration-300">
              <Film className="w-4 h-4 text-black stroke-[2.5]" />
            </div>
            <span className="font-mono text-lg font-bold tracking-tight text-white group-hover:text-amber-400 transition-colors">
              CINEMATCH<span className="text-amber-500 text-xs ml-1 font-mono tracking-widest">v2</span>
            </span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-[11px] font-mono text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>SERVING ALS HYBRID</span>
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
                className={`relative flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
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

        {/* Right Side Actions: Search & User Switcher */}
        <div className="flex items-center gap-2.5">
          {/* Quick Search Trigger */}
          <button
            onClick={() => setIsSearchOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#18181c] hover:bg-[#222228] border border-white/10 text-xs text-zinc-400 hover:text-zinc-200 transition-all cursor-pointer shadow-sm"
          >
            <Search className="w-3.5 h-3.5 text-zinc-400" />
            <span className="hidden sm:inline">Search 9.7k movies</span>
            <kbd className="hidden sm:inline-block px-1.5 py-0.5 rounded bg-black/40 border border-white/10 text-[10px] font-mono text-zinc-500">
              /
            </kbd>
          </button>

          {/* User Account / Demo Profile Selector */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#18181c] hover:bg-[#222228] border border-white/10 text-xs text-zinc-300 transition-all cursor-pointer"
            >
              <UserIcon className="w-3.5 h-3.5 text-amber-400" />
              <span className="max-w-[100px] truncate font-medium">{username}</span>
              <span className="px-1.5 py-0.5 rounded bg-zinc-800 font-mono text-[10px] text-zinc-400">
                {ratingCount}★
              </span>
            </button>

            {/* Dropdown Menu */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-72 rounded-xl bg-[#121215] border border-zinc-800 shadow-2xl p-2 z-50">
                <div className="px-3 py-2 border-b border-zinc-800/80 mb-1">
                  <p className="text-[11px] font-mono uppercase tracking-wider text-zinc-500">
                    Switch Taste Profile
                  </p>
                  <p className="text-xs text-zinc-300 mt-0.5 font-medium">
                    Test how recommendations adapt to different real MovieLens user histories.
                  </p>
                </div>

                <div className="space-y-1">
                  {demoProfiles.map((p) => (
                    <button
                      key={p.userId}
                      onClick={() => handleSelectDemo(p.userId)}
                      className="w-full text-left px-3 py-2 rounded-lg hover:bg-zinc-800/60 transition-colors flex items-center justify-between group"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs text-amber-400 font-semibold">
                            User #{p.userId}
                          </span>
                          <span className="text-[11px] text-zinc-400 font-normal">
                            ({p.rating_count} ratings)
                          </span>
                        </div>
                        <p className="text-[11px] text-zinc-500 truncate mt-0.5">
                          {p.label}
                        </p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Nav Bar */}
      <div className="lg:hidden border-t border-white/5 px-2 py-1.5 flex items-center justify-around bg-[#0e0e11]">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.tab;
          return (
            <button
              key={item.tab}
              onClick={() => setActiveTab(item.tab)}
              className={`flex flex-col items-center gap-1 p-2 rounded-lg text-[10px] font-medium transition-colors ${
                isActive ? "text-amber-400" : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>
    </header>
  );
}
