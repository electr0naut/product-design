import { createHash } from "node:crypto";
import { readFile, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Locator, type Page } from "@playwright/test";

const product = "portal-smoke";
const gate = "design-to-backlog";
const lane = "E01";
const manifest = path.join(process.cwd(), `review/${product}.json`);
let installed = false;
test.beforeAll(async () => {
  await writeFile(manifest, await readFile(path.join(process.cwd(), "tests/fixtures/portal-smoke.json")), { flag: "wx" });
  installed = true;
});
test.afterAll(async () => {
  if (installed) await rm(manifest, { force: true });
});
const routes = [
  ["/review", /Products under review/],
  [`/review/${product}/product`, /product review queue/],
  [`/review/${product}/product/${gate}/${lane}`, /design-to-backlog \/ E01/],
] as const;

for (const [route, title] of routes) {
  test(`${route} has no serious or critical axe violations`, async ({ page }) => {
    await page.goto(route);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
    const { violations } = await new AxeBuilder({ page }).analyze();
    const severe = violations.filter((violation) => ["serious", "critical"].includes(violation.impact ?? ""));
    expect(severe, JSON.stringify(severe, null, 2)).toEqual([]);
  });
}

async function tabTo(page: Page, target: Locator) {
  for (let i = 0; i < 35; i += 1) {
    await page.keyboard.press("Tab");
    if (await target.evaluate((element) => element === document.activeElement)) return;
  }
  throw new Error("Target cannot be reached by keyboard");
}

test("keyboard-only reviewer navigates and downloads a verifiable, unrecorded packet", async ({ page }) => {
  await page.goto("/review");
  await expect(page.getByRole("heading", { name: "Products under review" })).toBeVisible();
  await tabTo(page, page.getByRole("link", { name: new RegExp(product) }));
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/review/${product}$`));
  await tabTo(page, page.getByRole("link", { name: /product Open the review queue/i }));
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/review/${product}/product$`));
  await tabTo(page, page.getByRole("link", { name: new RegExp(`${gate} / ${lane}`) }));
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(new RegExp(`/review/${product}/product/${gate}/${lane}$`));
  await tabTo(page, page.getByRole("textbox", { name: "Reviewer name" }));
  await page.keyboard.type("Keyboard Reviewer");
  await tabTo(page, page.getByRole("combobox", { name: "Decision" }));
  await page.keyboard.press("ArrowDown");
  await tabTo(page, page.getByRole("textbox", { name: "Comment" }));
  await page.keyboard.type("Clarify the source document.");
  await tabTo(page, page.getByRole("button", { name: "Build packet" }));
  await page.keyboard.press("Enter");
  const packet = JSON.parse(await page.locator("pre").last().innerText());
  expect(packet).toMatchObject({
    product, gate, lane, role: "product", reviewer: "Keyboard Reviewer", decision: "request_changes",
    feedback: [{ text: "Clarify the source document." }],
  });
  expect(packet).not.toHaveProperty("id");
  expect(packet.artifact_sha256["README.md"]).toBe(
    createHash("sha256").update(await readFile(path.join(process.cwd(), "README.md"))).digest("hex"),
  );
  await tabTo(page, page.getByRole("button", { name: "Download JSON" }));
  const downloadPromise = page.waitForEvent("download");
  await page.keyboard.press("Enter");
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe(`${product}-${gate}-${lane}-product-packet.json`);
  expect(JSON.parse(await readFile(await download.path()!, "utf8"))).toEqual(packet);
  expect(await readFile(path.join(process.cwd(), `review/${product}.json`), "utf8")).not.toContain("Keyboard Reviewer");
});
