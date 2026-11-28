// Evaluates one expectation block (the vocabulary of ground-truth/cases.json) against the tool.
import { analyse, renderText, orderGroups, tradeSummary } from './harness.mjs';

const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const oneOf = (actual, wanted) => (Array.isArray(wanted) ? wanted : [wanted]).includes(actual);
const TRADE_KEYS = ['buyOrders', 'bought', 'avgBuy', 'sellOrders', 'sold', 'avgSell', 'net'];

export function tradesOf(r) {
  return Object.fromEntries(r.trades.map(row => [row[0], Object.fromEntries(TRADE_KEYS.map((k, i) => [k, row[i + 1]]))]));
}
export function statsOf(r) {
  const out = {};
  for (const s of r.stats) {
    let m;
    if ((m = /^(\d+) messages?$/.exec(s))) out.messages = +m[1];
    else if ((m = /^(\d+) valid$/.exec(s))) out.valid = +m[1];
    else if ((m = /^(\d+) malformed$/.exec(s))) out.malformed = +m[1];
    else if ((m = /^(\d+) sequence gaps?$/.exec(s))) out.gaps = +m[1];
    else if ((m = /^(\d+) orders?$/.exec(s))) out.orders = +m[1];
    else if ((m = /^(\d+) of (\d+) messages$/.exec(s))) { out.shown = +m[1]; out.messages = +m[2]; }
  }
  return out;
}
export const gapsOf = result => result.timeline.filter(e => e.name === 'SequenceGap').map(e => {
  const m = /expected (\d+), received (\d+)/.exec(e.detail);
  return [e.number, +m[1], +m[2]];
});
export const eventsOf = result => result.timeline.map(e => `${e.number}:${e.name}`);
export const groupsOf = result => orderGroups(result.decoded).map(g => g.numbers);
export function compareTrades(actual, wanted) {
  const diffs = [];
  for (const sym of new Set([...Object.keys(actual), ...Object.keys(wanted)])) {
    if (!actual[sym]) { diffs.push(`${sym}: no row`); continue; }
    if (!wanted[sym]) { diffs.push(`${sym}: unexpected row ${JSON.stringify(actual[sym])}`); continue; }
    for (const k of TRADE_KEYS) {
      if (wanted[sym][k] !== undefined && !oneOf(actual[sym][k], wanted[sym][k])) {
        diffs.push(`${sym}.${k}: shown ${actual[sym][k]}, expected ${[].concat(wanted[sym][k]).join(' or ')}`);
      }
    }
  }
  return diffs;
}

