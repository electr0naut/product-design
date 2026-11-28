/** Render local analysis into the overview and the two output sections. Text nodes only. */
import { orderGroups, findOrder } from './orders.js';
import { tradeSummary } from './summary.js';
import { FILTERS, filterOptions, applyFilters } from './filters.js';

const el = (parent, tag, text, className) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  parent.append(node);
  return node;
};
const field = (message, tag) => message.fields.find(f => f.tag === tag) ?? null;
const value = (message, tag) => field(message, tag)?.value ?? null;
const meaning = (message, tag) => { const f = field(message, tag); return f ? (f.enumName && f.enumName !== 'unknown value' ? f.enumName : f.value) : null; };
const clock = stamp => (stamp && stamp.includes('-') ? stamp.slice(stamp.indexOf('-') + 1) : stamp);
const qty = n => (Math.round(n * 10000) / 10000).toLocaleString('en-GB', { maximumFractionDigits: 4 });
const px = n => n.toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 4 });
const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
const eventClass = event => {
  if (event.name === 'SequenceGap') return 'gap';
  if (event.name === 'SessionReject' || event.name === 'BusinessReject') return 'reject';
  return event.kind === 'order' ? 'order' : 'session';
};
const ORDER_ID_TAGS = [11, 37, 41];

/** An order id the user can click to see that order's story. A button, never a link. */
function orderId(parent, id, prefix, pick) {
  const button = el(parent, 'button', prefix ? `${prefix} ${id}` : id, 'order-link');
  button.type = 'button';
  button.addEventListener('click', () => pick(id));
  return button;
}

function renderStats(root, result, shown, events, filtered) {
  const row = el(root, 'div', undefined, 'stats');
  const gaps = events.filter(e => e.name === 'SequenceGap').length;
  const total = result.decoded.length + result.errors.length;
  el(row, 'span', filtered ? `${shown.length} of ${plural(total, 'message')}` : plural(total, 'message'), 'stat');
  if (!filtered) {
    el(row, 'span', `${result.decoded.length} valid`, 'stat ok');
    el(row, 'span', `${result.errors.length} malformed`, result.errors.length ? 'stat bad' : 'stat');
  }
  el(row, 'span', plural(gaps, 'sequence gap'), gaps ? 'stat warn' : 'stat');
  el(row, 'span', plural(orderGroups(shown).length, 'order'), 'stat');
}

function renderFilters(root, result, chosen, setFilter) {
  const options = filterOptions(result.decoded);
  const bar = el(root, 'div', undefined, 'filters');
  el(bar, 'span', 'Filter', 'filters-label');
  for (const { key, label } of FILTERS) {
    const values = options[key];
    const wrap = el(bar, 'label', undefined, 'filter');
    el(wrap, 'span', label);
    const select = el(wrap, 'select');
    el(select, 'option', 'All');
    // Option values are positions in the list, never the pasted text itself.
    values.forEach(v => el(select, 'option', v));
    select.disabled = values.length === 0;
    select.selectedIndex = chosen[key] === null || chosen[key] === undefined ? 0 : values.indexOf(chosen[key]) + 1;
    select.addEventListener('change', () => setFilter(key, select.selectedIndex === 0 ? null : values[select.selectedIndex - 1]));
  }
  if (FILTERS.some(f => chosen[f.key])) {
    const clear = el(bar, 'button', 'Clear filters', 'ghost');
    clear.type = 'button';
    clear.addEventListener('click', () => setFilter(null, null));
  }
}

function renderTrades(root, shown) {
  const rows = tradeSummary(shown);
  const box = el(root, 'div', undefined, 'trades');
  el(box, 'h2', 'Buys, sells and net by symbol');
  if (!rows.length) { el(box, 'p', 'No orders or fills in the messages shown.', 'empty'); return; }
  const table = el(box, 'table', undefined, 'trade-table');
  const head = el(el(table, 'thead'), 'tr');
  for (const [text, cls] of [['Symbol', ''], ['Buy orders', 'n'], ['Bought', 'n buy'], ['Avg buy', 'n'], ['Sell orders', 'n'], ['Sold', 'n sell'], ['Avg sell', 'n'], ['Net', 'n']]) el(head, 'th', text, cls);
  const body = el(table, 'tbody');
  for (const r of rows) {
    const net = r.buy.filledQty - r.sell.filledQty;
    const tr = el(body, 'tr');
    el(tr, 'td', r.symbol, 'symbol');
    el(tr, 'td', String(r.buy.orders), 'n');
    el(tr, 'td', qty(r.buy.filledQty), 'n buy');
    el(tr, 'td', r.buy.filledQty ? px(r.buy.notional / r.buy.filledQty) : '', 'n');
    el(tr, 'td', String(r.sell.orders), 'n');
    el(tr, 'td', qty(r.sell.filledQty), 'n sell');
    el(tr, 'td', r.sell.filledQty ? px(r.sell.notional / r.sell.filledQty) : '', 'n');
    el(tr, 'td', `${net > 0 ? '+' : ''}${qty(net)}`, net > 0 ? 'n net buy' : net < 0 ? 'n net sell' : 'n net');
  }
  el(box, 'p', 'Bought and sold are filled quantities from execution reports, counted once per ExecID. Net is bought minus sold.', 'note');
}

function renderOrderBanner(root, order, clear) {
  const box = el(root, 'div', undefined, 'order-story');
  el(box, 'span', 'Order', 'order-kicker');
  el(box, 'strong', [...order.group.clOrdIds, ...order.group.orderIds].join(' · '));
  if (order.terms) el(box, 'span', order.terms, 'order-terms');
  if (order.state) el(box, 'span', order.state, 'stat ok');
  el(box, 'span', plural(order.group.numbers.length, 'message'), 'stat');
  const all = el(box, 'button', 'Back to all messages', 'ghost');
  all.type = 'button';
  all.addEventListener('click', clear);
}

