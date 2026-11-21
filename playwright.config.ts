import os from "node:os";
import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  outputDir: path.join(process.env.TMPDIR ?? os.tmpdir(), "product-design-playwright-results"),
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  use: { baseURL: "http://127.0.0.1:3197", ...devices["Desktop Chrome"] },
  webServer: {
    command: "npm run dev -- -H 127.0.0.1 -p 3197",
    url: "http://127.0.0.1:3197/",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
