"use client";
import { useEffect } from "react";

function getEffectiveOpacity(el: HTMLElement): number {
  let opacity = 1.0;
  let curr: HTMLElement | null = el;
  while (curr && curr !== document.body) {
    const style = window.getComputedStyle(curr);
    opacity *= parseFloat(style.opacity || "1");
    if (style.visibility === "hidden" || style.display === "none") return 0;
    curr = curr.parentElement;
  }
  return opacity;
}

function getCssPath(el: HTMLElement): string {
  if (el.id) return `#${el.id}`;
  const parts: string[] = [];
  let curr: HTMLElement | null = el;
  while (curr && curr !== document.body && parts.length < 4) {
    let part = curr.tagName.toLowerCase();
    if (curr.className && typeof curr.className === "string") {
      const firstClass = curr.className.split(" ")[0];
      if (firstClass) part += `.${firstClass}`;
    }
    parts.unshift(part);
    curr = curr.parentElement;
  }
  return parts.join(" > ");
}

interface Box {
  el: string;
  element: HTMLElement;
  rect: DOMRect;
}

export function useOverlapDebugger() {
  useEffect(() => {
    if (typeof window === "undefined") return;
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("debug") !== "overlap") return;

    console.log("[CineMatch Overlap Debugger] Active: Outlining text bounding box collisions in red");

    let overlayCanvas = document.getElementById("cinematch-overlap-canvas") as HTMLCanvasElement;
    if (!overlayCanvas) {
      overlayCanvas = document.createElement("canvas");
      overlayCanvas.id = "cinematch-overlap-canvas";
      overlayCanvas.style.position = "fixed";
      overlayCanvas.style.top = "0";
      overlayCanvas.style.left = "0";
      overlayCanvas.style.width = "100vw";
      overlayCanvas.style.height = "100vh";
      overlayCanvas.style.pointerEvents = "none";
      overlayCanvas.style.zIndex = "99999";
      document.body.appendChild(overlayCanvas);
    }

    const checkOverlaps = () => {
      const ctx = overlayCanvas.getContext("2d");
      if (!ctx) return;
      overlayCanvas.width = window.innerWidth;
      overlayCanvas.height = window.innerHeight;
      ctx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);

      const boxes: Box[] = [];
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let node: Node | null;
      while ((node = walker.nextNode())) {
        const el = node.parentElement;
        if (!el || !node.textContent?.trim()) continue;
        if (el.closest('[data-decor],[aria-hidden="true"],[inert]')) continue;
        if (getEffectiveOpacity(el) < 0.05 || getComputedStyle(el).visibility === "hidden") continue;

        const range = document.createRange();
        range.selectNodeContents(node);
        const rects = range.getClientRects();
        for (let i = 0; i < rects.length; i++) {
          const r = rects[i];
          if (r.width > 2 && r.height > 2) {
            boxes.push({ el: getCssPath(el), element: el, rect: r });
          }
        }
      }

      // Find collisions between unrelated elements intersecting by > 2 px^2
      let collisions = 0;
      for (let i = 0; i < boxes.length; i++) {
        for (let j = i + 1; j < boxes.length; j++) {
          const a = boxes[i];
          const b = boxes[j];
          if (a.element === b.element || a.element.contains(b.element) || b.element.contains(a.element)) {
            continue;
          }

          const overlapX = Math.max(0, Math.min(a.rect.right, b.rect.right) - Math.max(a.rect.left, b.rect.left));
          const overlapY = Math.max(0, Math.min(a.rect.bottom, b.rect.bottom) - Math.max(a.rect.top, b.rect.top));
          const overlapArea = overlapX * overlapY;

          if (overlapArea > 2) {
            collisions++;
            ctx.fillStyle = "rgba(239, 68, 68, 0.4)";
            ctx.strokeStyle = "#ef4444";
            ctx.lineWidth = 2;
            ctx.strokeRect(a.rect.x, a.rect.y, a.rect.width, a.rect.height);
            ctx.strokeRect(b.rect.x, b.rect.y, b.rect.width, b.rect.height);
            ctx.fillRect(
              Math.max(a.rect.left, b.rect.left),
              Math.max(a.rect.top, b.rect.top),
              overlapX,
              overlapY
            );
          }
        }
      }

      if (collisions > 0) {
        console.warn(`[Overlap Debugger] Detected ${collisions} text box collision(s) on screen`);
      }
    };

    let animationId: number;
    const loop = () => {
      checkOverlaps();
      animationId = requestAnimationFrame(loop);
    };
    loop();

    return () => {
      cancelAnimationFrame(animationId);
      if (overlayCanvas.parentNode) {
        overlayCanvas.parentNode.removeChild(overlayCanvas);
      }
    };
  }, []);
}
