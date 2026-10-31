import { expect, test } from "@playwright/test";

const WIDTHS = [320, 360, 390, 430, 640, 641, 768, 1024, 1280, 1440, 1920];

test("no horizontal scroll at any width", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop", "widths are set by hand on one engine");
  test.setTimeout(60_000);
  for (const width of WIDTHS) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/stats/");
    await expect(page.getByText(/^Last run \d/)).toBeVisible({ timeout: 15_000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `${width}px`).toBe(width);
  }
});

test("numbers come from the stats API", async ({ page }) => {
  await page.route("**/api/stats", (route) =>
    route.fulfill({
      json: {
        months: [
          { run_date: "2026-10-30", model_version: "4", openphish_n: 300, openphish_recall: 0.68, openphish_https_recall: 0.552, legit_n: 232, legit_fpr: 0.026, api_urls: 30, drifted_columns: 21 },
          { run_date: "2026-11-01", model_version: "4", openphish_n: 280, openphish_recall: 0.611, openphish_https_recall: 0.5, legit_n: 240, legit_fpr: 0.03, api_urls: 52, drifted_columns: 18 },
        ],
        latest_by_scheme: { http: { n: 80, recall: 0.95 }, https: { n: 200, recall: 0.5 } },
        live_predictions: 90,
        batch_predictions: 1052,
        updated_at: "2026-11-01T02:05:00+00:00",
        model_version: "4",
      },
    }),
  );
  await page.goto("/stats/");
  await expect(page.getByText("Last run 1 Nov 2026")).toBeVisible();
  await expect(page.getByText("Next run 1 Dec 2026, 02:00 WIB")).toBeVisible();
  await expect(page.getByText("61.1%").first()).toBeVisible();
  await expect(page.getByText("Live HTTPS phishing, 200 URLs")).toBeVisible();
  await expect(page.getByText("52 predictions from the API")).toBeVisible();
  await expect(page.getByText("Dec, next")).toBeVisible();
});

test("the page still works when live numbers are unavailable", async ({ page }) => {
  await page.route("**/api/stats", (route) => route.fulfill({ status: 503 }));
  await page.goto("/stats/");
  await expect(page.getByText("Live numbers are unavailable right now.")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Why v4 replaced v3" })).toBeVisible();
});
