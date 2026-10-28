"use client";
import { useState, useEffect, useRef } from "react";
import gsap from "gsap";
import { useAppStore } from "../core/store";
import { MOTION_TOKENS } from "../core/motion/tokens";

export type TransitionPhase = "idle" | "exiting" | "entering";

export interface SceneTransitionState {
  visibleIndex: number;
  phase: TransitionPhase;
  direction: number;
}

/**
 * Deterministic Single-Visible-Scene State Machine (Section 3.1)
 * Guarantees zero text collisions during transitions.
 * Sequence: Outgoing exits -> sets hidden & inert -> Incoming enters.
 */
export function useSceneTransition(targetIndex: number): SceneTransitionState {
  const [visibleIndex, setVisibleIndex] = useState(targetIndex);
  const [phase, setPhase] = useState<TransitionPhase>("idle");
  const [direction, setDirection] = useState(1);

  const reducedMotion = useAppStore((s) => s.reducedMotion);

  const currentVisibleRef = useRef(visibleIndex);
  useEffect(() => {
    currentVisibleRef.current = visibleIndex;
  }, [visibleIndex]);

  const activeTweenRef = useRef<gsap.core.Timeline | null>(null);

  useEffect(() => {
    const fromIndex = currentVisibleRef.current;
    if (fromIndex === targetIndex) return;

    const dir = targetIndex > fromIndex ? 1 : -1;
    setDirection(dir);

    // If reduced motion is requested, swap immediately without queuing
    if (reducedMotion) {
      setVisibleIndex(targetIndex);
      setPhase("idle");
      return;
    }

    // Cancel any active handoff timeline immediately (collapses rapid jumps)
    if (activeTweenRef.current) {
      activeTweenRef.current.kill();
      activeTweenRef.current = null;
    }

    const { exitDuration, enterDuration, exitEase, enterEase } = MOTION_TOKENS.sceneMorph;

    // Build unified handoff timeline
    setPhase("exiting");
    const tl = gsap.timeline({
      onComplete: () => {
        setPhase("idle");
        activeTweenRef.current = null;
      },
    });
    activeTweenRef.current = tl;

    // Step 1: Outgoing Scene Exit (Fade + subtle lift)
    tl.to(
      {},
      {
        duration: exitDuration,
        ease: exitEase,
        onComplete: () => {
          // Commit scene index swap at the exact moment outgoing finishes
          setVisibleIndex(targetIndex);
          setPhase("entering");
        },
      }
    );

    // Step 2: Incoming Scene Enter (Fade + rise)
    tl.to(
      {},
      {
        duration: enterDuration,
        ease: enterEase,
      }
    );

    return () => {
      if (activeTweenRef.current) {
        activeTweenRef.current.kill();
        activeTweenRef.current = null;
      }
    };
  }, [targetIndex, reducedMotion]);

  return { visibleIndex, phase, direction };
}
