import { create } from "zustand";

export type WorkspaceTab = "discover" | "similar" | "foryou" | "watchlist" | "insights";

interface CineMatchState {
  // Navigation
  activeTab: WorkspaceTab;
  setActiveTab: (tab: WorkspaceTab) => void;

  // Active User / Session
  userId: string;
  username: string;
  ratingCount: number;
  watchlistCount: number;
  selectedDemoUserId: number | null;
  setUser: (userId: string, username: string, ratingCount?: number, watchlistCount?: number) => void;
  setSelectedDemoUserId: (demoId: number | null) => void;
  incrementRatings: () => void;
  decrementRatings: () => void;
  updateWatchlistCount: (delta: number) => void;

  // Global Modals & Drawers
  selectedMovieId: number | null;
  setSelectedMovieId: (id: number | null) => void;

  isSearchOpen: boolean;
  setIsSearchOpen: (open: boolean) => void;

  // Similar Movies Seed
  seedMovieId: number;
  setSeedMovieId: (id: number) => void;

  // Toast / Status Message
  toastMessage: string | null;
  setToast: (msg: string | null) => void;
}

export const useStore = create<CineMatchState>((set) => ({
  activeTab: "foryou",
  setActiveTab: (tab) => set({ activeTab: tab }),

  userId: "guest_default",
  username: "Guest Explorer",
  ratingCount: 0,
  watchlistCount: 0,
  selectedDemoUserId: null,

  setUser: (userId, username, ratingCount = 0, watchlistCount = 0) =>
    set({ userId, username, ratingCount, watchlistCount }),

  setSelectedDemoUserId: (demoId) => set({ selectedDemoUserId: demoId }),

  incrementRatings: () => set((state) => ({ ratingCount: state.ratingCount + 1 })),
  decrementRatings: () => set((state) => ({ ratingCount: Math.max(0, state.ratingCount - 1) })),
  updateWatchlistCount: (delta) =>
    set((state) => ({ watchlistCount: Math.max(0, state.watchlistCount + delta) })),

  selectedMovieId: null,
  setSelectedMovieId: (id) => set({ selectedMovieId: id }),

  isSearchOpen: false,
  setIsSearchOpen: (open) => set({ isSearchOpen: open }),

  seedMovieId: 1, // Toy Story default
  setSeedMovieId: (id) => set({ seedMovieId: id }),

  toastMessage: null,
  setToast: (msg) => {
    set({ toastMessage: msg });
    if (msg) {
      setTimeout(() => set({ toastMessage: null }), 3000);
    }
  },
}));
