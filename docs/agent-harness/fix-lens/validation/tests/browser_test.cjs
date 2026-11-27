// Real-browser checks and timings (Playwright + Chromium). The product is served read-only by python3 -m http.server.
//   FIX_LENS_DIR=<product> node tests/browser_test.cjs --perf <perf dir> [--lifted <copy with the limit raised>]
const { chromium } = require('playwright');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const root = path.dirname(__dirname);
const args = Object.fromEntries(process.argv.slice(2).reduce((acc, x, i, all) => (x.startsWith('--') ? [...acc, [x.slice(2), all[i + 1]]] : acc), []));
const PRODUCT = process.env.FIX_LENS_DIR;
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const SOH = '\x01';
const enc = new TextEncoder();
function msg(fields, begin = 'FIX.4.4') {
  const body = fields.map(([t, v]) => `${t}=${v}${SOH}`).join('');
  const head = `8=${begin}${SOH}9=${enc.encode(body).length}${SOH}`;
  let sum = 0;
  for (const b of enc.encode(head + body)) sum += b;
  return `${head}${body}10=${String(sum % 256).padStart(3, '0')}${SOH}`;
}
const tests = [];
const bench = [];
function record(id, feature, expected, actual, pass, extra = {}) {
  tests.push({ id, feature, version: extra.version ?? 'FIX.4.2 + FIX.4.4', dataset: extra.dataset ?? 'built in tests/browser_test.cjs', expected, actual, status: pass ? 'PASS' : 'FAIL' });
  console.log(`${pass ? 'PASS' : 'FAIL'} ${id} ${feature}${pass ? '' : `\n      expected: ${JSON.stringify(expected)}\n      actual:   ${JSON.stringify(actual)?.slice(0, 700)}`}`);
}
function serve(dir, port) {
  const p = spawn('python3', ['-m', 'http.server', String(port), '--bind', '127.0.0.1'], { cwd: dir, stdio: 'ignore' });
  return p;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Set the textarea, press Decode, and time it inside the page: handler time, and time to the frame after it.
async function decode(page, text) {
  await page.evaluate(t => { const a = document.querySelector('#paste'); a.value = t; }, text);
  return page.evaluate(() => new Promise(resolve => {
    const button = document.querySelector('#decode-button');
    const t0 = performance.now();
    button.click();
    const handler = performance.now() - t0;
    requestAnimationFrame(() => setTimeout(() => resolve({ handler, painted: performance.now() - t0 }), 0));
  }));
}
const act = (page, fn) => page.evaluate(`new Promise(resolve => { const t0 = performance.now(); (${fn})(); const handler = performance.now() - t0; requestAnimationFrame(() => setTimeout(() => resolve({ handler, painted: performance.now() - t0 }), 0)); })`);
const state = page => page.evaluate(() => ({
  stats: [...document.querySelectorAll('#summary .stat')].map(n => n.textContent),
  trades: [...document.querySelectorAll('#summary .trade-table tbody tr')].map(tr => [...tr.children].map(td => td.textContent)),
  cards: document.querySelectorAll('#decode article.card').length,
  malformed: document.querySelectorAll('#decode article.card.malformed').length,
  events: document.querySelectorAll('#timeline li.event').length,
  warning: document.querySelector('#decode .warning')?.textContent ?? null,
  banner: [...document.querySelectorAll('#summary .order-story > *')].map(n => n.textContent),
  summaryChildren: document.querySelector('#summary').children.length,
  nodes: document.querySelectorAll('*').length,
}));
async function metrics(page) {
  const client = await page.context().newCDPSession(page);
  await client.send('Performance.enable');
  await client.send('HeapProfiler.collectGarbage').catch(() => {});
  const { metrics: m } = await client.send('Performance.getMetrics');
  const get = n => m.find(x => x.name === n)?.value;
  await client.detach();
  return { heapMb: get('JSHeapUsedSize') / 1048576, nodes: get('Nodes') };
}

(async () => {
  const port = 8700 + Math.floor(Math.random() * 200);
  const servers = [serve(PRODUCT, port)];
  if (args.lifted) servers.push(serve(args.lifted, port + 1));
  await sleep(1200);
  const browser = await chromium.launch();
  const url = `http://127.0.0.1:${port}/index.html`;
  try {
    const context = await browser.newContext();
    await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: `http://127.0.0.1:${port}` }).catch(() => {});
    const page = await context.newPage();
    const requests = [];
    const consoleErrors = [];
    const dialogs = [];
    page.on('request', r => requests.push(r.url()));
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    page.on('pageerror', e => consoleErrors.push(String(e)));
    page.on('dialog', d => { dialogs.push(d.message()); d.dismiss(); });

    // ---- BR-01 the page starts over HTTP and only talks to its own origin
    const t0 = Date.now();
    await page.goto(url, { waitUntil: 'load' });
    await page.waitForSelector('main:not([hidden])');
    const loadMs = Date.now() - t0;
    const started = await page.evaluate(() => ({ notStarted: !!document.querySelector('#not-started'), mainHidden: document.querySelector('main').hidden, csp: document.querySelector('meta[http-equiv]')?.content }));
    const foreign = requests.filter(r => !r.startsWith(`http://127.0.0.1:${port}/`));
    record('BR-01', 'The page starts over HTTP, removes the not-started message, and requests only its own files', { notStarted: false, mainHidden: false, foreignRequests: 0, consoleErrors: 0 },
      { ...started, foreignRequests: foreign, consoleErrors, requests: requests.length }, !started.notStarted && !started.mainHidden && foreign.length === 0 && consoleErrors.length === 0
      && started.csp === "default-src 'self'; connect-src 'none'; form-action 'none'");

    // ---- BR-02 opened from disk
    const filePage = await context.newPage();
    await filePage.goto('file://' + path.join(PRODUCT, 'index.html'));
    await sleep(500);
    const disk = await filePage.evaluate(() => ({ text: document.querySelector('#not-started')?.textContent ?? null, visible: !!document.querySelector('#not-started')?.offsetParent, mainHidden: document.querySelector('main').hidden }));
    await filePage.close();
    record('BR-02', 'Opened from disk: the not-started message is shown in place of the tool (AC-024)', 'message visible, tool hidden', disk,
      disk.visible && disk.mainHidden && disk.text === 'FIX Lens did not start. Open it through a web server, not as a file from disk.');

    // ---- BR-03 a real clipboard paste of raw SOH text
    const truth44 = JSON.parse(read('ground-truth/lifecycle-44.json'));
    const text44 = read(truth44.dataset);
    let pasted = 'clipboard';
    try {
      await page.evaluate(t => navigator.clipboard.writeText(t), text44);
      await page.focus('#paste');
      await page.keyboard.press('Control+V');
    } catch (e) { pasted = 'fallback: ' + String(e).slice(0, 80); }
    let inArea = await page.evaluate(() => { const v = document.querySelector('#paste').value; return { length: v.length, soh: v.split('\x01').length - 1 }; });
    if (inArea.length === 0) { pasted = 'insertText fallback (clipboard paste not available headless)'; await page.focus('#paste'); await page.keyboard.insertText(text44); inArea = await page.evaluate(() => { const v = document.querySelector('#paste').value; return { length: v.length, soh: v.split('\x01').length - 1 }; }); }
    await page.click('#decode-button');
    let s = await state(page);
    const want44 = [`${truth44.messages} messages`, `${truth44.valid} valid`, '0 malformed', `${truth44.gaps.length} sequence gaps`, `${truth44.orderCount} orders`];
    record('BR-03', `Raw SOH text pasted into the textarea (${pasted}) keeps every SOH and decodes to the ground-truth counts`, { soh: text44.split(SOH).length - 1, stats: want44 }, { soh: inArea.soh, stats: s.stats },
      inArea.soh === text44.split(SOH).length - 1 && JSON.stringify(s.stats) === JSON.stringify(want44), { version: 'FIX.4.4', dataset: truth44.dataset });

    // ---- BR-04 CRLF text set into the textarea
    await decode(page, text44.replaceAll('\n', '\r\n'));
    s = await state(page);
    record('BR-04', 'Windows CRLF text gives the same counts', want44, s.stats, JSON.stringify(s.stats) === JSON.stringify(want44), { version: 'FIX.4.4', dataset: truth44.dataset });

    // ---- BR-05 trading summary in the real page against ground truth
    const truthMix = JSON.parse(read('ground-truth/mixed-sessions.json'));
    await decode(page, read(truthMix.dataset));
    s = await state(page);
    const keys = ['buyOrders', 'bought', 'avgBuy', 'sellOrders', 'sold', 'avgSell', 'net'];
    const diffs = [];
    for (const row of s.trades) keys.forEach((k, i) => { const w = truthMix.trades[row[0]]?.[k]; if (!(Array.isArray(w) ? w : [w]).includes(row[i + 1])) diffs.push(`${row[0]}.${k}: ${row[i + 1]} vs ${w}`); });
    record('BR-05', 'Trading summary table in the browser equals the decimal ground truth (845 messages, 5 sessions)', 'no differences', diffs.length ? diffs : `${s.trades.length} rows equal`, diffs.length === 0 && s.trades.length === Object.keys(truthMix.trades).length, { dataset: truthMix.dataset });

    // ---- BR-06 filters and order selection in the page
    const view = truthMix.views.find(v => v.filters.account);
    await page.evaluate(acct => { const sel = document.querySelectorAll('#summary label.filter select')[0]; sel.selectedIndex = [...sel.options].findIndex(o => o.textContent === acct); sel.dispatchEvent(new Event('change')); }, view.filters.account);
    s = await state(page);
    const filteredOk = s.cards === view.shown.length && s.stats[0] === `${view.shown.length} of ${truthMix.messages} messages` && s.malformed === 0;
    await page.click('button.clear-filters');
    const afterClear = await state(page);
    record('BR-06', 'Choosing an Account shows that account\'s orders only; Clear filters brings the log back', { cards: view.shown.length, strip: `${view.shown.length} of ${truthMix.messages} messages`, afterClear: truthMix.messages },
      { cards: s.cards, strip: s.stats[0], afterClear: afterClear.cards }, filteredOk && afterClear.cards === truthMix.messages, { dataset: truthMix.dataset });
    const order = truthMix.orders.find(o => o.clOrdIds.length > 2);
    await page.evaluate(id => [...document.querySelectorAll('button.order-link')].find(b => b.textContent === id).click(), order.clOrdIds[0]);
    s = await state(page);
    const picked = s.cards === order.numbers.length && order.clOrdIds.every(c => s.banner[0].includes(c));
    await page.click('button.show-all');
    const afterAll = await state(page);
    record('BR-07', 'Clicking a ClOrdID shows the whole amendment chain under a banner; Show all messages returns', { cards: order.numbers.length, ids: order.clOrdIds }, { cards: s.cards, banner: s.banner, afterShowAll: afterAll.cards },
      picked && afterAll.cards === truthMix.messages && afterAll.banner.length === 0, { dataset: truthMix.dataset });

    // ---- BR-08 an id that is one order's ClOrdID and another order's OrderID (case S07-11)
    await decode(page, read('datasets/multi-session/S07-11.log'));
    await page.evaluate(() => { const card = [...document.querySelectorAll('#decode article.card')].find(a => a.querySelector('.num').textContent === '#4'); [...card.querySelectorAll('tbody tr')].find(tr => tr.children[0].textContent === '37').querySelector('button').click(); });
    s = await state(page);
    record('BR-08', 'Clicking OrderID 1001 in message 4 opens the order that has that OrderID (ZZ9), not the order whose ClOrdID is 1001', { banner: 'ZZ9 · 1001', cards: 2 }, { banner: s.banner, cards: s.cards }, s.banner[0]?.includes('ZZ9'), { dataset: 'datasets/multi-session/S07-11.log', version: 'FIX.4.4' });

    // ---- BR-09 hostile text in every place the page shows pasted values
    const evil = ['<img src=x onerror=window.__xss=1>', '<script>window.__xss=2</script>', '"><svg onload=window.__xss=3>', "javascript:window.__xss=4", '</td></tr></table><iframe srcdoc="<script>parent.__xss=5</script>">'];
    const lines = evil.map((e, i) => msg([[35, 'D'], [49, e], [56, e], [50, e], [57, e], [34, i + 1], [52, e], [11, e + i], [1, e], [37, e], [41, e], [55, e], [54, 1], [38, 100], [40, 1], [58, e], [9000 + i, e]]));
    lines.push(msg([[35, '8'], [49, evil[0]], [56, evil[1]], [34, 9], [37, evil[0]], [11, evil[0] + '0'], [17, evil[2]], [150, 'F'], [39, 2], [55, evil[0]], [54, 1], [32, 5], [31, 2], [14, 5], [6, 2], [19, evil[3]]]));
    lines.push('8=FIX.4.4' + SOH + evil[0] + SOH);                       // malformed: the error card
    lines.push(msg([[35, evil[1]], [49, 'A'], [56, 'B'], [34, 1]], 'FIX.9.9' + evil[0]));
    await decode(page, lines.join('\n'));
    await page.evaluate(() => { for (const sel of document.querySelectorAll('#summary label.filter select')) { if (!sel.disabled) { sel.selectedIndex = 1; sel.dispatchEvent(new Event('change')); break; } } });
    await page.evaluate(() => document.querySelector('button.order-link')?.click());
    await sleep(300);
    const hostile = await page.evaluate(() => ({ xss: window.__xss ?? null, injected: document.querySelectorAll('main img, main script, main svg, main iframe, main a').length,
      attrs: [...document.querySelectorAll('main *')].flatMap(el => el.getAttributeNames().filter(n => /^on|^href$|^src$|^style$/.test(n))).length, cards: document.querySelectorAll('article.card').length }));
    record('BR-09', 'Markup and script in pasted values (ids, parties, symbol, account, text, MsgType, BeginString, a malformed message) stays text', { xss: null, injected: 0, attrs: 0, dialogs: 0, consoleErrors: 0 },
      { ...hostile, dialogs, consoleErrors }, hostile.xss === null && hostile.injected === 0 && hostile.attrs === 0 && dialogs.length === 0 && consoleErrors.length === 0 && hostile.cards > 0);

    // ---- BR-10 nothing leaves the page, nothing is stored, a reload clears the textarea
    const before = requests.length;
    await decode(page, text44);
    const stored = await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length, cookie: document.cookie }));
    const during = requests.length - before;
    await page.reload({ waitUntil: 'load' });
    const afterReload = await page.evaluate(() => ({ value: document.querySelector('#paste').value.length, cards: document.querySelectorAll('article.card').length }));
    record('BR-10', 'Decoding makes no request and stores nothing; a reload clears the text and the results (AC-020..AC-022)', { requestsDuringDecode: 0, local: 0, session: 0, cookie: '', value: 0, cards: 0 },
      { requestsDuringDecode: during, ...stored, ...afterReload }, during === 0 && stored.local === 0 && stored.session === 0 && stored.cookie === '' && afterReload.value === 0 && afterReload.cards === 0);

    // ---- BR-11 theme button
    const theme = await page.evaluate(() => { const b = document.querySelector('#theme-button'); const first = b.textContent; b.click(); const cls = document.documentElement.className; const second = b.textContent; b.click(); return { first, cls, second, back: document.documentElement.className }; });
    record('BR-11', 'The theme button switches between light and dark (AC-031)', 'class theme-dark then theme-light, label follows', theme, ['theme-dark', 'theme-light'].includes(theme.cls) && theme.first !== theme.second && theme.back !== theme.cls);

    // ---- BR-12 limits in the page (AC-016..AC-018)
    const perf = f => fs.readFileSync(path.join(args.perf, f), 'utf8');
    const limitCases = [['mix-1000.log', true], ['mix-1001.log', false], ['bytes-1048576.log', true], ['bytes-1048577.log', false], ['mix-10000.log', false]];
    for (const [file, ok] of limitCases) {
      const text = perf(file);
      const t = await decode(page, text);
      s = await state(page);
      const bytes = enc.encode(text).length;
      const refusedCleanly = s.warning !== null && s.cards === 0 && s.events === 0 && s.summaryChildren === 0 && s.warning.includes(String(bytes)) && /split/i.test(s.warning);
      record(`BR-12-${file.replace('.log', '')}`, ok ? `At the limit (${file}): decoded` : `Over the limit (${file}): refused with size and count, advice to split, no partial output`,
        ok ? 'decoded, no warning' : `warning naming ${bytes} bytes and the message count; nothing else shown`, { warning: s.warning, cards: s.cards, events: s.events, paintedMs: Math.round(t.painted) },
        ok ? s.warning === null && s.cards > 0 : refusedCleanly, { dataset: `performance/${file} (regenerated)` });
      bench.push({ suite: ok ? 'browser, at the limit' : 'browser, over the limit', dataset: file, product: 'v1.2', messages: null, handlerMs: t.handler, paintedMs: t.painted, nodes: s.nodes });
    }

    // ---- browser timings inside the limits
    async function timings(pg, file, label, product) {
      const text = perf(file);
      await pg.reload({ waitUntil: 'load' });
      await pg.waitForSelector('main:not([hidden])');
      const first = await decode(pg, text);
      const repeats = [];
      for (let i = 0; i < 5; i++) repeats.push(await decode(pg, text));
      repeats.sort((a, b) => a.painted - b.painted);
      const st = await state(pg);
      const m = await metrics(pg);
      const filter = await act(pg, `() => { const sel = [...document.querySelectorAll('#summary label.filter select')].find(x => !x.disabled); sel.selectedIndex = 1; sel.dispatchEvent(new Event('change')); }`);
      const filtered = await state(pg);
      await act(pg, `() => document.querySelector('button.clear-filters').click()`);
      const pick = await act(pg, `() => document.querySelector('#timeline button.order-link').click()`);
      const picked2 = await state(pg);
      const back = await act(pg, `() => document.querySelector('button.show-all').click()`);
      const row = { suite: label, dataset: file, product, messages: st.cards, bytes: enc.encode(text).length, firstHandlerMs: first.handler, firstPaintedMs: first.painted,
        repeatHandlerMs: repeats.map(r => r.handler), repeatPaintedMs: repeats.map(r => r.painted), medianHandlerMs: repeats[2].handler, medianPaintedMs: repeats[2].painted,
        filterHandlerMs: filter.handler, filterPaintedMs: filter.painted, filterCards: filtered.cards, orderPickHandlerMs: pick.handler, orderPickPaintedMs: pick.painted, orderCards: picked2.cards,
        showAllPaintedMs: back.painted, domElements: st.nodes, cdpNodes: m.nodes, heapMb: m.heapMb };
      bench.push(row);
      console.log(`${label} | ${file} | first ${first.painted.toFixed(0)} ms (handler ${first.handler.toFixed(0)}), repeat median ${repeats[2].painted.toFixed(0)} ms (handler ${repeats[2].handler.toFixed(0)}), filter ${filter.painted.toFixed(0)}, pick ${pick.painted.toFixed(0)}, show all ${back.painted.toFixed(0)} | ${st.nodes} elements, heap ${m.heapMb.toFixed(0)} MB`);
      return row;
    }
    bench.push({ suite: 'browser, page load', dataset: 'index.html', product: 'v1.2', loadToReadyMs: loadMs });
    const empty = await metrics(page);
    bench.push({ suite: 'browser, empty page', dataset: '-', product: 'v1.2', heapMb: empty.heapMb, cdpNodes: empty.nodes });
    const rows = [];
    for (const n of [100, 250, 500, 1000]) rows.push(await timings(page, `mix-${n}.log`, 'browser, inside the limits', 'v1.2'));
    for (const f of ['sessions-01-1000.log', 'sessions-50-1000.log', 'malformed-050pct-1000.log', 'bytes-1048576.log']) {
      const text = perf(f); await page.reload({ waitUntil: 'load' }); const first = await decode(page, text); const again = await decode(page, text); const st = await state(page);
      bench.push({ suite: 'browser, variants', dataset: f, product: 'v1.2', messages: st.cards, firstPaintedMs: first.painted, medianPaintedMs: again.painted, medianHandlerMs: again.handler, domElements: st.nodes });
      console.log(`browser, variants | ${f} | first ${first.painted.toFixed(0)} ms, again ${again.painted.toFixed(0)} ms, ${st.nodes} elements`);
    }
    const r100 = rows[0], r1000 = rows[3];
    record('BR-13', 'A 100-message log is decoded and painted in under 5 seconds (AC-006)', '< 5000 ms', `${r100.firstPaintedMs.toFixed(0)} ms first, ${r100.medianPaintedMs.toFixed(0)} ms repeated`, r100.firstPaintedMs < 5000, { dataset: 'performance/mix-100.log' });
    record('BR-14', 'At 1,000 messages a filter change and an order selection each paint in under 1 second (TR-005 measured on the page)', '< 1000 ms each', `filter ${r1000.filterPaintedMs.toFixed(0)} ms, order ${r1000.orderPickPaintedMs.toFixed(0)} ms, decode ${r1000.medianPaintedMs.toFixed(0)} ms`, r1000.filterPaintedMs < 1000 && r1000.orderPickPaintedMs < 1000, { dataset: 'performance/mix-1000.log (regenerated)' });

    // ---- hostile input in the page
    const hostileInputs = {
      'one message with a 1,000,000-character value': msg([[35, 'D'], [49, 'A'], [56, 'B'], [34, 1], [58, 'L'.repeat(1_000_000)]]),
      'one message with 100,000 fields': msg([[35, 'D'], [49, 'A'], [56, 'B'], [34, 1], ...Array.from({ length: 100_000 }, (_, i) => [5000 + (i % 900), 'v'])]),
      'pipe form, 1,000,000 literal pipes in a value': `8=FIX.4.4|9=5|35=0|58=${'|'.repeat(1_000_000)}`,
      '"8=FIX|" 170,000 times': '8=FIX|'.repeat(170_000),
      '1,000 malformed one-field candidates': Array.from({ length: 1000 }, (_, i) => `8=FIX.4.4|oops ${i}`).join('\n'),
    };
    let worst = 0;
    for (const [label, text] of Object.entries(hostileInputs)) {
      await page.reload({ waitUntil: 'load' });
      const started2 = Date.now();
      const t = await Promise.race([decode(page, text), sleep(120000).then(() => null)]);
      const st = t ? await state(page) : null;
      const wall = Date.now() - started2;
      worst = Math.max(worst, wall);
      bench.push({ suite: 'browser, hostile input', dataset: label, product: 'v1.2', bytes: enc.encode(text).length, handlerMs: t?.handler ?? null, paintedMs: t?.painted ?? null, wallMs: wall, domElements: st?.nodes ?? null, hung: !t });
      console.log(`browser, hostile | ${label} | ${t ? `${t.painted.toFixed(0)} ms painted (handler ${t.handler.toFixed(0)})` : 'NO ANSWER IN 120 s'} | ${st?.nodes} elements`);
    }
    record('BR-15', 'Hostile input inside the size limit: the page answers each of five inputs without hanging', 'every input answered; times in benchmark-results.csv', `slowest ${worst} ms wall clock`, bench.filter(b => b.suite === 'browser, hostile input').every(b => !b.hung));

    // ---- information for the planned limit of 10,000 messages (a copy with the limit lifted)
    if (args.lifted) {
      const lp = await context.newPage();
      await lp.goto(`http://127.0.0.1:${port + 1}/index.html`, { waitUntil: 'load' });
      for (const n of [1000, 2500, 5000, 10000]) await timings(lp, `mix-${n}.log`, 'browser, limit lifted to 10,000 (information)', 'copy, limit lifted');
      await lp.close();
    }
  } finally {
    await browser.close();
    servers.forEach(p => p.kill());
  }
  fs.mkdirSync(path.join(root, 'reports/partial'), { recursive: true });
  fs.writeFileSync(path.join(root, 'reports/partial/browser.json'), JSON.stringify({ chromium: require('playwright/package.json').version, tests, bench }, null, 1));
  console.log(`\n${tests.length} browser checks: ${tests.filter(t => t.status === 'PASS').length} PASS, ${tests.filter(t => t.status === 'FAIL').length} FAIL`);
})().catch(e => { console.error(e); process.exit(1); });
