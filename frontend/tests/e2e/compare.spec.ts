import { expect, test } from "@playwright/test";

// Puts the main page in the same state as the design reference (the paypal ticket, fully
// appraised) and captures it at CSS pixel scale so it lines up with the reference image.
test("main page after appraising the paypal ticket", async ({ page }, info) => {
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await page.getByRole("button", { name: /paypal-verify\.xyz/ }).click();
  await expect(page.getByRole("heading", { name: "Who pulled the score?" })).toBeVisible({ timeout: 10_000 });
  await page.waitForTimeout(1200);
  await page.screenshot({
    path: `tests/e2e/.captures/compare-${info.project.name}-main.png`,
    fullPage: true,
    animations: "disabled",
    scale: "css",
  });
});
