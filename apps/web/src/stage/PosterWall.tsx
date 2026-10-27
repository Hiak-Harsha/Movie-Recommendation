"use client";
import React, { useMemo } from "react";
import Image from "next/image";
import { ProceduralPoster } from "../core/motion/ProceduralPoster";
import type { MovieCard } from "@cinematch/api-client";

interface PosterWallProps {
  movies: MovieCard[];
  progress: number; // 0.0 to 1.0
  blurPx?: number;
}

export const PosterWall: React.FC<PosterWallProps> = ({
  movies,
  progress,
  blurPx = 0,
}) => {
  // Partition movies into 5 columns
  const columns = useMemo(() => {
    const cols: MovieCard[][] = [[], [], [], [], []];
    movies.forEach((m, i) => {
      cols[i % 5].push(m);
    });
    return cols;
  }, [movies]);

  // Speed multipliers per column: 0.6, 1.0, 0.8, 1.2, 0.7
  const speeds = [0.6, 1.0, 0.8, 1.2, 0.7];
  // Alternate column directions: odd columns down, even columns up
  const directions = [-1, 1, -1, 1, -1];

  return (
    <div
      aria-hidden="true"
      data-decor="true"
      className="absolute inset-0 overflow-hidden pointer-events-none select-none z-0"
      style={{
        perspective: "1200px",
        filter: blurPx > 0 ? `blur(${blurPx}px)` : "none",
        transition: "filter 0.4s ease-out",
      }}
    >
      {/* 3D Tilted Container */}
      <div
        className="w-[120%] h-[150%] -left-[10%] -top-[25%] absolute flex justify-between gap-4 will-change-transform"
        style={{
          transform: "rotateX(8deg) rotateZ(-6deg) scale(1.15)",
          transformOrigin: "center center",
        }}
      >
        {columns.map((col, colIdx) => {
          const speed = speeds[colIdx];
          const dir = directions[colIdx];
          // Parallax translateY based on scroll progress
          const offset = dir * progress * 320 * speed;

          return (
            <div
              key={colIdx}
              className="flex-1 flex flex-col gap-4 will-change-transform"
              style={{
                transform: `translateY(${offset}px)`,
                transition: "transform 0.05s linear",
              }}
            >
              {col.map((m, mIdx) => {
                const isEager = colIdx < 2 && mIdx < 3;
                const posterUrl = m.poster_path
                  ? (m.poster_path.startsWith("http")
                      ? m.poster_path
                      : `https://image.tmdb.org/t/p/w185${m.poster_path}`)
                  : null;

                return (
                  <div
                    key={m.movieId}
                    className="w-full aspect-[2/3] rounded-md overflow-hidden bg-[#121316] border border-[#26282e]/50 shadow-lg relative opacity-70"
                  >
                    {posterUrl ? (
                      <Image
                        src={posterUrl}
                        alt=""
                        fill
                        sizes="160px"
                        loading={isEager ? "eager" : "lazy"}
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
          );
        })}
      </div>

      {/* Cinematic Vignette / Scrim Gradient (Ensures foreground readability and contrast) */}
      <div
        className="absolute inset-0 bg-gradient-to-t from-[#0b0b0c] via-[#0b0b0c]/75 to-[#0b0b0c]/85"
        style={{ mixBlendMode: "multiply" }}
      />
    </div>
  );
};
