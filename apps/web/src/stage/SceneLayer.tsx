"use client";
import React, { useRef, useEffect } from "react";
import gsap from "gsap";
import { useAppStore } from "../core/store";
import { MOTION_TOKENS } from "../core/motion/tokens";
import type { TransitionPhase } from "./useSceneTransition";

interface SceneLayerProps {
  index: number;
  visibleIndex: number;
  phase: TransitionPhase;
  direction: number;
  children: React.ReactNode;
}

export const SceneLayer: React.FC<SceneLayerProps> = ({
  index,
  visibleIndex,
  phase,
  direction,
  children,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollerRef = useRef<HTMLDivElement>(null);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  const isVisible = visibleIndex === index;

  useEffect(() => {
    const el = containerRef.current;
    if (!el || reducedMotion) return;

    if (isVisible) {
      if (phase === "entering") {
        gsap.fromTo(
          el,
          { opacity: 0, y: direction * 16 },
          {
            opacity: 1,
            y: 0,
            duration: MOTION_TOKENS.sceneMorph.enterDuration,
            ease: MOTION_TOKENS.sceneMorph.enterEase,
            clearProps: "transform",
          }
        );
      } else if (phase === "idle") {
        gsap.set(el, { opacity: 1, y: 0 });
      }
    } else {
      if (phase === "exiting" && visibleIndex === index) {
        gsap.to(el, {
          opacity: 0,
          y: -direction * 16,
          duration: MOTION_TOKENS.sceneMorph.exitDuration,
          ease: MOTION_TOKENS.sceneMorph.exitEase,
        });
      } else {
        gsap.set(el, { opacity: 0, y: 0 });
      }
    }
  }, [isVisible, phase, direction, index, visibleIndex, reducedMotion]);

  // Reset scroll to top on scene change
  useEffect(() => {
    if (isVisible && scrollerRef.current) {
      scrollerRef.current.scrollTop = 0;
    }
  }, [isVisible]);

  return (
    <div
      ref={containerRef}
      className={`absolute inset-0 w-full h-full ${
        isVisible ? "visible pointer-events-auto z-10" : "invisible pointer-events-none z-0"
      }`}
      aria-hidden={!isVisible}
      inert={!isVisible}
    >
      <div
        ref={scrollerRef}
        data-lenis-prevent="true"
        className="scene-scroller scroll-edge-fade w-full h-full"
      >
        <div className="scene-content-center w-full">
          {children}
        </div>
      </div>
    </div>
  );
};

