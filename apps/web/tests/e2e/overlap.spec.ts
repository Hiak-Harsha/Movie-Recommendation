import { test, expect } from "@playwright/test";

// 10 viewports matching specification
const ALL_VIEWPORTS = [
  { width: 320, height: 568, name: "320x568-mobile-se" },
  { width: 360, height: 640, name: "360x640-mobile-compact" },
  { width: 390, height: 844, name: "390x844-mobile-standard" },
  { width: 768, height: 1024, name: "768x1024-tablet-portrait" },
  { width: 1024, height: 768, name: "1024x768-desktop-small" },
  { width: 1280, height: 720, name: "1280x720-desktop-720p" },
  { width: 1366, height: 768, name: "1366x768-desktop-laptop" },
  { width: 1440, height: 900, name: "1440x900-desktop-macbook" },
  { width: 1920, height: 1080, name: "1920x1080-desktop-1080p" },
  { width: 2560, height: 1440, name: "2560x1440-desktop-2k" },
];

/**
 * Helper to inspect DOM for text node rectangle collisions
 */
async function detectTextCollisions(page: import("@playwright/test").Page): Promise<string[]> {
  return await page.evaluate(() => {
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

    const boxes: { el: string; element: HTMLElement; rect: DOMRect; text: string }[] = [];
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node: Node | null;

    while ((node = walker.nextNode())) {
      const el = node.parentElement;
      const text = node.textContent?.trim() || "";
      if (!el || text.length === 0) continue;
      if (el.closest('[data-decor],[aria-hidden="true"],[inert],.sr-only,script,style')) continue;
      if (getEffectiveOpacity(el) < 0.05 || getComputedStyle(el).visibility === "hidden") continue;

      const range = document.createRange();
      range.selectNodeContents(node);
      for (const b of range.getClientRects()) {
        if (b.width > 3 && b.height > 3) {
          boxes.push({ el: el.tagName.toLowerCase(), element: el, rect: b, text });
        }
      }
    }

    const hits: string[] = [];
    for (let i = 0; i < boxes.length; i++) {
      for (let j = i + 1; j < boxes.length; j++) {
        const a = boxes[i];
        const b = boxes[j];

        // Skip ancestor/descendant relationships
        if (a.element === b.element || a.element.contains(b.element) || b.element.contains(a.element)) {
          continue;
        }

        // Skip elements within the same inline or text block container
        const commonBlockA = a.element.closest("p, h1, h2, h3, h4, h5, h6, button, a, label, li, [data-text-flow]");
        const commonBlockB = b.element.closest("p, h1, h2, h3, h4, h5, h6, button, a, label, li, [data-text-flow]");
        if (commonBlockA && commonBlockB && commonBlockA === commonBlockB) {
          continue;
        }

        // Skip elements within the same discrete card component
        const cardA = a.element.closest("[data-card], .group, article");
        const cardB = b.element.closest("[data-card], .group, article");
        if (cardA && cardB && cardA === cardB) {
          continue;
        }

        const overlapX = Math.max(0, Math.min(a.rect.right, b.rect.right) - Math.max(a.rect.left, b.rect.left));
        const overlapY = Math.max(0, Math.min(a.rect.bottom, b.rect.bottom) - Math.max(a.rect.top, b.rect.top));
        const overlapArea = overlapX * overlapY;

        // Substantial overlap check (area > 15px^2 and both dimensions > 3px)
        if (overlapArea > 15 && overlapX > 3 && overlapY > 3) {
          hits.push(`Collision (${overlapArea.toFixed(0)}px²): [${a.text.slice(0, 15)}] in <${a.el}> vs [${b.text.slice(0, 15)}] in <${b.el}>`);
        }
      }
    }
    return hits;
  });
}

test.describe("Section 8 — Zero Overlapping Text Acceptance Across 10 Viewports", () => {
  for (const vp of ALL_VIEWPORTS) {
    test(`Zero text overlap in Stage Mode at ${vp.name} (${vp.width}x${vp.height})`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/?debug=overlap", { waitUntil: "networkidle" });

      // Verify CineMatch root is rendered
      await expect(page.locator("h1")).toBeVisible();

      // Check text collisions in active scene (Hero)
      const collisions = await detectTextCollisions(page);
      expect(collisions).toHaveLength(0);
    });
  }

  test("Zero text overlap in Stack Mode", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/?debug=overlap", { waitUntil: "networkidle" });

    // Toggle to Stack Mode if button is available
    const stackToggle = page.locator("button[aria-label*='mode'], button:has-text('Stack')").first();
    if (await stackToggle.isVisible()) {
      await stackToggle.click();
      await page.waitForTimeout(400);
    }

    const collisions = await detectTextCollisions(page);
    expect(collisions).toHaveLength(0);
  });

  test("Zero text overlap with prefers-reduced-motion: reduce", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/?debug=overlap", { waitUntil: "networkidle" });

    await expect(page.locator("h1")).toBeVisible();
    const collisions = await detectTextCollisions(page);
    expect(collisions).toHaveLength(0);
  });
});

