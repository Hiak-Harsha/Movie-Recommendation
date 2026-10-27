"use client";
import React from "react";
import { useAppStore } from "../store";

export const ProjectorBeam: React.FC<{ active?: boolean }> = ({ active = false }) => {
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  if (!active) return null;

  return (
    <div
      aria-hidden="true"
      data-decor="true"
      className="pointer-events-none absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-96 z-0"
      style={{
        background: "radial-gradient(ellipse at top center, rgba(245, 165, 36, 0.14) 0%, rgba(245, 165, 36, 0.03) 45%, transparent 75%)",
        clipPath: "polygon(40% 0%, 60% 0%, 95% 100%, 5% 100%)",
        animation: reducedMotion ? "none" : "projectorFlicker 4s infinite alternate ease-in-out",
      }}
    />
  );
};