/** Returns a list of { check, pass, expected, actual }. */
export async function evaluate(text, expect, view) {
  const out = [];
  const add = (check, pass, expected, actual) => out.push({ check, pass: Boolean(pass), expected, actual });
  let result;
  try {
    result = analyse(text);
  } catch (error) {
    add('no exception', false, 'analyse() returns', String(error));
    return out;
  }
  const v = view ?? { orderId: null, filters: {} };
  const r = await renderText(result, v);
  const stats = statsOf(r);
  const cardNumbers = r.cards.filter(c => !c.malformed).map(c => +c.head.slice(1).split(' ')[0]);
  const card = n => r.cards.find(c => c.head.startsWith(`#${n} `) && !c.malformed);
  for (const [key, want] of Object.entries(expect)) {
    if (key === 'stats') {
      const got = Object.fromEntries(Object.keys(want).map(k => [k, stats[k]]));
      add('summary strip', same(got, want), want, got);
    } else if (key === 'stats_text') add('summary strip text', same(r.stats, want), want, r.stats);
    else if (key === 'events') add('timeline events', same(eventsOf(result).filter(e => !e.endsWith(':SequenceGap') || want.some(w => w.endsWith(':SequenceGap'))), want), want, eventsOf(result));
    else if (key === 'events_include') add('timeline includes', want.every(w => eventsOf(result).includes(w)), want, eventsOf(result));
    else if (key === 'gaps') add('sequence gaps', same(gapsOf(result), want), want, gapsOf(result));
    else if (key === 'gaps_include') add('sequence gaps include', want.every(w => gapsOf(result).some(g => same(g, w))), want, gapsOf(result));
    else if (key === 'flagged') {
      for (const n of want) {
        const own = result.timeline.filter(e => e.number === n);
        add(`message ${n} is flagged`, own.some(e => e.detail) || own.length > 1, 'an event or a note that marks the anomaly', own.map(e => e.name));
      }
    } else if (key === 'classes') {
      for (const [n, cls] of Object.entries(want)) {
        const li = r.events.find(e => e.text.startsWith(`#${n} `));
        add(`timeline row ${n} class`, li?.cls.split(' ').includes(cls), cls, li?.cls);
      }
    } else if (key === 'trades') {
      const diffs = compareTrades(tradesOf(r), want);
      add('trading summary', diffs.length === 0, want, diffs.length ? diffs : tradesOf(r));
    } else if (key === 'trades_fields') {
      const diffs = compareTrades(Object.fromEntries(Object.entries(tradesOf(r)).filter(([s]) => s in want)), want);
      add('trading summary figures', diffs.length === 0, want, diffs.length ? diffs : 'as expected');
    } else if (key === 'unmatched') {
      const got = tradeSummary(result.decoded, undefined).unmatched;
      add('unmatched cancels/corrections', got === want, want, got);
    } else if (key === 'notes_include') add('notes', want.every(w => r.notes.includes(w)), want, r.notes);
    else if (key === 'groups') add('order groups', same(groupsOf(result), want), want, groupsOf(result));
    else if (key === 'shown') add('messages shown', same(cardNumbers, want), want, cardNumbers);
    else if (key === 'banner') add('order banner', want.every(w => r.banner.some(b => b.includes(w))), want, r.banner);
    else if (key === 'filter_options') {
      const got = Object.fromEntries(r.filters.map(f => [f.label, f.options]));
      add('filter options', same(got, want), want, got);
    } else if (key === 'labels') {
      for (const [n, label] of Object.entries(want)) add(`card ${n} label`, card(n)?.head.split(' | ')[1] === label, label, card(n)?.head);
    } else if (key === 'labels_any') {
      for (const [n, labels] of Object.entries(want)) add(`card ${n} label`, labels.some(l => card(n)?.head.split(' | ')[1].includes(l)), labels, card(n)?.head);
    } else if (key === 'rows') {
      for (const w of want) {
        const rows = (card(w.number)?.rows ?? []).filter(row => row[0] === w.tag);
        const hit = rows.find(row => (w.field === undefined || row[1] === w.field) && (w.value === undefined || row[2] === w.value)
          && (w.meaning === undefined || row[3] === w.meaning) && (w.meaning_not === undefined || row[3] !== w.meaning_not));
        add(`card ${w.number} row for tag ${w.tag}`, hit, w, rows);
      }
    } else if (key === 'tag_sequence') {
      for (const [n, tags] of Object.entries(want)) add(`card ${n} tag order`, same(card(n)?.rows.map(row => +row[0]), tags), tags, card(n)?.rows.map(row => +row[0]));
    } else if (key === 'empty_text') add('empty-state text', r.cards.length === 0 && (await pageHas(want)), want, r.cards.length);
    else if (key === 'errors') {
      const got = result.errors.map(e => ({ number: e.number, rule: e.rule, position: e.position, text: e.text }));
      const ok = got.length === want.length && want.every((w, i) => got[i].number === w.number && got[i].rule === w.rule
        && (w.position === undefined || oneOf(got[i].position, w.position)) && (w.text === undefined || got[i].text === w.text)
        && new RegExp(`^Message ${w.number}: .+ at position \\d+$`, 's').test(got[i].text));
      add('errors (number, rule, position, text)', ok, want, got);
      const errorCards = r.cards.filter(c => c.malformed).map(c => c.error);
      if (!(v.orderId || Object.keys(v.filters ?? {}).length)) add('error cards on the page', same(errorCards, got.map(g => g.text)), got.map(g => g.text), errorCards);
    } else if (key === 'error_numbers') add('malformed message numbers', same(result.errors.map(e => e.number), want), want, result.errors.map(e => e.number));
    else if (key === 'valid_numbers') add('valid message numbers', same(result.decoded.map(d => d.number), want), want, result.decoded.map(d => d.number));
    else if (key === 'click') {
      const got = await clickId(result, want.card, want.tag);
      add(`click tag ${want.tag} in card ${want.card}: messages shown`, same(got.shown, want.shown), want.shown, got.shown);
      add(`click tag ${want.tag} in card ${want.card}: banner`, want.banner.every(w => got.banner[0]?.includes(w)), want.banner, got.banner);
    } else add(`unknown check ${key}`, false, null, null);
  }
  return out;
}

async function pageHas(text) {
  return globalThis.document.querySelector('#decode').textContent.includes(text);
}

/** Press the order-id button of `tag` in message card `number`, as a user would, and report what is shown. */
async function clickId(result, number, tag) {
  const view = { orderId: null, filters: {} };
  const handlers = { pick(id) { view.orderId = id; }, clear() { view.orderId = null; }, setFilter() {} };
  await renderText(result, view, handlers);
  const d = globalThis.document;
  const cardEl = [...d.querySelectorAll('#decode article.card')].find(a => a.querySelector('.num')?.textContent === `#${number}`);
  const rowEl = [...cardEl.querySelectorAll('tbody tr')].find(tr => tr.children[0].textContent === tag);
  rowEl.querySelector('button.order-link').click();
  const r = await renderText(result, view, handlers);
  return { shown: r.cards.map(c => +c.head.slice(1).split(' ')[0]), banner: r.banner };
}
