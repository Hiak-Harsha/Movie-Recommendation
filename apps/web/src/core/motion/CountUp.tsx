"use client";
import React, { useEffect, useRef, useState } from "react";
import { animate } from "motion";
import { useAppStore } from "../store";

interface CountUpProps {
  to: number;
  duration?: number;
  className?: string;
}

export const CountUp: React.FC<CountUpProps> = ({
  to,
  duration = 0.8,
  className = "font-mono tabular-nums",
}) => {
  const reducedMotion = useAppStore((s) => s.reducedMotion);
  const [current, setCurrent] = useState(to);
  const prevTo = useRef(to);

  useEffect(() => {
    if (reducedMotion) return;
    if (prevTo.current === to) return;

    const controls = animate(prevTo.current, to, {
      duration,
      ease: [0.16, 1, 0.3, 1],
      onUpdate: (latest) => setCurrent(Math.round(latest)),
    });

    prevTo.current = to;

    return () => controls.stop();
  }, [to, duration, reducedMotion]);

  return <span className={className}>{reducedMotion ? to : current}</span>;
};
