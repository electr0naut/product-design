/**
 * Filters over decoded messages. Each filter is a tag and one chosen value, or null for "all".
 * Account (1) is matched per order: choosing an account keeps every message of the orders that
 * carry it. The four comp and sub ids are matched on the message itself.
 */
import { orderGroups } from './orders.js';

export const FILTERS = [
  { key: 'account', tag: 1, label: 'Account' },
  { key: 'senderCompId', tag: 49, label: 'SenderCompID' },
  { key: 'senderSubId', tag: 50, label: 'SenderSubID' },
  { key: 'targetCompId', tag: 56, label: 'TargetCompID' },
  { key: 'targetSubId', tag: 57, label: 'TargetSubID' },
];
const value = (message, tag) => message.fields.find(f => f.tag === tag)?.value ?? null;

/** The distinct values present in the log for each filter, sorted. */
export function filterOptions(decoded) {
  const options = {};
  for (const { key, tag } of FILTERS) {
    options[key] = [...new Set(decoded.map(m => value(m, tag)).filter(v => v !== null && v !== ''))].sort();
  }
  return options;
}

/** The decoded messages that pass every chosen filter. */
export function applyFilters(decoded, chosen) {
  let kept = decoded;
  for (const { key, tag } of FILTERS) {
    const want = chosen[key] ?? null;
    if (want === null) continue;
    if (key === 'account') {
      const numbers = new Set();
      for (const message of decoded) if (value(message, 1) === want) numbers.add(message.number);
      for (const group of orderGroups(decoded)) {
        if (group.numbers.some(n => numbers.has(n))) group.numbers.forEach(n => numbers.add(n));
      }
      kept = kept.filter(m => numbers.has(m.number));
    } else {
      kept = kept.filter(m => value(m, tag) === want);
    }
  }
  return kept;
}