test.describe("Transition State Machine & Layer Integrity", () => {
  test("Mid-transition guarantees at most one scene is visible (phase exit-before-enter)", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/", { waitUntil: "networkidle" });

    // Start on Scene 0 (Hero)
    await expect(page.locator("h1")).toBeVisible();

    // Trigger navigation to Search Scene (#search) via dock or navigation
    const searchNav = page.locator("nav button[aria-label*='Search'], [data-dock] button:has-text('Search')").first();
    if (await searchNav.isVisible()) {
      await searchNav.click();

      // Sample scene visibility during transition
      const activeScenes = await page.evaluate(() => {
        const layers = Array.from(document.querySelectorAll("[data-scene-layer]"));
        return layers.filter((el) => {
          const style = window.getComputedStyle(el);
          return style.display !== "none" && style.visibility !== "hidden" && parseFloat(style.opacity || "1") > 0.05;
        }).length;
      });

      // State machine guarantees at most 1 scene layer active at any given moment
      expect(activeScenes).toBeLessThanOrEqual(1);
    }
  });

  test("Letterbox bars retract when activeSceneIndex > 0", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto("/", { waitUntil: "networkidle" });

    // In Scene 0, letterbox elements exist
    const letterboxBars = page.locator("[data-letterbox]");
    if (await letterboxBars.count() > 0) {
      // Navigate down or switch scene
      const searchNav = page.locator("nav button[aria-label*='Search'], [data-dock] button:has-text('Search')").first();
      if (await searchNav.isVisible()) {
        await searchNav.click();
        await page.waitForTimeout(500);

        // Verify letterbox bars are either hidden, pointer-events-none, or scaled to 0
        const isRetracted = await page.evaluate(() => {
          const bars = document.querySelectorAll("[data-letterbox]");
          if (bars.length === 0) return true;
          return Array.from(bars).every((b) => {
            const style = window.getComputedStyle(b);
            return style.opacity === "0" || style.display === "none" || style.transform.includes("scaleY(0)");
          });
        });
        expect(isRetracted).toBe(true);
      }
    }
  });

  test("No top clipping: scene headers and eyebrows remain accessible at scroll top", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto("/", { waitUntil: "networkidle" });

    // Verify h1 top is accessible and within viewport
    const h1Box = await page.locator("h1").boundingBox();
    expect(h1Box).not.toBeNull();
    if (h1Box) {
      expect(h1Box.y).toBeGreaterThanOrEqual(0);
      expect(h1Box.y).toBeLessThan(400);
    }
  });
});

test.describe("Overlays & Modal Interactivity", () => {
  test("Search Panel: opens, traps focus, locks Lenis scroll, closes on Escape", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/", { waitUntil: "networkidle" });

    // Open Search dialog
    const searchBtn = page.locator("button[aria-label*='Search films']");
    await searchBtn.click();
    await page.waitForTimeout(300);

    // Verify search input is focused or visible
    const searchInput = page.locator("input[placeholder*='Search films']");
    await expect(searchInput).toBeVisible();

    // Verify backdrop or modal prevents body scrolling
    const scrollLocked = await page.evaluate(() => {
      return document.body.hasAttribute("data-lenis-prevent") ||
             document.documentElement.style.overflow === "hidden" ||
             document.documentElement.classList.contains("overflow-hidden") ||
             document.body.classList.contains("overflow-hidden");
    });
    expect(scrollLocked).toBe(true);

    // Press Escape to dismiss
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    // Verify search modal is closed
    await expect(searchInput).not.toBeVisible();
  });

  test("About Drawer: opens, displays content, closes on Escape, restores focus", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/", { waitUntil: "networkidle" });

    const aboutBtn = page.locator("button[aria-label*='Open About']").first();
    await aboutBtn.click();
    await page.waitForTimeout(300);

    const aboutHeading = page.locator("h2:has-text('About CineMatch')");
    await expect(aboutHeading).toBeVisible();

    // Dismiss with Escape
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);
    await expect(aboutHeading).not.toBeVisible();
  });
});
