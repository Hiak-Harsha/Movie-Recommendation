"use client";
import React, { useEffect, useRef, useCallback } from "react";
import { useAppStore } from "../core/store";
import { SCENES, TOTAL_STORY_VH } from "./scenes.config";
import { useModeSwitch } from "./modeSwitch";
import { Stage } from "./Stage";

// Stack Mode Panels
import { HeroScene } from "./HeroScene";
import { SearchPanel } from "../modules/search";
import { TastePanel } from "../modules/taste";
import { ForYouPanel } from "../modules/foryou";
import { TunePanel } from "../modules/tune";
import { LibraryPanel } from "../modules/library";
import { ClosingScene } from "./ClosingScene";
import { Dock } from "./Dock";

export const Story: React.FC = () => {
  useModeSwitch();
  const isStageMode = useAppStore((s) => s.isStageMode);
  const setActiveScene = useAppStore((s) => s.setActiveScene);
  const setStoryProgress = useAppStore((s) => s.setStoryProgress);

  const storyRef = useRef<HTMLDivElement>(null);

  const handleScroll = useCallback(() => {
    if (!storyRef.current || !isStageMode) return;
    const rect = storyRef.current.getBoundingClientRect();
    const totalScrollable = storyRef.current.scrollHeight - window.innerHeight;
    if (totalScrollable <= 0) return;

    const scrolled = -rect.top;
    const progress = Math.max(0, Math.min(1, scrolled / totalScrollable));
    setStoryProgress(progress);

    // Compute which scene is active based on vh percentage
    const currentVh = progress * TOTAL_STORY_VH;
    const sceneIdx = SCENES.findIndex(
      (s) => currentVh >= s.startVh && currentVh <= s.endVh
    );
    const activeIdx = sceneIdx !== -1 ? sceneIdx : (currentVh < SCENES[0].startVh ? 0 : SCENES.length - 1);
    const activeScene = SCENES[activeIdx];

    setActiveScene(activeScene.id, activeIdx);
  }, [isStageMode, setActiveScene, setStoryProgress]);

  useEffect(() => {
    window.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();
    return () => window.removeEventListener("scroll", handleScroll);
  }, [handleScroll]);

  // STACK MODE: Render natural vertical sections on mobile/reduced-motion
  if (!isStageMode) {
    return (
      <div className="w-full min-h-screen bg-[#0b0b0c] text-[#f2efe6] flex flex-col pb-24">
        <section id="showcase" className="min-h-screen flex items-center justify-center py-12">
          <HeroScene />
        </section>

        <section id="search" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <SearchPanel />
        </section>

        <section id="taste" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <TastePanel />
        </section>

        <section id="for-you" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <ForYouPanel />
        </section>

        <section id="tune" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <TunePanel />
        </section>

        <section id="library" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <LibraryPanel />
        </section>

        <section id="closing" className="min-h-screen flex items-center justify-center py-12 border-t border-[#26282e]/50">
          <ClosingScene />
        </section>

        {/* Dock on mobile/stack mode */}
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
