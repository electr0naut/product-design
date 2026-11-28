// Real-browser smoke check for FIX Lens. Serve the repo root over HTTP first, for example:
//   python3 -m http.server 8765 --bind 127.0.0.1
// then: node check.mjs sample.log out.png [url]
// Exits 1 if the page logs any console error, shows a dialog, creates an <img>, requests another origin,
// or decodes nothing.
import fs from 'node:fs';
import { createRequire } from 'node:module';

// Playwright is loaded with CommonJS resolution so a globally installed copy (NODE_PATH) is found too.
const { chromium } = createRequire(import.meta.url)('playwright');

const url = process.argv[4] || 'http://127.0.0.1:8765/index.html';
const origin = new URL(url).origin;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1100, height: 900 }, deviceScaleFactor: 2 });
const requests = [], problems = [];
page.on('request', r => requests.push(r.url()));
page.on('console', m => { if (m.type() === 'error') problems.push('console error: ' + m.text()); });
page.on('pageerror', e => problems.push('page error: ' + e.message));
page.on('dialog', d => { problems.push('dialog shown: ' + d.message()); d.dismiss(); });
await page.goto(url);
await page.fill('#paste', fs.readFileSync(process.argv[2], 'utf8'));
await page.click('#decode-button');
await page.waitForTimeout(500);
const out = {
  cards: await page.locator('#decode article').count(),
  timeline: await page.locator('#timeline p').allTextContents(),
  errors: await page.locator('#decode > p').allTextContents(),
  imgs: await page.locator('img').count(),
  foreignRequests: requests.filter(u => !u.startsWith(origin)),
};
if (out.cards === 0) problems.push('no message was decoded');
if (out.imgs > 0) problems.push('an <img> element was created from pasted text');
if (out.foreignRequests.length) problems.push('requests to another origin: ' + out.foreignRequests.join(', '));
console.log(JSON.stringify({ ...out, problems }, null, 1));
if (process.argv[3]) await page.screenshot({ path: process.argv[3], fullPage: true });
await browser.close();
process.exit(problems.length ? 1 : 0);
