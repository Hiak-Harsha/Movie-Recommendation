"use client";
import { useEffect } from "react";
import { useAppStore } from "../core/store";

export function useModeSwitch() {
  const setIsStageMode = useAppStore((s) => s.setIsStageMode);
  const setReducedMotion = useAppStore((s) => s.setReducedMotion);

  useEffect(() => {
    // Check initial media query for reduced motion
    const motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReducedMotion(motionQuery.matches);

    const handleMotionChange = (e: MediaQueryListEvent) => {
      setReducedMotion(e.matches);
    };
    motionQuery.addEventListener("change", handleMotionChange);

    // Responsive mode checker
    const checkMode = () => {
      const isDesktopSize = window.innerWidth >= 1024 && window.innerHeight >= 640;
      const isMotionReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      setIsStageMode(isDesktopSize && !isMotionReduced);
    };

    checkMode();
    window.addEventListener("resize", checkMode);

    return () => {
      motionQuery.removeEventListener("change", handleMotionChange);
      window.removeEventListener("resize", checkMode);
    };
  }, [setIsStageMode, setReducedMotion]);
}
