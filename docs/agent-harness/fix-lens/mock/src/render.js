/** Render local analysis into the summary strip and the two output sections. Text nodes only. */
import { orderGroups, findOrder } from './orders.js';

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

function renderSummary(root, result, order, clear) {
  root.replaceChildren();
  if (!result.ok) return;
  if (order) {
    const box = el(root, 'div', undefined, 'order-story');
    el(box, 'span', 'Order', 'order-kicker');
    el(box, 'strong', [...order.group.clOrdIds, ...order.group.orderIds].join(' · '));
    if (order.terms) el(box, 'span', order.terms, 'order-terms');
    if (order.state) el(box, 'span', order.state, 'stat ok');
    el(box, 'span', `${order.group.numbers.length} message${order.group.numbers.length === 1 ? '' : 's'}`, 'stat');
    const all = el(box, 'button', 'Show all messages', 'ghost');
    all.type = 'button';
    all.addEventListener('click', clear);
    return;
  }
  const gaps = result.timeline.filter(e => e.name === 'SequenceGap').length;
  const total = result.decoded.length + result.errors.length;
  const orders = orderGroups(result.decoded).length;
  el(root, 'span', `${total} message${total === 1 ? '' : 's'}`, 'stat');
  el(root, 'span', `${result.decoded.length} valid`, 'stat ok');
  el(root, 'span', `${result.errors.length} malformed`, result.errors.length ? 'stat bad' : 'stat');
  el(root, 'span', `${gaps} sequence gap${gaps === 1 ? '' : 's'}`, gaps ? 'stat warn' : 'stat');
  el(root, 'span', `${orders} order${orders === 1 ? '' : 's'}`, 'stat');
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
 * render(result, selectedOrderId?, handlers?)
 * With a selected order id, only that order's messages and events are shown.
 */
export function render(result, selectedOrderId = null, handlers = {}) {
  const pick = handlers.pick ?? (() => {});
  const clear = handlers.clear ?? (() => {});
  const decodeSection = document.querySelector('#decode');
  const timelineSection = document.querySelector('#timeline');
  for (const section of [decodeSection, timelineSection]) section.replaceChildren(section.querySelector('h2'));
  const summary = document.querySelector('#summary');
  if (!result.ok) {
    if (summary) summary.replaceChildren();
    el(decodeSection, 'p', result.limit.warning, 'callout bad');
    return;
  }
  const group = selectedOrderId ? findOrder(orderGroups(result.decoded), selectedOrderId) : null;
  const inView = number => !group || group.numbers.includes(number);
  if (summary) renderSummary(summary, result, group ? { group, ...describe(group, result.decoded) } : null, clear);
  renderTimeline(timelineSection, result.timeline.filter(e => inView(e.number)), pick);
  const items = [
    ...result.decoded.filter(m => inView(m.number)).map(message => ({ number: message.number, message })),
    ...(group ? [] : result.errors.map(error => ({ number: error.number, error }))),
  ].sort((a, b) => a.number - b.number);
  if (!items.length) el(decodeSection, 'p', 'No FIX messages found in the pasted text.', 'empty');
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
