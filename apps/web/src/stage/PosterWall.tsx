"use client";
import React, { useMemo } from "react";
import Image from "next/image";
import { ProceduralPoster } from "../core/motion/ProceduralPoster";
import type { MovieCard } from "@cinematch/api-client";

interface PosterWallProps {
  movies: MovieCard[];
  blurPx?: number;
  activeSceneIndex?: number;
}

export const PosterWall: React.FC<PosterWallProps> = ({
  movies,
  blurPx = 0,
  activeSceneIndex = 0,
}) => {
  // Partition movies into 5 columns
  const columns = useMemo(() => {
    const cols: MovieCard[][] = [[], [], [], [], []];
    movies.forEach((m, i) => {
      cols[i % 5].push(m);
    });
    return cols;
  }, [movies]);

  // Scrim opacity: slightly brighter in Scene 0 (0.65), darker in scenes 1-6 (0.85) for AA text contrast
  const scrimOpacity = activeSceneIndex === 0 ? "rgba(11, 11, 12, 0.65)" : "rgba(11, 11, 12, 0.86)";

  return (
    <div
      aria-hidden="true"
      data-decor="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
      style={{
        perspective: "1200px",
        filter: blurPx > 0 ? `blur(${blurPx}px)` : "none",
        transition: "filter 0.6s cubic-bezier(0.25, 0.1, 0.25, 1)",
      }}
    >
      {/* 3D Tilted Perspective Poster Grid Container */}
      <div
        className="w-[120%] h-[150%] -left-[10%] -top-[25%] absolute flex justify-between gap-3 sm:gap-4 will-change-transform"
        style={{
          transform: "rotateX(8deg) rotateZ(-6deg) scale(1.15)",
          transformOrigin: "center center",
        }}
      >
        {columns.map((col, colIdx) => (
          <div
            key={colIdx}
            className={`flex-1 flex flex-col gap-3 sm:gap-4 will-change-transform ${
              colIdx >= 3 ? "hidden md:flex" : "flex"
            }`}
          >
            {col.slice(0, 8).map((m, mIdx) => {
              const isEager = colIdx < 2 && mIdx < 2;
              const posterUrl = m.poster_path
                ? (m.poster_path.startsWith("http")
                    ? m.poster_path
                    : `https://image.tmdb.org/t/p/w185${m.poster_path}`)
                : null;

              return (
                <div
                  key={m.movieId}
                  className="w-full aspect-[2/3] rounded-md overflow-hidden bg-[#121316] border border-[#26282e]/40 shadow-lg relative opacity-50"
                >
                  {posterUrl ? (
                    <Image
                      src={posterUrl}
                      alt=""
                      fill
                      sizes="160px"
                      loading={isEager ? "eager" : "lazy"}
                      decoding="async"
                      className="object-cover"
                    />
                  ) : (
                    <ProceduralPoster
                      movieId={m.movieId}
                      title={m.display_title || m.title}
                      year={m.year}
                      genres={m.genres}
                    />
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      {/* Cinematic Normal-Blend Vignette Scrim (Ensures Foreground WCAG AA Contrast) */}
      <div
        className="absolute inset-0 transition-colors duration-500 pointer-events-none"
        style={{
          backgroundColor: scrimOpacity,
          backgroundImage:
            "radial-gradient(circle at center, transparent 0%, rgba(11, 11, 12, 0.5) 70%, #0b0b0c 100%)",
        }}
      />
    </div>
  );
};
