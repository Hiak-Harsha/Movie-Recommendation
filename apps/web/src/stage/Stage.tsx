"use client";
import React, { useEffect, useState, useMemo } from "react";
import { useAppStore } from "../core/store";
import { SCENES } from "./scenes.config";
import { PosterWall } from "./PosterWall";
import { SceneRail } from "./SceneRail";
import { Dock } from "./Dock";
import { FilmGrain } from "../core/motion/FilmGrain";
import { SceneLayer } from "./SceneLayer";
import { useSceneTransition } from "./useSceneTransition";
import { api } from "../core/client";
import type { MovieCard } from "@cinematch/api-client";

// Stage Scenes
import { HeroScene } from "./HeroScene";
import { SearchScene } from "../modules/search";
import { TasteScene } from "../modules/taste";
import { ForYouScene } from "../modules/foryou";
import { TuneScene } from "../modules/tune";
import { LibraryScene } from "../modules/library";
import { ClosingScene } from "./ClosingScene";

export const Stage: React.FC = () => {
  const activeSceneIndex = useAppStore((s) => s.activeSceneIndex);
  const [showcaseMovies, setShowcaseMovies] = useState<MovieCard[]>([]);

  const { visibleIndex, phase, direction } = useSceneTransition(activeSceneIndex);

  useEffect(() => {
    let mounted = true;
    api.getShowcaseMovies()
      .then((res) => {
        if (mounted && res.movies) {
          setShowcaseMovies(res.movies);
        }
      })
      .catch((err) => {
        console.error("Failed to load showcase movies:", err);
      });

    return () => {
      mounted = false;
    };
  }, []);

  // Compute wall blur: rack focus (0px in scene 0, ramps to 10px in scenes 1-5, 8px in scene 6)
  const wallBlur = useMemo(() => {
    if (activeSceneIndex === 0) return 0;
    if (activeSceneIndex === 6) return 8;
    return 10;
  }, [activeSceneIndex]);

  const activeScene = SCENES[activeSceneIndex] || SCENES[0];

  return (
    <div
      className="sticky top-0 h-[100svh] w-full overflow-hidden bg-[#0b0b0c] text-[#f2efe6] flex flex-col justify-between"
      style={{ zIndex: 10 }}
    >
      {/* Background Poster Wall (Hardware accelerated, normal-blend scrim) */}
      <PosterWall
        movies={showcaseMovies}
        blurPx={wallBlur}
        activeSceneIndex={activeSceneIndex}
      />

      {/* Cinematic Letterbox Bars (Mounted at Stage root, completely retracted outside Scene 00) */}
      <div
        aria-hidden="true"
        data-decor="true"
        className={`fixed top-0 left-0 right-0 h-[12vh] bg-black origin-top pointer-events-none transition-transform duration-100 ${
          activeSceneIndex === 0 ? "visible opacity-100" : "hidden opacity-0"
        }`}
        style={{
          zIndex: 25,
          transform: "scaleY(calc(1 - var(--letterbox, 0)))",
        }}
      />
      <div
        aria-hidden="true"
        data-decor="true"
        className={`fixed bottom-0 left-0 right-0 h-[12vh] bg-black origin-bottom pointer-events-none transition-transform duration-100 ${
          activeSceneIndex === 0 ? "visible opacity-100" : "hidden opacity-0"
        }`}
        style={{
          zIndex: 25,
          transform: "scaleY(calc(1 - var(--letterbox, 0)))",
        }}
      />

      {/* Subtle Analog Film Grain Overlay */}
      <FilmGrain />

      {/* Screen Reader Live Region */}
      <div
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {`Scene ${activeScene.number}: ${activeScene.label}`}
      </div>

      {/* Left Pinned Scene Rail (Desktop only, z-index 20) */}
      <SceneRail />

      {/* Dedicated Scene Viewport (Section 4.2) */}
      <div className="scene-viewport">
        {/* Scene 00: Hero Showcase */}
        <SceneLayer index={0} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <HeroScene />
        </SceneLayer>

        {/* Scene 01: Search */}
        <SceneLayer index={1} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <SearchScene />
        </SceneLayer>

        {/* Scene 02: Taste Grid */}
        <SceneLayer index={2} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <TasteScene />
        </SceneLayer>

        {/* Scene 03: For You Curated Shelves */}
        <SceneLayer index={3} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <ForYouScene />
        </SceneLayer>

        {/* Scene 04: Tune Faders */}
        <SceneLayer index={4} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <TuneScene />
        </SceneLayer>

        {/* Scene 05: Library Tickets */}
        <SceneLayer index={5} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <LibraryScene />
        </SceneLayer>

        {/* Scene 06: Closing & Credits */}
        <SceneLayer index={6} visibleIndex={visibleIndex} phase={phase} direction={direction}>
          <ClosingScene />
        </SceneLayer>
      </div>

      {/* Floating Navigation Dock (z-index 30) */}
      <Dock />
    </div>
  );
};
