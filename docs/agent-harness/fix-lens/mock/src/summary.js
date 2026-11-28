/**
 * Buys and sells per symbol, from the decoded messages given (already filtered by the caller).
 * Orders come from NewOrderSingle (35=D). Fills come from ExecutionReports (35=8) with LastQty (32) > 0,
 * counted once per ExecID (17) so a resent report is not counted twice.
 */
const value = (message, tag) => message.fields.find(f => f.tag === tag)?.value ?? null;
const BUY = ['1', '3'];
const SELL = ['2', '4', '5', '6'];
const sideOf = message => { const s = value(message, 54); return BUY.includes(s) ? 'buy' : SELL.includes(s) ? 'sell' : null; };
const num = text => { const n = Number(text); return Number.isFinite(n) ? n : 0; };
const empty = () => ({ orders: 0, orderedQty: 0, fills: 0, filledQty: 0, notional: 0 });

export function tradeSummary(decoded) {
  const bySymbol = new Map();
  const seenExec = new Set();
  const row = symbol => {
    if (!bySymbol.has(symbol)) bySymbol.set(symbol, { symbol, buy: empty(), sell: empty() });
    return bySymbol.get(symbol);
  };
  for (const message of decoded) {
    const type = value(message, 35);
    const symbol = value(message, 55);
    const side = sideOf(message);
    if (!symbol || !side) continue;
    if (type === 'D') {
      const cell = row(symbol)[side];
      cell.orders += 1;
      cell.orderedQty += num(value(message, 38));
    } else if (type === '8') {
      const lastQty = num(value(message, 32));
      if (lastQty <= 0) continue;
      const execId = value(message, 17);
      const key = `${value(message, 37) ?? ''}|${execId ?? `#${message.number}`}`;
      if (seenExec.has(key)) continue;
      seenExec.add(key);
      const cell = row(symbol)[side];
      cell.fills += 1;
      cell.filledQty += lastQty;
      cell.notional += lastQty * num(value(message, 31));
    }
  }
  return [...bySymbol.values()].sort((a, b) => a.symbol.localeCompare(b.symbol));
}
