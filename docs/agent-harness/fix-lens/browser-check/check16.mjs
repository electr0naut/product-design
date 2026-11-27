// Real-browser check of the trading summary and the filters (FXL-16): node check16.mjs <out prefix> <http url>
import { createRequire } from 'node:module';
const { chromium } = createRequire(import.meta.url)('playwright');
const [out, url] = process.argv.slice(2);
const origin = new URL(url).origin;
const S = '\x01';
function fixmsg(fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join('');
  const head = `8=FIX.4.4${S}9=${Buffer.byteLength(body)}${S}`;
  let sum = 0; for (const c of Buffer.from(head + body)) sum += c;
  return (head + body + `10=${String(sum % 256).padStart(3, '0')}${S}`).replaceAll(S, '|');
}
const seq = { CLIENT: 0, BROKER: 0 };
const line = text => {
  const f = text.trim().split(/\s+/).map(p => [p.slice(0, p.indexOf('=')), p.slice(p.indexOf('=') + 1)]);
  const type = f.find(([t]) => t === '35')[1];
  const [from, to] = type === 'D' ? ['CLIENT', 'BROKER'] : ['BROKER', 'CLIENT'];
  return fixmsg([[35, type], [49, from], [56, to], [34, ++seq[from]], ...f.filter(([t]) => t !== '35')]);
};
// Log A of FXL-12, then one order whose Account is markup.
const LOG = [
  '35=D 11=C1 1=ACC1 55=VOD.L 54=1 38=1000', '35=8 37=O1 11=C1 17=E1 150=F 55=VOD.L 54=1 32=400 31=71.25',
  '35=8 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5', '35=8 43=Y 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5',
  '35=8 37=O1 11=C1 17=E3 19=E1 150=G 55=VOD.L 54=1 32=300 31=71.2', '35=8 37=O1 11=C1 17=E4 19=E2 150=H 55=VOD.L 54=1 32=0 31=0',
  '35=D 11=C2 1=ACC2 55=VOD.L 54=2 38=500', '35=8 37=O2 11=C2 17=E5 150=F 55=VOD.L 54=2 32=200 31=72',
  '35=8 37=O2 11=C2 17=E6 19=E5 150=G 55=VOD.L 54=2 32=250 31=72.1', '35=8 37=O2 11=C2 17=E7 19=E6 150=G 55=VOD.L 54=2 32=260 31=72.2',
  '35=8 37=O9 11=C9 17=E8 19=ZZ 150=H 55=VOD.L 54=1 32=0', '35=8 37=O8 11=C3 17=E9 19=YY 150=G 55=BARC.L 54=5 32=50 31=2.5',
  '35=D 11=C3 1=ACC1 55=BARC.L 54=5 38=50', '35=8 37=O3 11=C4 17=E10 150=F 55=AZN.L 54=1 32=10',
  '35=8 37=O3 11=C4 17=E11 150=F 55=AZN.L 54=8 32=10 31=100', '35=8 37=O3 11=C4 17=E12 150=F 54=1 32=10 31=100',
  '35=8 37=O3 11=C4 17=E13 150=F 55=AZN.L 54=1 32=0 31=100', '35=8 37=O1 11=C1 17=E14 19=E2 150=G 55=VOD.L 54=1 32=999 31=1',
  '35=8 37=O3 11=C4 17=E15 150=0 55=AZN.L 54=1 32=5 31=100',
];
const A = LOG.map(line).join('\n');
const MARKUP = '<img/src=x/onerror=alert(1)>';
const B = A + '\n' + line(`35=D 11=C7 1=${MARKUP} 55=VOD.L 54=1 38=10`);
const browser = await chromium.launch();
const problems = [];
const expectEq = (what, got, want) => { if (JSON.stringify(got) !== JSON.stringify(want)) problems.push(`${what}: got ${JSON.stringify(got)}, want ${JSON.stringify(want)}`); };
const report = {};
for (const scheme of ['light', 'dark']) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2, colorScheme: scheme });
  const requests = [];
  page.on('request', r => requests.push(r.url()));
  page.on('console', m => { if (m.type() === 'error') problems.push(`${scheme} console error: ${m.text()}`); });
  page.on('pageerror', e => problems.push(`${scheme} page error: ${e.message}`));
  page.on('dialog', d => { problems.push(`${scheme} dialog: ${d.message()}`); d.dismiss(); });
  await page.goto(url);
  const rows = () => page.locator('#summary .trade-table tbody tr').evaluateAll(trs => trs.map(tr => [...tr.cells].map(c => c.textContent)));
  const stats = () => page.locator('#summary .stat').allTextContents();
  const cards = () => page.locator('#decode article.card').count();
  const select = n => page.locator('#summary .filters select').nth(n);
  await page.fill('#paste', A);
  await page.click('#decode-button');
  expectEq(`${scheme} order inside #summary`, await page.locator('#summary > div').evaluateAll(d => d.map(e => e.className)), ['stats', 'trades', 'filters']);
  expectEq(`${scheme} header`, await page.locator('#summary .trade-table th').allTextContents(), ['Symbol', 'Buy orders', 'Bought', 'Avg buy', 'Sell orders', 'Sold', 'Avg sell', 'Net']);
  expectEq(`${scheme} log A rows`, await rows(), [['AZN.L', '0', '10', '–', '0', '0', '–', '+10'], ['BARC.L', '0', '0', '–', '1', '50', '2.5', '-50'], ['VOD.L', '1', '300', '71.2', '1', '260', '72.2', '+40']]);
  expectEq(`${scheme} notes`, (await page.locator('#summary .trades p').allTextContents()).length, 2);
  expectEq(`${scheme} unmatched note`, await page.locator('#summary .trades p.unmatched').textContent(), '2 trade cancels or corrections refer to an execution that is not in this log.');
  expectEq(`${scheme} filter labels`, await page.locator('#summary .filters label.filter > span').allTextContents(), ['Account', 'SenderCompID', 'SenderSubID', 'TargetCompID', 'TargetSubID']);
  expectEq(`${scheme} account options`, await select(0).locator('option').allTextContents(), ['All', 'ACC1', 'ACC2']);
  expectEq(`${scheme} disabled selects`, await page.locator('#summary .filters select').evaluateAll(s => s.map(x => x.disabled)), [false, false, true, false, true]);
  expectEq(`${scheme} no clear button`, await page.locator('button.clear-filters').count(), 0);
  const all = { stats: await stats(), cards: await cards() };
  await select(0).selectOption({ label: 'ACC2' });
  expectEq(`${scheme} ACC2 rows`, await rows(), [['VOD.L', '0', '0', '–', '1', '260', '72.2', '-260']]);
  expectEq(`${scheme} ACC2 no unmatched note`, await page.locator('#summary .trades p.unmatched').count(), 0);
  expectEq(`${scheme} ACC2 selected after render`, await select(0).evaluate(s => s.options[s.selectedIndex].textContent), 'ACC2');
  const acc2 = { stats: await stats(), cards: await cards() };
  expectEq(`${scheme} ACC2 strip`, acc2.stats, ['4 of 19 messages', '0 sequence gaps', '1 order']);
  if (scheme === 'light') await page.screenshot({ path: `${out}-filtered.png`, fullPage: false });
  await select(1).selectOption({ label: 'CLIENT' });
  const both = { stats: await stats(), cards: await cards() };
  expectEq(`${scheme} ACC2 and CLIENT strip`, both.stats, ['1 of 19 messages', '0 sequence gaps', '1 order']);
  await page.locator('#timeline button.order-link', { hasText: 'ClOrdID C2' }).first().click();
  expectEq(`${scheme} order and filters together`, { banner: await page.locator('.order-story').count(), cards: await cards() }, { banner: 1, cards: 1 });
  await page.click('button.clear-filters');
  expectEq(`${scheme} filters cleared, order kept`, { banner: await page.locator('.order-story').count(), cards: await cards(), clear: await page.locator('button.clear-filters').count() }, { banner: 1, cards: 4, clear: 0 });
  await select(0).selectOption({ label: 'ACC1' });
  expectEq(`${scheme} an order outside the filter`, { cards: await cards(), empty: await page.locator('#decode p.empty').allTextContents(), trades: await page.locator('#summary .trades p.empty').allTextContents() }, { cards: 0, empty: ['No messages match the current filters.'], trades: ['No orders or fills in the messages shown.'] });
  await page.click('#decode-button');
  expectEq(`${scheme} Decode clears filters and order`, { stats: await stats(), cards: await cards(), clear: await page.locator('button.clear-filters').count(), banner: await page.locator('.order-story').count(), chosen: await page.locator('#summary .filters select').evaluateAll(s => s.map(x => x.selectedIndex)) }, { ...all, clear: 0, banner: 0, chosen: [0, 0, 0, 0, 0] });
  await page.fill('#paste', B);
  await page.click('#decode-button');
  expectEq(`${scheme} markup is an option's text`, await select(0).locator('option').allTextContents(), ['All', MARKUP, 'ACC1', 'ACC2']);
  await select(0).selectOption({ index: 1 });
  expectEq(`${scheme} markup filter works`, { cards: await cards(), stats: await stats() }, { cards: 1, stats: ['1 of 20 messages', '0 sequence gaps', '1 order'] });
  expectEq(`${scheme} no element from pasted text`, await page.locator('img, script:not([src]), iframe').count(), 0);
  expectEq(`${scheme} option value attributes`, await page.locator('#summary .filters option[value]').count(), 0);
  expectEq(`${scheme} storage`, await page.evaluate(() => [localStorage.length, sessionStorage.length, document.cookie]), [0, 0, '']);
  expectEq(`${scheme} foreign requests`, requests.filter(u => !u.startsWith(origin)), []);
  await page.click('button.clear-filters');
  await page.fill('#paste', A);
  await page.click('#decode-button');
  await page.locator('#summary').scrollIntoViewIfNeeded();
  await page.screenshot({ path: `${out}-${scheme}.png`, fullPage: false });
  report[scheme] = { all, acc2, both };
  await page.close();
}
console.log(JSON.stringify({ report, problems }, null, 1));
await browser.close();
process.exit(problems.length ? 1 : 0);
