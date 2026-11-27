// Simulated and engine-generated datasets against their ground truth, and the format-equivalence checks.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { analyse, renderText, SOH } from './harness.mjs';
import { tradesOf, statsOf, gapsOf, eventsOf, groupsOf, compareTrades } from './checks.mjs';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const read = p => fs.readFileSync(path.join(root, p), 'utf8');
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const results = [];
function record(id, feature, version, dataset, expected, actual, pass, kind = 'prd') {
  results.push({ id, feature, version, dataset, kind, status: pass ? 'PASS' : 'FAIL', expected, actual });
  console.log(`${pass ? 'PASS' : 'FAIL'} ${id} ${feature}${pass ? '' : `\n      expected: ${JSON.stringify(expected)?.slice(0, 400)}\n      actual:   ${JSON.stringify(actual)?.slice(0, 400)}`}`);
}
const brief = list => (list.length > 12 ? `${list.length} items, first: ${JSON.stringify(list.slice(0, 3))}` : list);
const firstDiff = (a, b) => { for (let i = 0; i < Math.max(a.length, b.length); i++) if (!same(a[i], b[i])) return { index: i, expected: a[i], actual: b[i] }; return null; };

for (const [name, version] of [['lifecycle-42', 'FIX.4.2'], ['lifecycle-44', 'FIX.4.4'], ['mixed-sessions', 'FIX.4.2 + FIX.4.4'], ['mix-100', 'FIX.4.2 + FIX.4.4']]) {
  const truth = JSON.parse(read(`ground-truth/${name}.json`));
  const text = read(truth.dataset);
  const result = analyse(text);
  const r = await renderText(result);
  const id = n => `DS-${name}-${n}`;
  const stats = statsOf(r);
  const wantStats = { messages: truth.messages, valid: truth.valid, malformed: truth.invalid, gaps: truth.gaps.length, orders: truth.orderCount };
  record(id('01'), 'Counts: messages, valid, malformed, sequence gaps, orders', version, truth.dataset, wantStats, stats, same(stats, wantStats));
  const ev = eventsOf(result);
  record(id('02'), 'Every timeline event, in log order', version, truth.dataset, brief(truth.events), firstDiff(truth.events, ev) ?? brief(ev), same(ev, truth.events));
  const wantGaps = truth.gaps.map(g => [g.number, g.expected, g.received]);
  record(id('03'), 'Sequence gaps: message, expected and received numbers', version, truth.dataset, wantGaps, gapsOf(result), same(gapsOf(result), wantGaps));
  const wantGroups = truth.orders.map(o => o.numbers);
  const groups = groupsOf(result);
  record(id('04'), 'Order grouping: each logical order (with its amendment chain) is one group', version, truth.dataset, brief(wantGroups), firstDiff(wantGroups, groups) ?? brief(groups), same(groups, wantGroups));
  const diffs = compareTrades(tradesOf(r), truth.trades);
  record(id('05'), 'Trading summary per symbol against decimal ground truth', version, truth.dataset, truth.trades, diffs.length ? diffs : tradesOf(r), diffs.length === 0);
  // every order (or a fixed sample of 30) selected in turn
  const sample = truth.orders.length > 45 ? truth.orders.filter((_, i) => i % Math.ceil(truth.orders.length / 30) === 0) : truth.orders;
  const bad = [];
  for (const o of sample) {
    const pick = o.clOrdIds[o.clOrdIds.length - 1];
    const rv = await renderText(result, { orderId: pick, filters: {} });
    const shown = rv.cards.map(c => +c.head.slice(1).split(' ')[0]);
    if (!same(shown, o.numbers)) bad.push({ order: pick, why: 'messages shown', expected: o.numbers, actual: shown });
    if (o.lastReport && Number(o.lastReport.cum) > 0) {
      const want = `${o.lastReport.cum} filled @ ${o.lastReport.avg}`;
      if (!rv.banner.some(b => b.includes(want))) bad.push({ order: pick, why: 'banner state', expected: want, actual: rv.banner });
    }
    const st = statsOf(rv);
    if (st.shown !== o.numbers.length || st.messages !== truth.messages || st.orders !== 1) bad.push({ order: pick, why: 'strip', actual: rv.stats });
  }
  record(id('06'), `Selecting an order (${sample.length} orders): its messages, its state, the strip`, version, truth.dataset, 'no differences', bad.slice(0, 3), bad.length === 0);
  const badViews = [];
  for (const v of truth.views) {
    const rv = await renderText(result, { orderId: null, filters: v.filters });
    const shown = rv.cards.map(c => +c.head.slice(1).split(' ')[0]);
    if (!same(shown, v.shown)) badViews.push({ filters: v.filters, why: 'messages shown', diff: firstDiff(v.shown, shown) });
    const d = compareTrades(tradesOf(rv), v.trades);
    if (d.length) badViews.push({ filters: v.filters, why: 'trading summary', diff: d.slice(0, 3) });
    const st = statsOf(rv);
    if (v.orders !== undefined && st.orders !== v.orders) badViews.push({ filters: v.filters, why: 'orders', expected: v.orders, actual: st.orders });
    if (v.gaps !== undefined && st.gaps !== v.gaps) badViews.push({ filters: v.filters, why: 'gaps', expected: v.gaps, actual: st.gaps });
    if (rv.cards.some(c => c.malformed)) badViews.push({ filters: v.filters, why: 'malformed card shown under a filter' });
  }
  record(id('07'), `Filters (${truth.views.length} Account and SenderCompID choices): messages, summary, counts`, version, truth.dataset, 'no differences', badViews.slice(0, 3), badViews.length === 0);
  const again = analyse(text);
  record(id('08'), 'Decoding the same text twice gives the same result', version, truth.dataset, 'identical', same(result, again) ? 'identical' : 'different', same(result, again));

  // ---- the same traffic in other representations (brief 9, 14)
  if (name === 'mix-100') continue;
  const norm = async t => {
    const a = analyse(t);
    const rr = await renderText(a);
    return { decoded: a.decoded.map(d => [d.number, d.label, d.fields.map(f => [f.tag, f.value, f.name, f.enumName])]), timeline: a.timeline, errors: a.errors.length, trades: rr.trades, stats: rr.stats };
  };
  const base = await norm(text);
  const lines = text.split('\n').filter(Boolean);
  const dirOf = l => (/\x0149=CLIENT/.test(l) ? 'OUT' : 'IN ');
  const variants = {
    'pipe-delimited': text.replaceAll(SOH, '|'),
    '^A text form': text.replaceAll(SOH, '^A'),
    '<SOH> text form': text.replaceAll(SOH, '<SOH>'),
    'Windows CRLF': text.replaceAll('\n', '\r\n'),
    'CR only': text.replaceAll('\n', '\r'),
    'UTF-8 BOM': '﻿' + text,
    'no trailing newline': text.replace(/\n$/, ''),
    'empty lines between messages': lines.join('\n\n\n') + '\n',
    'QuickFIX file log lines': lines.map((l, i) => `20261127-09:00:${String(i % 60).padStart(2, '0')}.000000000 : ${l}`).join('\n') + '\n',
    'QuickFIX/J log lines': lines.map(l => `<20261127-09:00:00, FIX.4.4:CLIENTA->BROKERX, incoming> (${l})`).join('\n') + '\n',
    'timestamp and direction prefix': lines.map((l, i) => `2026-11-27 09:00:00,${String(i % 1000).padStart(3, '0')} ${dirOf(l)} ${l}`).join('\n') + '\n',
    'logger prefix, pipe form': lines.map(l => `[fix-gw-3] INFO  c.e.fix.Session - msg=${l.replaceAll(SOH, '|')}`).join('\n') + '\n',
    'mixed with non-FIX log lines': lines.map((l, i) => (i % 3 === 0 ? `2026-11-27 09:00:00 WARN pool exhausted, retry=${i}\n\tat com.example.Gateway.send(Gateway.java:${i})\n` : '') + l).join('\n') + '\n',
    'all messages on one line': lines.join(''),
    'two messages per line': lines.map((l, i) => l + (i % 2 ? '\n' : '')).join(''),
    'three delimiter forms mixed by line': lines.map((l, i) => [l, l.replaceAll(SOH, '|'), l.replaceAll(SOH, '^A'), l.replaceAll(SOH, '<SOH>')][i % 4]).join('\n') + '\n',
  };
  let k = 0;
  for (const [label, t] of Object.entries(variants)) {
    k += 1;
    const got = await norm(t);
    const diff = Object.keys(base).filter(key => !same(base[key], got[key]));
    record(`EQ-${name}-${String(k).padStart(2, '0')}`, `Same result as raw SOH: ${label}`, version, `${truth.dataset} (rewritten by tests/run_datasets.mjs)`, 'identical decode, timeline, summary and counts', diff.length ? { differs: diff, stats: got.stats } : 'identical', diff.length === 0);
  }
}

