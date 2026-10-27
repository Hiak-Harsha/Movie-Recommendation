"use client";
import React, { useEffect, useState, useMemo } from "react";
import { useAppStore } from "../core/store";
import { SCENES } from "./scenes.config";
import { PosterWall } from "./PosterWall";
import { SceneRail } from "./SceneRail";
import { Dock } from "./Dock";
import { FilmGrain } from "../core/motion/FilmGrain";
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
  const storyProgress = useAppStore((s) => s.storyProgress);
  const [showcaseMovies, setShowcaseMovies] = useState<MovieCard[]>([]);

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

  // Compute wall blur: rack focus (0px in scene 0, ramps to 12px in scenes 1-5, dim in 6)
  const wallBlur = useMemo(() => {
    if (activeSceneIndex === 0) return 0;
    if (activeSceneIndex === 6) return 8;
    return 12;
  }, [activeSceneIndex]);

  const activeScene = SCENES[activeSceneIndex] || SCENES[0];

  return (
    <div
      className="sticky top-0 h-[100svh] w-full overflow-hidden bg-[#0b0b0c] text-[#f2efe6] flex flex-col justify-between"
      style={{ zIndex: 10 }}
    >
      {/* Background Poster Wall */}
      <PosterWall
        movies={showcaseMovies}
        progress={storyProgress}
        blurPx={wallBlur}
      />

      {/* Subtle Analog Film Grain Overlay */}
      <FilmGrain />

      {/* Screen Reader Polite Live Region */}
      <div
        className="sr-only"
        role="status"
        aria-live="polite"
        aria-atomic="true"
      >
        {`Scene ${activeScene.number}: ${activeScene.label}`}
      </div>

      {/* Left Pinned Scene Rail (Desktop) */}
      <SceneRail />

      {/* Center Stage Workspace Slots (All mounted to preserve state, inert when inactive) */}
      <div className="relative z-10 w-full h-full flex items-center justify-center overflow-y-auto px-4 pb-20 pt-6">
        {/* Scene 00: Hero Showcase */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 0
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 0}
          inert={activeSceneIndex !== 0}
        >
          <HeroScene progress={storyProgress} />
        </div>

        {/* Scene 01: Search */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 1
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 1}
          inert={activeSceneIndex !== 1}
        >
          <SearchScene />
        </div>

        {/* Scene 02: Taste Grid */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 2
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 2}
          inert={activeSceneIndex !== 2}
        >
          <TasteScene />
        </div>

        {/* Scene 03: For You Curated Shelves */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 3
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 3}
          inert={activeSceneIndex !== 3}
        >
          <ForYouScene />
        </div>

        {/* Scene 04: Tune Faders */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 4
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 4}
          inert={activeSceneIndex !== 4}
        >
          <TuneScene />
        </div>

        {/* Scene 05: Library Tickets */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 5
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 5}
          inert={activeSceneIndex !== 5}
        >
          <LibraryScene />
        </div>

        {/* Scene 06: Closing & Credits */}
        <div
          className={`w-full transition-opacity duration-500 ${
            activeSceneIndex === 6
              ? "opacity-100 visible"
              : "opacity-0 invisible pointer-events-none absolute"
          }`}
          aria-hidden={activeSceneIndex !== 6}
          inert={activeSceneIndex !== 6}
        >
          <ClosingScene />
        </div>
      </div>

      {/* Floating Navigation Dock */}
      <Dock />
    </div>
  );
};
