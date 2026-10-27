"use client";
import React from "react";
import { ForYouScene } from "./Scene";

export const ForYouPanel: React.FC = () => {
  return (
    <section id="for-you" className="w-full min-h-screen py-16">
      <ForYouScene />
    </section>
  );
};
