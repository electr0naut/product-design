// Test harness for the FIX Lens validation. It loads the product's modules from
// FIX_LENS_DIR (read-only) and offers an independent message builder for ad-hoc cases.
// Nothing here is derived from the product's code: the builder below was written from
// the FIX 4.2/4.4 specification (BodyLength, CheckSum). It is for ad-hoc probes only: every
// stored dataset and every expected result comes from the Python generator in ../generators/.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

export const PRODUCT = process.env.FIX_LENS_DIR;
if (!PRODUCT || !fs.existsSync(path.join(PRODUCT, 'src/analyse.js'))) {
  throw new Error('Set FIX_LENS_DIR to the folder that holds the FIX Lens index.html and src/');
}
const mod = name => import(pathToFileURL(path.join(PRODUCT, 'src', name)).href);
export const { analyse } = await mod('analyse.js');
export const { orderGroups, findOrder } = await mod('orders.js');
export const { tradeSummary } = await mod('summary.js');
export const { applyFilters, filterOptions } = await mod('filters.js');
export const { checkLimits } = await mod('limits.js');
export const { splitMessages, checkMessage } = await mod('framing.js');
export const { timeline } = await mod('timeline.js');

export const SOH = '\x01';
const enc = new TextEncoder();

/** Build one wire message. fields: [[tag, value], ...] WITHOUT 8, 9, 10. Returns a JS string with SOH. */
export function msg(begin, fields, opts = {}) {
  const body = fields.map(([t, v]) => `${t}=${v}${SOH}`).join('');
  const len = opts.bodyLength ?? enc.encode(body).length;
  const head = `8=${begin}${SOH}9=${len}${SOH}`;
  let sum = 0;
  for (const b of enc.encode(head + body)) sum += b;
  const cks = opts.checkSum ?? String(sum % 256).padStart(3, '0');
  return `${head}${body}10=${cks}${SOH}`;
}
export const pipe = s => s.replaceAll(SOH, '|');
export const caret = s => s.replaceAll(SOH, '^A');
export const soh5 = s => s.replaceAll(SOH, '<SOH>');

/** A tiny session helper: keeps MsgSeqNum per direction and a clock. */
export class Sess {
  constructor(begin = 'FIX.4.4', start = '20261127-09:00:00') {
    this.begin = begin; this.seq = new Map(); this.t = 0; this.start = start;
  }
  time() {
    const s = this.t++; const hh = 9 + Math.floor(s / 3600), mm = Math.floor(s / 60) % 60, ss = s % 60;
    return `${this.start.slice(0, 8)}-${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}:${String(ss).padStart(2, '0')}.000`;
  }
  m(from, to, type, fields = [], o = {}) {
    const key = `${from}>${to}`;
    const seq = o.seq ?? ((this.seq.get(key) ?? 0) + 1);
    if (!o.keepSeq) this.seq.set(key, seq);
    const head = [[35, type], [49, from], [56, to], [34, seq], [52, this.time()]];
    if (o.possDup) head.push([43, 'Y'], [122, this.time()]);
    return msg(o.begin ?? this.begin, [...head, ...fields]);
  }
}

let jsdomWindow = null;
/** Render an analysis with the product's render.js in jsdom and return the page text pieces. */
export async function renderText(result, view = { orderId: null, filters: {} }, handlers = {}) {
  if (!jsdomWindow) {
    const require = createRequire(path.join(PRODUCT, 'package.json'));
    const { JSDOM } = require('jsdom');
    // jsdom runs no script unless asked to (`runScripts`), so the page's own script tag can stay
    const html = fs.readFileSync(path.join(PRODUCT, 'index.html'), 'utf8');
    jsdomWindow = new JSDOM(html).window;
    globalThis.document = jsdomWindow.document;
  }
  const { render } = await mod('render.js');
  render(result, view, handlers);
  const d = jsdomWindow.document;
  const all = (sel, root = d) => [...root.querySelectorAll(sel)];
  return {
    stats: all('#summary .stat').map(n => n.textContent),
    trades: all('#summary .trade-table tbody tr').map(tr => all('td', tr).map(td => td.textContent)),
    notes: all('#summary .trades p').map(n => n.textContent),
    banner: all('#summary .order-story > *').map(n => n.textContent),
    warning: all('#decode .warning').map(n => n.textContent),
    events: all('#timeline li.event').map(li => ({ cls: li.className, text: all(':scope > *', li).map(n => n.textContent).filter(Boolean).join(' | ') })),
    cards: all('#decode article.card').map(a => ({ malformed: a.classList.contains('malformed'), head: all('header > *', a).map(n => n.textContent).join(' | '), error: a.querySelector('.error-text')?.textContent ?? null, rows: all('tbody tr', a).map(tr => all('td', tr).map(td => td.textContent)) })),
    filters: all('#summary label.filter').map(l => ({ label: l.querySelector('span').textContent, options: all('option', l).map(o => o.textContent), disabled: l.querySelector('select').disabled })),
  };
}

/** Summary rows as the page shows them, keyed by symbol. */
export async function shownTrades(text, view) {
  const result = analyse(text);
  const r = await renderText(result, view);
  return { result, r, bySymbol: Object.fromEntries(r.trades.map(row => [row[0], { buyOrders: row[1], bought: row[2], avgBuy: row[3], sellOrders: row[4], sold: row[5], avgSell: row[6], net: row[7] }])) };
}

export const names = result => result.timeline.map(e => `${e.number}:${e.name}${e.detail ? ` (${e.detail})` : ''}`);
