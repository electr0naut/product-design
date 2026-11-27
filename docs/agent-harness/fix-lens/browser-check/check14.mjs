// Real-browser check for the v1.2 page: node check14.mjs <log> <out-prefix> <http url> <file path of index.html>
import fs from 'node:fs';
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const [log, out, url, file] = process.argv.slice(2);
const origin = new URL(url).origin;
const browser = await chromium.launch();
const result = {}, problems = [];
for (const scheme of ['light', 'dark']) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, colorScheme: scheme });
  const requests = [];
  page.on('request', r => requests.push(r.url()));
  page.on('console', m => { if (m.type() === 'error') problems.push(`${scheme}: console error: ${m.text()}`); });
  page.on('pageerror', e => problems.push(`${scheme}: page error: ${e.message}`));
  page.on('dialog', d => { problems.push(`${scheme}: dialog: ${d.message()}`); d.dismiss(); });
  await page.goto(url);
  const before = { notStarted: await page.locator('#not-started').count(), mainHidden: await page.locator('main').evaluate(e => e.hidden), button: await page.locator('#theme-button').textContent() };
  await page.fill('#paste', fs.readFileSync(log, 'utf8'));
  await page.click('#decode-button');
  await page.waitForTimeout(400);
  const r = {
    before,
    stats: await page.locator('#summary .stat').allTextContents(),
    events: await page.locator('#timeline li.event').count(),
    eventClasses: await page.locator('#timeline li.event').evaluateAll(els => [...new Set(els.map(e => e.className))]),
    cards: await page.locator('#decode article.card').count(),
    malformed: await page.locator('#decode article.card.malformed').count(),
    imgs: await page.locator('img').count(),
    bg: await page.evaluate(() => getComputedStyle(document.body).backgroundColor),
    foreign: requests.filter(u => !u.startsWith(origin)),
    hScroll: await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth),
  };
  if (before.notStarted !== 0) problems.push(`${scheme}: the not-started message is still there`);
  if (before.mainHidden) problems.push(`${scheme}: main is hidden`);
  if (r.imgs) problems.push(`${scheme}: an <img> was created`);
  if (r.foreign.length) problems.push(`${scheme}: foreign requests ${r.foreign}`);
  if (r.hScroll) problems.push(`${scheme}: horizontal scroll at 1280`);
  await page.screenshot({ path: `${out}-${scheme}.png`, fullPage: true });
  if (scheme === 'light') {
    await page.click('#theme-button');
    r.afterToggle = { html: await page.evaluate(() => document.documentElement.className), button: await page.locator('#theme-button').textContent(), bg: await page.evaluate(() => getComputedStyle(document.body).backgroundColor) };
    await page.setViewportSize({ width: 390, height: 800 });
    r.phoneHScroll = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  }
  result[scheme] = r;
  await page.close();
}
const f = await browser.newPage();
await f.goto('file://' + file);
await f.waitForTimeout(300);
result.fromDisk = { notStartedShown: await f.locator('#not-started').isVisible(), text: (await f.locator('#not-started').textContent()).trim(), mainHidden: await f.locator('main').evaluate(e => e.hidden) };
console.log(JSON.stringify({ ...result, problems }, null, 1));
await browser.close();
process.exit(problems.length ? 1 : 0);
