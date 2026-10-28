"use client";
import React, { useEffect, useRef } from "react";
import { useAppStore } from "../core/store";
import { SCENES, TOTAL_STORY_VH } from "./scenes.config";
import { useModeSwitch } from "./modeSwitch";
import { Stage } from "./Stage";

// Stack Mode Scenes (Natural Flow for Mobile / Tablet / Reduced Motion)
import { HeroScene } from "./HeroScene";
import { SearchScene } from "../modules/search";
import { TasteScene } from "../modules/taste";
import { ForYouScene } from "../modules/foryou";
import { TuneScene } from "../modules/tune";
import { LibraryScene } from "../modules/library";
import { ClosingScene } from "./ClosingScene";
import { Dock } from "./Dock";

export const Story: React.FC = () => {
  useModeSwitch();
  const isStageMode = useAppStore((s) => s.isStageMode);
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const setActiveScene = useAppStore((s) => s.setActiveScene);

  const storyRef = useRef<HTMLDivElement>(null);
  const activeIdxRef = useRef(activeSceneIndex);
  useEffect(() => {
    activeIdxRef.current = activeSceneIndex;
  }, [activeSceneIndex]);

  const rafIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (isStageMode !== true) return;

    const onScroll = () => {
      if (rafIdRef.current) return;
      rafIdRef.current = requestAnimationFrame(() => {
        rafIdRef.current = null;
        if (!storyRef.current) return;

        const rect = storyRef.current.getBoundingClientRect();
        const totalScrollable = storyRef.current.scrollHeight - window.innerHeight;
        if (totalScrollable <= 0) return;

        const scrolled = -rect.top;
        const progress = Math.max(0, Math.min(1, scrolled / totalScrollable));

        // Fast imperative CSS variable updates (bypasses React re-renders)
        storyRef.current.style.setProperty("--story-progress", progress.toFixed(4));
        const letterboxProgress = Math.min(1, progress * 15);
        storyRef.current.style.setProperty("--letterbox", letterboxProgress.toFixed(4));

        // Scene Determination with Hysteresis (Section 3.2: 4vh deadband prevents edge flicker)
        const currentVh = progress * TOTAL_STORY_VH;
        const currentIdx = activeIdxRef.current;
        let newIdx = currentIdx;

        // Check if currentVh left current scene bounds with hysteresis buffer
        const currentScene = SCENES[currentIdx];
        const lowerBound = currentIdx === 0 ? 0 : currentScene.startVh - 4;
        const upperBound = currentIdx === SCENES.length - 1 ? TOTAL_STORY_VH : currentScene.endVh + 4;

        if (currentVh < lowerBound || currentVh > upperBound) {
          // Find target scene
          for (let i = 0; i < SCENES.length; i++) {
            if (currentVh >= SCENES[i].startVh && currentVh <= SCENES[i].endVh) {
              newIdx = i;
              break;
            }
          }
          if (currentVh < SCENES[0].startVh) newIdx = 0;
          if (currentVh > SCENES[SCENES.length - 1].endVh) newIdx = SCENES.length - 1;
        }

        if (newIdx !== currentIdx) {
          activeIdxRef.current = newIdx;
          setActiveScene(SCENES[newIdx].id, newIdx);
        }
      });
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    return () => {
      window.removeEventListener("scroll", onScroll);
      if (rafIdRef.current) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    };
  }, [isStageMode, setActiveScene]);

  // SSR / Initial measurement state: render neutral hero to prevent hydration layout flash
  if (isStageMode === null) {
    return (
      <div className="w-full min-h-[100svh] bg-[#0b0b0c] text-[#f2efe6] flex items-center justify-center">
        <HeroScene />
      </div>
    );
  }

  // STACK MODE: Natural vertical scrolling flow for mobile, tablets, or prefers-reduced-motion
  if (!isStageMode) {
    return (
      <div className="w-full min-h-[100svh] bg-[#0b0b0c] text-[#f2efe6] flex flex-col pb-24">
        <section id="showcase" className="min-h-[100svh] flex items-center justify-center py-12 scroll-mt-[var(--header-h)]">
          <HeroScene />
        </section>

        <section id="search" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <SearchScene />
        </section>

        <section id="taste" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <TasteScene />
        </section>

        <section id="for-you" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <ForYouScene />
        </section>

        <section id="tune" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <TuneScene />
        </section>

        <section id="library" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <LibraryScene />
        </section>

        <section id="closing" className="min-h-[100svh] flex items-center justify-center py-12 border-t border-[#26282e]/50 scroll-mt-[var(--header-h)]">
          <ClosingScene />
        </section>

        {/* Floating Dock / Mobile Bottom Bar */}
        <Dock />
      </div>
    );
  }

  // STAGE MODE: 700vh scroll container with sticky 100svh stage and scroll anchors
  return (
    <div
      ref={storyRef}
      className="relative w-full"
      style={{ height: `${TOTAL_STORY_VH}vh` }}
    >
      {/* Anchor targets positioned throughout the 700vh height */}
      {SCENES.map((scene) => (
        <div
          key={scene.id}
          id={scene.hash.replace("#", "")}
          className="absolute left-0 w-full pointer-events-none"
          style={{
            top: `${(scene.startVh / TOTAL_STORY_VH) * 100}%`,
            height: "1px",
          }}
          aria-hidden="true"
        />
      ))}

      {/* Sticky Living Stage */}
      <Stage />
    </div>
  );
};
