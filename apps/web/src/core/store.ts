import { create } from "zustand";

export interface CineMatchState {
  // Navigation & Stage
  activeScene: string;
  activeSceneIndex: number;
  storyProgress: number; // 0.0 to 1.0
  isStageMode: boolean;
  reducedMotion: boolean;

  setActiveScene: (id: string, index: number) => void;
  setStoryProgress: (progress: number) => void;
  setIsStageMode: (isStage: boolean) => void;
  setReducedMotion: (reduced: boolean) => void;

  // Session & Counts
  userId: string;
  picksCount: number;
  libraryCount: number;
  hasPicks: boolean;

  setSession: (session: { userId: string; picksCount: number; libraryCount: number; hasPicks: boolean }) => void;
  incrementPicks: () => void;
  decrementPicks: () => void;
  updateLibraryCount: (delta: number) => void;

  // Overlays & Drawers
  isSearchOpen: boolean;
  setIsSearchOpen: (open: boolean) => void;

  isAboutOpen: boolean;
  setIsAboutOpen: (open: boolean) => void;
  aboutTab: "howToUse" | "howItWorks" | "dataCredits" | "terms" | "modelReport";
  setAboutTab: (tab: "howToUse" | "howItWorks" | "dataCredits" | "terms" | "modelReport") => void;

  selectedMovieId: number | null;
  setSelectedMovieId: (id: number | null) => void;

  // Undo Toast (5-second auto dismiss)
  toast: { message: string; undoAction?: () => void } | null;
  setToast: (toast: { message: string; undoAction?: () => void } | null) => void;
}

export const useAppStore = create<CineMatchState>((set) => ({
  activeScene: "scene00",
  activeSceneIndex: 0,
  storyProgress: 0,
  isStageMode: true,
  reducedMotion: false,

  setActiveScene: (activeScene, activeSceneIndex) => set({ activeScene, activeSceneIndex }),
  setStoryProgress: (storyProgress) => set({ storyProgress }),
  setIsStageMode: (isStageMode) => set({ isStageMode }),
  setReducedMotion: (reducedMotion) => set({ reducedMotion }),

  userId: "",
  picksCount: 0,
  libraryCount: 0,
  hasPicks: false,

  setSession: ({ userId, picksCount, libraryCount, hasPicks }) =>
    set({ userId, picksCount, libraryCount, hasPicks }),

  incrementPicks: () => set((state) => ({
    picksCount: state.picksCount + 1,
    hasPicks: state.picksCount + 1 >= 5,
  })),

  decrementPicks: () => set((state) => ({
    picksCount: Math.max(0, state.picksCount - 1),
    hasPicks: Math.max(0, state.picksCount - 1) >= 5,
  })),

  updateLibraryCount: (delta) => set((state) => ({
    libraryCount: Math.max(0, state.libraryCount + delta),
  })),

  isSearchOpen: false,
  setIsSearchOpen: (isSearchOpen) => set({ isSearchOpen }),

  isAboutOpen: false,
  setIsAboutOpen: (isAboutOpen) => set({ isAboutOpen }),
  aboutTab: "howToUse",
  setAboutTab: (aboutTab) => set({ aboutTab }),

  selectedMovieId: null,
  setSelectedMovieId: (selectedMovieId) => set({ selectedMovieId }),

  toast: null,
  setToast: (toast) => set({ toast }),
}));
