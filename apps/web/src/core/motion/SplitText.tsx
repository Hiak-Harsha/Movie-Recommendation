"use client";
import React, { useEffect, useRef, useState } from "react";
import gsap from "gsap";
import { useAppStore } from "../store";

interface SplitTextProps {
  text: string;
  className?: string;
  as?: "h1" | "h2" | "h3" | "p" | "span" | "div";
  stagger?: number;
  delay?: number;
}

export const SplitText: React.FC<SplitTextProps> = ({
  text,
  className = "",
  as: Component = "span",
  stagger = 0.035,
  delay = 0,
}) => {
  const containerRef = useRef<HTMLElement>(null);
  const [isClient, setIsClient] = useState(false);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  useEffect(() => {
    setIsClient(true);
  }, []);

  useEffect(() => {
    if (!isClient || reducedMotion || !containerRef.current) return;

    const chars = containerRef.current.querySelectorAll(".split-char");
    if (!chars.length) return;

    gsap.fromTo(
      chars,
      { yPercent: 110, opacity: 0 },
      {
        yPercent: 0,
        opacity: 1,
        stagger,
        delay,
        duration: 0.85,
        ease: "power3.out",
      }
    );
  }, [isClient, reducedMotion, text, stagger, delay]);

  // Server render / Reduced motion fallback: plain text inside semantic element
  if (!isClient || reducedMotion) {
    return <Component className={className}>{text}</Component>;
  }

  const words = text.split(" ");

  return (
    <Component
      ref={containerRef as any}
      aria-label={text}
      className={`inline-block ${className}`}
    >
      {words.map((word, wIdx) => (
        <span key={wIdx} className="inline-block whitespace-nowrap overflow-hidden mr-[0.25em]">
          {word.split("").map((char, cIdx) => (
            <span
              key={cIdx}
              aria-hidden="true"
              className="split-char inline-block will-change-transform"
            >
              {char}
            </span>
          ))}
        </span>
      ))}
    </Component>
  );
};
