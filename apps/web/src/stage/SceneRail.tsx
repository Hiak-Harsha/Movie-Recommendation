"use client";
import React from "react";
import { SCENES } from "./scenes.config";
import { useAppStore } from "../core/store";

export const SceneRail: React.FC = () => {
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const activeScene = SCENES[activeSceneIndex] || SCENES[0];

  return (
    <div
      aria-label="Scene progress indicator"
      className="hidden lg:flex fixed left-8 top-1/2 -translate-y-1/2 z-20 flex-col items-start gap-4 select-none"
    >
      {/* Rolling Eyebrow Label */}
      <div className="h-6 overflow-hidden">
        <div
          key={activeScene.id}
          className="text-[11px] font-mono tracking-widest uppercase text-[#f5a524] font-semibold transition-all duration-300"
        >
          {activeScene.number}/ {activeScene.label}
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
              onClick={() => {
                const el = document.querySelector(scene.hash);
                if (el) el.scrollIntoView({ behavior: "smooth" });
              }}
              className="group flex items-center gap-3 py-0.5 focus:outline-none"
              aria-label={`Jump to scene ${scene.number}: ${scene.label}`}
              aria-current={isActive ? "step" : undefined}
            >
              <span
                className={`font-mono text-xs transition-colors duration-300 ${
                  isActive
                    ? "text-[#f2efe6] font-bold"
                    : "text-[#9a9aa0]/50 group-hover:text-[#9a9aa0]"
                }`}
              >
                {scene.number}
              </span>

              {/* Progress Indicator Bar */}
              <div
                className={`h-0.5 transition-all duration-300 ${
                  isActive
                    ? "w-8 bg-[#f5a524]"
                    : "w-2 bg-[#26282e] group-hover:w-4 group-hover:bg-[#9a9aa0]"
                }`}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
};
