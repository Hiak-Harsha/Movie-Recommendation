/**
 * CineMatch Motion Tokens & Cinematic Timing System
 * Specs defined in docs/motion-spec.md Section 1.3
 */

export const MOTION_TOKENS = {
  // Micro Interactions (Buttons, hover, toggles)
  micro: {
    duration: 0.2,
    ease: "cubic-bezier(0.16, 1, 0.3, 1)",
    gsapEase: "power2.out",
  },
  // Interface Shifts (Drawers, tab switches, panels)
  interfaceShift: {
    duration: 0.4,
    ease: "cubic-bezier(0.25, 0.1, 0.25, 1)",
    gsapEase: "power2.inOut",
  },
  // Scene Morphs (Cross-scene state machine handoffs)
  sceneMorph: {
    exitDuration: 0.24,
    enterDuration: 0.42,
    totalBudget: 0.8,
    exitEase: "power2.in",
    enterEase: "power3.out",
    staggerChildren: 0.04,
  },
  // Text Reveal (Headlines, wordmark masks)
  textReveal: {
    duration: 0.9,
    stagger: 0.035,
    ease: "expo.out",
  },
  // Lenis Smooth Scroll Config
  lenis: {
    lerp: 0.1,
    wheelMultiplier: 0.9,
  },
  // Z-Index Layers
  zIndex: {
    wall: 0,
    grain: 1,
    scene: 10,
    rail: 20,
    letterbox: 25,
    header: 30,
    dock: 30,
    toast: 40,
    modalBackdrop: 50,
    modalDialog: 60,
  },
} as const;

