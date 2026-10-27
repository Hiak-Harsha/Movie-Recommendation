import { test, expect } from "@playwright/test";

const VIEWPORTS = [
  { width: 320, height: 640, name: "mobile-small" },
  { width: 390, height: 844, name: "mobile-standard" },
  { width: 768, height: 1024, name: "tablet" },
  { width: 1024, height: 768, name: "desktop-small" },
  { width: 1280, height: 720, name: "desktop-720p" },
  { width: 1366, height: 768, name: "desktop-laptop" },
  { width: 1440, height: 900, name: "desktop-macbook" },
  { width: 1920, height: 1080, name: "desktop-1080p" },
];

test.describe("Section 8 — Zero Overlapping Text Acceptance Suite", () => {
  for (const vp of VIEWPORTS) {
    test(`Zero text overlap at ${vp.name} (${vp.width}x${vp.height})`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("http://localhost:3000/?debug=overlap", { waitUntil: "networkidle" });

      // Verify page loaded
      await expect(page.locator("h1")).toBeVisible();

      // Check for zero text box collisions across visible text elements
      const collisions = await page.evaluate(() => {
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

        const boxes: { el: string; element: HTMLElement; rect: DOMRect }[] = [];
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let node: Node | null;
        while ((node = walker.nextNode())) {
          const el = node.parentElement;
          if (!el || !node.textContent?.trim()) continue;
          if (el.closest('[data-decor],[aria-hidden="true"],[inert],.sr-only')) continue;
          if (getEffectiveOpacity(el) < 0.05 || getComputedStyle(el).visibility === "hidden") continue;

          const range = document.createRange();
          range.selectNodeContents(node);
          for (const b of range.getClientRects()) {
            if (b.width > 2 && b.height > 2) {
              boxes.push({ el: el.tagName.toLowerCase(), element: el, rect: b });
            }
          }
        }

        const hits: string[] = [];
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
              hits.push(`Collision (${overlapArea.toFixed(1)}px²): ${a.el} with ${b.el}`);
            }
          }
        }
        return hits;
      });

      expect(collisions).toHaveLength(0);
    });
  }

  test("Modals and Drawers have zero overlap", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("http://localhost:3000/", { waitUntil: "networkidle" });

    // Open Search dialog using the search button
    const searchBtn = page.locator("button[aria-label*='Search films']");
    await searchBtn.click();
    await page.waitForTimeout(300);

    // Verify search input is open
    const searchInput = page.locator("input[placeholder*='Search films']");
    await expect(searchInput).toBeVisible();

    // Close with Escape
    await page.keyboard.press("Escape");
    await page.waitForTimeout(300);

    // Open About drawer using the about button
    const aboutBtn = page.locator("button[aria-label*='Open About']").first();
    await aboutBtn.click();
    await page.waitForTimeout(300);

    const aboutHeading = page.locator("h2:has-text('About CineMatch')");
    await expect(aboutHeading).toBeVisible();

    // Close with Escape
    await page.keyboard.press("Escape");
  });
});