function renderTimeline(section, events, pick) {
  if (!events.length) { el(section, 'p', 'No session or order events.', 'empty'); return; }
  const list = el(section, 'ol', undefined, 'events');
  for (const event of events) {
    const row = el(list, 'li', undefined, `event ${eventClass(event)}`);
    el(row, 'span', `#${event.number}`, 'num');
    el(row, 'span', clock(event.sendingTime) ?? '', 'time');
    el(row, 'span', event.name, 'badge');
    const meta = el(row, 'span', undefined, 'meta');
    el(meta, 'span', `${event.sender ?? ''} → ${event.target ?? ''}`, 'dir');
    el(meta, 'span', event.seqNum === null || event.seqNum === undefined ? '' : `seq ${event.seqNum}`, 'seq');
    if (event.clOrdId) orderId(meta, event.clOrdId, 'ClOrdID', pick);
    if (event.orderId) orderId(meta, event.orderId, 'OrderID', pick);
    if (event.detail) el(row, 'span', event.detail, 'detail');
  }
}

function renderMessage(section, message, pick) {
  const card = el(section, 'article', undefined, message.supported ? 'card' : 'card unsupported');
  const head = el(card, 'header', undefined, 'card-head');
  el(head, 'span', `#${message.number}`, 'num');
  el(head, 'h3', message.label.replace(/^Message \d+: /, ''));
  el(head, 'span', `${value(message, 49) ?? ''} → ${value(message, 56) ?? ''}`, 'dir');
  const seq = value(message, 34);
  if (seq !== null) el(head, 'span', `seq ${seq}`, 'seq');
  const time = clock(value(message, 52));
  if (time) el(head, 'span', time, 'time');
  const table = el(card, 'table', undefined, 'fields');
  const body = el(table, 'tbody');
  for (const f of message.fields) {
    const row = el(body, 'tr', undefined, f.known === false && message.supported ? 'unknown' : '');
    el(row, 'td', String(f.tag), 'tag');
    el(row, 'td', message.supported ? f.name : '', 'name');
    const cell = el(row, 'td', undefined, 'value');
    if (ORDER_ID_TAGS.includes(f.tag) && f.value) orderId(cell, f.value, '', pick);
    else cell.textContent = f.value;
    el(row, 'td', f.enumName ?? '', f.enumName === 'unknown value' ? 'meaning unknown-value' : 'meaning');
  }
}

/** One line of terms and one of state for the order banner, from its first and last messages. */
function describe(group, decoded) {
  const messages = decoded.filter(m => group.numbers.includes(m.number));
  const first = messages.find(m => value(m, 35) === 'D') ?? messages[0];
  const last = [...messages].reverse().find(m => value(m, 35) === '8');
  const part = (m, tag) => (m ? meaning(m, tag) : null);
  const price = part(first, 44);
  const terms = [part(first, 54), part(first, 38), part(first, 55), price ? `@ ${price}` : null, part(first, 40)].filter(Boolean).join(' ');
  const filled = last ? value(last, 14) : null;
  const state = last ? [part(last, 39), filled && filled !== '0' ? `${filled} filled @ ${value(last, 6)}` : null].filter(Boolean).join(' · ') : null;
  return { terms, state };
}

/**
 * render(result, view?, handlers?)
 * view: { orderId, filters }. With an order id, only that order's messages and events are shown.
 * handlers: { pick(orderId), clear(), setFilter(key, value) }.
 */
export function render(result, view = {}, handlers = {}) {
  const pick = handlers.pick ?? (() => {});
  const clear = handlers.clear ?? (() => {});
  const setFilter = handlers.setFilter ?? (() => {});
  const chosen = view.filters ?? {};
  const decodeSection = document.querySelector('#decode');
  const timelineSection = document.querySelector('#timeline');
  for (const section of [decodeSection, timelineSection]) section.replaceChildren(section.querySelector('h2'));
  const overview = document.querySelector('#summary');
  if (overview) overview.replaceChildren();
  if (!result.ok) { el(decodeSection, 'p', result.limit.warning, 'callout bad'); return; }

  const filtered = FILTERS.some(f => chosen[f.key]);
  const passing = applyFilters(result.decoded, chosen);
  const group = view.orderId ? findOrder(orderGroups(result.decoded), view.orderId) : null;
  const shown = group ? passing.filter(m => group.numbers.includes(m.number)) : passing;
  const numbers = new Set(shown.map(m => m.number));
  const events = result.timeline.filter(e => numbers.has(e.number));

  if (overview) {
    if (group) renderOrderBanner(overview, { group, ...describe(group, result.decoded) }, clear);
    renderStats(overview, result, shown, events, filtered || Boolean(group));
    renderTrades(overview, shown);
    renderFilters(overview, result, chosen, setFilter);
  }
  renderTimeline(timelineSection, events, pick);
  const items = [
    ...shown.map(message => ({ number: message.number, message })),
    ...(group || filtered ? [] : result.errors.map(error => ({ number: error.number, error }))),
  ].sort((a, b) => a.number - b.number);
  if (!items.length) el(decodeSection, 'p', filtered || group ? 'No messages match the current filters.' : 'No FIX messages found in the pasted text.', 'empty');
  for (const item of items) {
    if (item.message) renderMessage(decodeSection, item.message, pick);
    else {
      const box = el(decodeSection, 'article', undefined, 'card malformed');
      const head = el(box, 'header', undefined, 'card-head');
      el(head, 'span', `#${item.error.number}`, 'num');
      el(head, 'h3', 'Malformed message');
      el(box, 'p', item.error.text, 'error-text');
    }
  }
}
