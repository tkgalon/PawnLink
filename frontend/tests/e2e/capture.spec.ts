import { test } from "@playwright/test";

// Full-page captures of each page per device, for side-by-side review against the design.
const PAGES = [
  { name: "main", path: "/" },
  { name: "stats", path: "/stats/" },
];

for (const page of PAGES) {
  test(`capture ${page.name}`, async ({ page: browser }, info) => {
    await browser.goto(page.path);
    await browser.evaluate(() => document.fonts.ready);
    await browser.screenshot({
      path: `tests/e2e/.captures/${info.project.name}-${page.name}.png`,
      fullPage: true,
      animations: "disabled",
    });
  });
}
