"use client";
import React, { useRef, useEffect } from "react";
import gsap from "gsap";
import { SCENES } from "./scenes.config";
import { useAppStore } from "../core/store";
import { scrollToScene } from "../core/motion/LenisProvider";

const SHORT_LABELS: Record<string, string> = {
  scene00: "SHOWCASE",
  scene01: "SEARCH",
  scene02: "TASTE",
  scene03: "FOR YOU",
  scene04: "TUNE",
  scene05: "LINEUP",
  scene06: "CREDITS",
};

export const SceneRail: React.FC = () => {
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const reducedMotion = useAppStore((s) => s.reducedMotion);
  const activeScene = SCENES[activeSceneIndex] || SCENES[0];

  const labelRef = useRef<HTMLDivElement>(null);
  const prevIdxRef = useRef(activeSceneIndex);

  // Rolling label animation (Section 5.6: old out up, new in from below, 250ms)
  useEffect(() => {
    if (prevIdxRef.current === activeSceneIndex || reducedMotion) {
      prevIdxRef.current = activeSceneIndex;
      return;
    }
    prevIdxRef.current = activeSceneIndex;

    const el = labelRef.current;
    if (!el) return;

    gsap.fromTo(
      el,
      { yPercent: 100, opacity: 0 },
      { yPercent: 0, opacity: 1, duration: 0.25, ease: "power2.out" }
    );
  }, [activeSceneIndex, reducedMotion]);

  const shortLabel = SHORT_LABELS[activeScene.id] || activeScene.label.toUpperCase();

  return (
    <nav
      aria-label="Scene progress indicator"
      className="hidden lg:flex fixed left-0 top-1/2 -translate-y-1/2 flex-col items-start gap-4 select-none px-6 pointer-events-auto"
      style={{
        width: "var(--rail-w)",
        zIndex: 20,
      }}
    >
      {/* Rolling Eyebrow Label constrained within rail width */}
      <div className="h-6 overflow-hidden w-full">
        <div
          ref={labelRef}
          className="text-[11px] font-mono tracking-widest uppercase text-[#f5a524] font-semibold truncate"
        >
          {activeScene.number} / {shortLabel}
        </div>
      </div>

      {/* Numbered Scene Markers */}
      <div className="flex flex-col gap-3">
        {SCENES.map((scene, idx) => {
          const isActive = idx === activeSceneIndex;
          return (
            <button
              key={scene.id}
              type="button"
              onClick={() => scrollToScene(scene.hash)}
              className="group flex items-center gap-3 py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#f5a524] rounded-sm cursor-pointer"
              aria-label={`Jump to scene ${scene.number}: ${scene.label}`}
              aria-current={isActive ? "step" : undefined}
            >
              <span
                className={`font-mono text-xs transition-colors duration-200 ${
                  isActive
                    ? "text-[#f2efe6] font-bold"
                    : "text-[#9a9aa0]/50 group-hover:text-[#9a9aa0]"
                }`}
              >
                {scene.number}
              </span>

              {/* Progress Indicator Bar */}
              <div
                className={`h-0.5 rounded-full transition-all duration-300 ${
                  isActive
                    ? "w-8 bg-[#f5a524]"
                    : "w-2 bg-[#26282e] group-hover:w-4 group-hover:bg-[#9a9aa0]"
                }`}
              />
            </button>
          );
        })}
      </div>
    </nav>
  );
};
