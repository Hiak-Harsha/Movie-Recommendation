"use client";
import React, { useEffect, useRef } from "react";
import gsap from "gsap";
import { useAppStore } from "../store";

interface SplitTextProps {
  text: string;
  className?: string;
  as?: "h1" | "h2" | "h3" | "p" | "span" | "div";
  stagger?: number;
  delay?: number;
  mode?: "chars" | "words";
  play?: boolean;
}

export const SplitText: React.FC<SplitTextProps> = ({
  text,
  className = "",
  as: Component = "span",
  stagger = 0.035,
  delay = 0,
  mode = "chars",
  play = true,
}) => {
  const containerRef = useRef<HTMLElement | null>(null);
  const reducedMotion = useAppStore((s) => s.reducedMotion);

  useEffect(() => {
    if (reducedMotion || !containerRef.current || !play) return;

    const ctx = gsap.context(() => {
      const items = containerRef.current?.querySelectorAll(".split-unit");
      if (!items || !items.length) return;

      gsap.fromTo(
        items,
        { yPercent: 110, opacity: 0 },
        {
          yPercent: 0,
          opacity: 1,
          stagger,
          delay,
          duration: 0.85,
          ease: "power3.out",
          clearProps: "transform",
        }
      );
    }, containerRef);

    return () => ctx.revert();
  }, [reducedMotion, text, stagger, delay, mode, play]);

  const words = text.split(" ");

  return (
    <Component
      ref={(el: HTMLElement | null) => {
        containerRef.current = el;
      }}
      aria-label={text}
      className={`inline-block ${className}`}
    >
      {mode === "chars" ? (
        words.map((word, wIdx) => (
          <span
            key={wIdx}
            className="inline-block whitespace-nowrap overflow-hidden mr-[0.25em]"
            style={{ paddingBlock: "0.15em", marginBlock: "-0.15em" }}
            aria-hidden="true"
          >
            {word.split("").map((char, cIdx) => (
              <span
                key={cIdx}
                className="split-unit inline-block will-change-transform"
                style={{ paddingBlock: "0.1em", marginBlock: "-0.1em" }}
              >
                {char}
              </span>
            ))}
          </span>
        ))
      ) : (
        words.map((word, wIdx) => (
          <span
            key={wIdx}
            className="inline-block whitespace-nowrap overflow-hidden mr-[0.25em]"
            style={{ paddingBlock: "0.15em", marginBlock: "-0.15em" }}
            aria-hidden="true"
          >
            <span
              className="split-unit inline-block will-change-transform"
              style={{ paddingBlock: "0.1em", marginBlock: "-0.1em" }}
            >
              {word}
            </span>
          </span>
        ))
      )}
    </Component>
  );
};
