"use client";
import React from "react";
import { LibraryScene } from "./Scene";

export const LibraryPanel: React.FC<{ mode?: "stack" | "overlay" | "sheet" }> = () => {
  return (
    <div className="w-full">
      <LibraryScene />
    </div>
  );
};