// ---- engine-generated logs (QuickFIX initiator and acceptor)
for (const [v, version] of [['42', 'FIX.4.2'], ['44', 'FIX.4.4']]) {
  const p = `ground-truth/engine-quickfix-${v}.truth.json`;
  if (!fs.existsSync(path.join(root, p))) { results.push({ id: `EN-${v}`, feature: 'Engine-generated traffic', version, status: 'BLOCKED', actual: 'no engine log present' }); continue; }
  const truth = JSON.parse(read(p));
  const text = read(truth.dataset);
  const result = analyse(text);
  const r = await renderText(result);
  const stats = statsOf(r);
  const want = { messages: truth.messagesInLog, valid: truth.messagesInLog, malformed: 0, gaps: 1, orders: truth.orders.length };
  record(`EN-${v}-01`, 'QuickFIX engine log: every message accepted; one gap, made by the engine; order count', version, truth.dataset, want, stats, same(stats, want));
  const g = truth.skippedSequenceNumbers;
  const gaps = gapsOf(result).map(x => x.slice(1));
  record(`EN-${v}-02`, 'QuickFIX engine log: the skipped sequence numbers are the gap reported', version, truth.dataset, [[g.expected, g.received]], gaps, same(gaps, [[g.expected, g.received]]));
  const diffs = compareTrades(tradesOf(r), truth.trades);
  record(`EN-${v}-03`, 'QuickFIX engine log: trading summary equals what the acceptor executed', version, truth.dataset, truth.trades, diffs.length ? diffs : tradesOf(r), diffs.length === 0);
  const wantGroups = truth.orders.map(o => [...o.clOrdIds].sort());
  const got = (await import('./harness.mjs')).orderGroups(result.decoded).map(x => [...x.clOrdIds].sort());
  const key = list => JSON.stringify(list.map(x => x.join(',')).sort());
  record(`EN-${v}-04`, 'QuickFIX engine log: each order chain is one group', version, truth.dataset, brief(wantGroups), brief(got), key(got) === key(wantGroups));
}

fs.mkdirSync(path.join(root, 'reports/partial'), { recursive: true });
fs.writeFileSync(path.join(root, 'reports/partial/datasets.json'), JSON.stringify(results, null, 1));
const fails = results.filter(x => x.status === 'FAIL');
console.log(`\n${results.length} dataset checks: ${results.length - fails.length} PASS, ${fails.length} FAIL`);
