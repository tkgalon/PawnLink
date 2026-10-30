import { expect, test } from "@playwright/test";

const WIDTHS = [320, 360, 390, 430, 640, 641, 768, 1024, 1280, 1440, 1920];

test("no horizontal scroll at any width, idle and with a result", async ({ page }, info) => {
  test.skip(info.project.name !== "desktop", "widths are set by hand on one engine");
  test.setTimeout(120_000);
  for (const width of WIDTHS) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `idle at ${width}px`).toBe(width);
    await page.getByRole("button", { name: /paypal-verify\.xyz/ }).click();
    await expect(page.getByRole("heading", { name: "Who pulled the score?" })).toBeVisible({ timeout: 10_000 });
    expect(await page.evaluate(() => document.documentElement.scrollWidth), `result at ${width}px`).toBe(width);
  }
});

test("each ticket gets the verdict the model gives it", async ({ page }) => {
  await page.goto("/");

  await page.getByRole("button", { name: /github\.com\/login/ }).click();
  await expect(page.getByText("Looks clean to me!")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Looks safe", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /mu\.qmmafe\.com/ }).click();
  await expect(page.getByText("Looks safe... I was wrong.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Known miss.")).toBeVisible();

  await page.getByRole("button", { name: /paypal-verify\.xyz/ }).click();
  await expect(page.getByText("Yikes. Do not click that.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Sketchy", { exact: true })).toBeVisible();
});

test("a typed URL is appraised on Enter", async ({ page }) => {
  await page.goto("/");
  await page.getByLabel("Link to appraise").fill("http://1.2.3.4/x.exe");
  await page.getByLabel("Link to appraise").press("Enter");
  await expect(page.getByText("Yikes. Do not click that.")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("Risky file type")).toBeVisible();
  await expect(page.getByText("1.2.3.4", { exact: true })).toBeVisible();
});

test("an unreachable model shows the closed-desk message", async ({ page }) => {
  await page.route("**/predict**", (route) => route.fulfill({ status: 503 }));
  await page.goto("/");
  await page.getByRole("button", { name: /github\.com\/login/ }).click();
  await expect(page.getByText("My appraisal desk is closed.")).toBeVisible({ timeout: 10_000 });
});

test("reduced motion skips straight to the result", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  await page.getByRole("button", { name: /paypal-verify\.xyz/ }).click();
  await expect(page.getByRole("heading", { name: "Who pulled the score?" })).toBeVisible({ timeout: 1_500 });
});

test("capture idle, miss and error states", async ({ page }, info) => {
  const shot = (name: string) =>
    page.screenshot({ path: `tests/e2e/.captures/state-${info.project.name}-${name}.png`, scale: "css" });
  await page.goto("/");
  await page.evaluate(() => document.fonts.ready);
  await shot("idle");
  await page.getByRole("button", { name: /mu\.qmmafe\.com/ }).click();
  await expect(page.getByText("Known miss.")).toBeVisible({ timeout: 10_000 });
  await page.waitForTimeout(800);
  await page.screenshot({ path: `tests/e2e/.captures/state-${info.project.name}-miss.png`, fullPage: true, scale: "css", animations: "disabled" });
});
