"use client";
import React, { useEffect, useRef } from "react";
import Lenis from "lenis";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { useAppStore } from "../store";

if (typeof window !== "undefined") {
  gsap.registerPlugin(ScrollTrigger);
}

// Module-level pointer to active Lenis instance for seamless scrollToScene access
let activeLenis: Lenis | null = null;

export function getActiveLenis(): Lenis | null {
  return activeLenis;
}

/**
 * Universal Smooth Scroll to Scene Helper (Section 3.3)
 * Replaces every ad-hoc scrollIntoView across the application.
 */
export function scrollToScene(target: string | HTMLElement, immediate = false) {
  if (typeof window === "undefined") return;

  const el = typeof target === "string" ? document.querySelector(target) : target;
  if (!el) return;

  if (activeLenis && !immediate) {
    activeLenis.scrollTo(el as HTMLElement, {
      duration: 1.0,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      lock: true,
    });
  } else {
    el.scrollIntoView({ behavior: immediate ? "auto" : "smooth", block: "start" });
  }
}

export const LenisProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const lenisRef = useRef<Lenis | null>(null);
  const isAboutOpen = useAppStore((s) => s.isAboutOpen);
  const isSearchOpen = useAppStore((s) => s.isSearchOpen);
  const selectedMovieId = useAppStore((s) => s.selectedMovieId);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  useEffect(() => {
    if (reducedMotion) {
      if (activeLenis) {
        activeLenis.destroy();
        activeLenis = null;
      }
      return;
    }

    // Spec: lerp: 0.10, wheelMultiplier: 0.90, sync with GSAP ticker
    const lenis = new Lenis({
      lerp: 0.1,
      wheelMultiplier: 0.9,
      orientation: "vertical",
      gestureOrientation: "vertical",
      smoothWheel: true,
      autoRaf: false,
    });

    lenisRef.current = lenis;
    activeLenis = lenis;

    lenis.on("scroll", ScrollTrigger.update);

    const rafTicker = (time: number) => {
      lenis.raf(time * 1000);
    };

    gsap.ticker.add(rafTicker);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(rafTicker);
      // Restore GSAP default lagSmoothing on cleanup
      gsap.ticker.lagSmoothing(500, 33);
      lenis.destroy();
      lenisRef.current = null;
      activeLenis = null;
    };
  }, [reducedMotion]);

  // Pause smooth scroll and lock body when modals/drawers are open
  useEffect(() => {
    if (!lenisRef.current) return;
    if (isAboutOpen || isSearchOpen || selectedMovieId !== null) {
      lenisRef.current.stop();
      document.documentElement.style.overflow = "hidden";
      document.body.setAttribute("data-lenis-prevent", "true");
    } else {
      lenisRef.current.start();
      document.documentElement.style.overflow = "";
      document.body.removeAttribute("data-lenis-prevent");
    }
  }, [isAboutOpen, isSearchOpen, selectedMovieId]);

  return <>{children}</>;
};

export const scrollToHash = scrollToScene;
