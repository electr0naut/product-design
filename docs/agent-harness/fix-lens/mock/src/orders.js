/**
 * Group messages into orders. Messages belong to the same order when they share a ClOrdID (11),
 * an OrderID (37), or are chained by OrigClOrdID (41), directly or through other messages.
 * Pure: takes decoded messages, returns groups in order of first appearance.
 */
const value = (message, tag) => message.fields.find(f => f.tag === tag)?.value || null;

export function orderGroups(decoded) {
  const parent = new Map();
  const find = key => {
    let root = key;
    while (parent.get(root) !== root) root = parent.get(root);
    parent.set(key, root);
    return root;
  };
  const add = key => { if (!parent.has(key)) parent.set(key, key); return key; };
  const union = (a, b) => { parent.set(find(add(a)), find(add(b))); };
  const keysOf = message => {
    const keys = [];
    for (const tag of [11, 41]) { const v = value(message, tag); if (v) keys.push(`C:${v}`); }
    const orderId = value(message, 37);
    if (orderId) keys.push(`O:${orderId}`);
    return keys;
  };
  for (const message of decoded) {
    const keys = keysOf(message);
    keys.forEach(add);
    for (let i = 1; i < keys.length; i++) union(keys[0], keys[i]);
  }
  const groups = new Map();
  for (const message of decoded) {
    const keys = keysOf(message);
    if (!keys.length) continue;
    const root = find(keys[0]);
    if (!groups.has(root)) groups.set(root, { clOrdIds: [], orderIds: [], numbers: [] });
    const group = groups.get(root);
    group.numbers.push(message.number);
    for (const key of keys) {
      const list = key.startsWith('C:') ? group.clOrdIds : group.orderIds;
      if (!list.includes(key.slice(2))) list.push(key.slice(2));
    }
  }
  return [...groups.values()];
}

/** The group that contains this ClOrdID or OrderID, or null. */
export function findOrder(groups, id) {
  return groups.find(g => g.clOrdIds.includes(id) || g.orderIds.includes(id)) ?? null;
}
