import { test } from "@playwright/test";

const BASELINE_VIEWPORTS = [
  { width: 1440, height: 900, name: "1440x900" },
  { width: 1280, height: 720, name: "1280x720" },
  { width: 1024, height: 768, name: "1024x768" },
  { width: 768, height: 1024, name: "768x1024" },
  { width: 390, height: 844, name: "390x844" },
];

test.describe("Baseline Screenshots", () => {
  for (const vp of BASELINE_VIEWPORTS) {
    test(`Capture baseline at ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/", { waitUntil: "networkidle" });
      await page.waitForTimeout(1000);
      await page.screenshot({
        path: `test-results/ux-before/scene-00-${vp.name}.png`,
        fullPage: false,
      });
    });
  }
});

