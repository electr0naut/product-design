import { expect, test } from "@playwright/test";

test("review responses bind every executable script to a per-response CSP nonce", async ({ request }) => {
  const response = await request.get("/review");
  expect(response.status()).toBe(200);
  const csp = response.headers()["content-security-policy"];
  expect(csp).toBeTruthy();
  const scripts = csp.split(";").map((directive) => directive.trim()).find((directive) => directive.startsWith("script-src "));
  expect(scripts).toBeTruthy();
  expect(scripts).not.toContain("'unsafe-inline'");
  const nonce = scripts?.match(/'nonce-([^']+)'/)?.[1];
  expect(nonce, "script-src must carry a nonce").toMatch(/^[A-Za-z0-9+/_=-]{16,}$/);
  const html = await response.text();
  const scriptTags = [...html.matchAll(/<script\b[^>]*>/gi)].map(([tag]) => tag);
  expect(scriptTags.length, "page should exercise script nonce coverage").toBeGreaterThan(0);
  for (const tag of scriptTags) {
    expect(tag, `script tag must match the response nonce: ${tag}`).toContain(`nonce="${nonce}"`);
  }
  const nextResponse = await request.get("/review");
  const nextNonce = nextResponse.headers()["content-security-policy"]?.match(/script-src[^;]*'nonce-([^']+)'/)?.[1];
  expect(nextNonce, "nonce must change on each response").toBeTruthy();
  expect(nextNonce).not.toBe(nonce);
});
