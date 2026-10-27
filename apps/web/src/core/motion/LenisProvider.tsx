"use client";
import React, { useEffect, useRef } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useAppStore } from "../store";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

export const LenisProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const lenisRef = useRef<Lenis | null>(null);
  const isAboutOpen = useAppStore((s) => s.isAboutOpen);
  const isSearchOpen = useAppStore((s) => s.isSearchOpen);
  const selectedMovieId = useAppStore((s) => s.selectedMovieId);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  useEffect(() => {
    if (reducedMotion) return;

    const lenis = new Lenis({
      duration: 1.1,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
    });

    lenisRef.current = lenis;

    lenis.on("scroll", ScrollTrigger.update);

    const rafTicker = (time: number) => {
      lenis.raf(time * 1000);
    };

    gsap.ticker.add(rafTicker);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(rafTicker);
      lenis.destroy();
      lenisRef.current = null;
    };
  }, [reducedMotion]);

  // Pause smooth scroll when modals/drawers are open to prevent background scrolling
  useEffect(() => {
    if (!lenisRef.current) return;
    if (isAboutOpen || isSearchOpen || selectedMovieId !== null) {
      lenisRef.current.stop();
    } else {
      lenisRef.current.start();
    }
  }, [isAboutOpen, isSearchOpen, selectedMovieId]);

  return <>{children}</>;
};

export function scrollToHash(hash: string) {
  if (typeof window === "undefined") return;
  const target = document.querySelector(hash);
  if (target) {
    target.scrollIntoView({ behavior: "smooth" });
  }
}
