"use client";
import React from "react";
import { TasteScene } from "./Scene";

export const TastePanel: React.FC = () => {
  return (
    <section id="taste" className="w-full min-h-screen py-16">
      <TasteScene />
    </section>
  );
};
