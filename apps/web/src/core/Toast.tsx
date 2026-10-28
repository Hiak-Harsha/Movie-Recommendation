"use client";
import React, { useState, useEffect } from "react";
import { Sparkles, RotateCcw } from "lucide-react";
import { useAppStore } from "./store";

export const Toast: React.FC = () => {
  const toast = useAppStore((s) => s.toast);
  const setToast = useAppStore((s) => s.setToast);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (!toast || isPaused) return;

    const timer = setTimeout(() => {
      setToast(null);
    }, 5000);

    return () => clearTimeout(timer);
  }, [toast, setToast, isPaused]);

  if (!toast) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onFocus={() => setIsPaused(true)}
      onBlur={() => setIsPaused(false)}
      className="fixed left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2.5 rounded-full bg-[#121316]/95 backdrop-blur-md border border-[#f5a524]/50 text-[#f2efe6] text-xs font-mono shadow-2xl transition-all duration-200 select-none pointer-events-auto"
      style={{
        bottom: "calc(var(--dock-h) + 1rem + env(safe-area-inset-bottom, 0px))",
        zIndex: 40,
      }}
    >
      <Sparkles className="w-3.5 h-3.5 text-[#f5a524] shrink-0" />
      <span>{toast.message}</span>
      {toast.undoAction && (
        <button
          type="button"
          onClick={() => {
            toast.undoAction?.();
            setToast(null);
          }}
          className="flex items-center gap-1 ml-2 px-2.5 py-0.5 rounded-full bg-[#f5a524] text-black font-bold hover:bg-[#e0941c] active:scale-95 transition-all cursor-pointer"
        >
          <RotateCcw className="w-3 h-3" />
          <span>Undo</span>
        </button>
      )}
    </div>
  );
};
