import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 2,
  forbidOnly: Boolean(process.env.CI),
  use: {
    baseURL: "http://127.0.0.1:8143",
    viewport: { width: 1440, height: 1000 },
    reducedMotion: "reduce",
    launchOptions: {
      executablePath: process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    },
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 8143 --strictPort",
    url: "http://127.0.0.1:8143",
    reuseExistingServer: false,
  },
});
