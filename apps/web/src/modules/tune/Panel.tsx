"use client";
import React from "react";
import { TuneScene } from "./Scene";

export const TunePanel: React.FC<{ mode?: "stack" | "overlay" | "sheet" }> = () => {
  return (
    <div className="w-full">
      <TuneScene />
    </div>
  );
};
