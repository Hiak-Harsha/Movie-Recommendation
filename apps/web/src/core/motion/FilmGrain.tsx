"use client";
import React from "react";
import { useAppStore } from "../store";

export const FilmGrain: React.FC = () => {
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  if (reducedMotion) return null;

  return (
    <div
      aria-hidden="true"
      data-decor="true"
      className="pointer-events-none fixed inset-0 z-10 opacity-[0.06] mix-blend-overlay"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        backgroundRepeat: "repeat",
      }}
    />
  );
};
