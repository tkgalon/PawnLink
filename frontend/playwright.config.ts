import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  outputDir: "tests/e2e/.results",
  fullyParallel: true,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:5173",
    reducedMotion: "no-preference",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1440, height: 900 } } },
    // iPhones run WebKit whatever browser app is used, so this is what Safari users see.
    { name: "iphone", use: { ...devices["iPhone 15"] } },
    { name: "android", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: "uv run uvicorn pawnlink.api.main:app --port 8080",
      cwd: "..",
      url: "http://127.0.0.1:8080/health",
      reuseExistingServer: true,
    },
    {
      command: "npx vite --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: true,
    },
  ],
});
