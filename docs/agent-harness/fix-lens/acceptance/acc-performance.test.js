// FXL-19: performance at the v1.3 size (PRD v1.3 TR-005; design v1.3 section 9). The log is built here, and the
// counts it must give were worked out from how it is built, not from the product.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { orderGroups } from "../src/orders.js";
import { tradeSummary } from "../src/summary.js";
import { applyFilters } from "../src/filters.js";

const S = "\x01";
const enc = new TextEncoder();
function fixmsg(fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=FIX.4.4${S}9=${enc.encode(body).length}${S}`;
  let sum = 0;
  for (const b of enc.encode(head + body)) sum += b;
  return (head + body + `10=${String(sum % 256).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// Order o is messages 5o+1 to 5o+5: a NewOrder, three fills of 100 at 71.25 and a heartbeat. Messages alternate
// between two sessions, each direction with its own sequence, so there is no gap. Side: even o buys, odd o
// sells. Symbol: o mod 3. Account: o mod 4.
const SYMBOLS = ["VOD.L", "BARC.L", "AZN.L"];
function log(n, pad = 0) {
  const rows = [];
  const seq = {};
  const next = (k) => (seq[k] = (seq[k] ?? 0) + 1);
  const text = pad ? [[58, "x".repeat(pad)]] : [];
  for (let i = 0; i < n; i++) {
    const [cli, brk] = i % 2 ? ["CLI2", "BRK2"] : ["CLI1", "BRK1"];
    const o = Math.floor(i / 5);
    const k = i % 5;
    const sym = SYMBOLS[o % 3];
    const sideOf = 1 + (o % 2);
    if (k === 0) rows.push(fixmsg([[35, "D"], [49, cli], [56, brk], [34, next(cli)], [52, "20261127-10:00:00"], [11, `C${o}`], [1, `ACC${o % 4}`], [55, sym], [54, sideOf], [38, 1000], [40, 2], [44, 71.5], ...text]));
    else if (k === 4) rows.push(fixmsg([[35, "0"], [49, cli], [56, brk], [34, next(cli)], [52, "20261127-10:00:02"], ...text]));
    else rows.push(fixmsg([[35, "8"], [49, brk], [56, cli], [34, next(brk)], [52, "20261127-10:00:01"], [37, `O${o}`], [11, `C${o}`], [17, `E${i}`], [150, "F"], [39, 1], [55, sym], [54, sideOf], [32, 100], [31, 71.25], [14, 100 * k], [6, 71.25], [151, 1000 - 100 * k], ...text]));
  }
  return rows.join("\n");
}
const timed = (fn) => { const t0 = performance.now(); const value = fn(); return [value, performance.now() - t0]; };

test("10,000 mixed messages: analyse under 5 seconds, each view under 1 second, and the right answers", () => {
  const text = log(10000);
  const [r, analyseMs] = timed(() => analyse(text));
  expect(r.ok).toBe(true);
  expect([r.decoded.length, r.errors.length, r.timeline.length]).toEqual([10000, 0, 10000]);
  expect(r.timeline.filter((e) => e.name === "SequenceGap").length).toBe(0);
  expect(analyseMs).toBeLessThan(5000);

  const [groups, groupsMs] = timed(() => orderGroups(r.decoded));
  expect(groups.length).toBe(2000);
  expect(groups[1999].numbers).toEqual([9996, 9997, 9998, 9999]);
  expect(groupsMs).toBeLessThan(1000);

  const [summary, summaryMs] = timed(() => tradeSummary(r.decoded));
  // 2,000 orders over six (symbol, side) cells: o mod 6 of 0 and 1 hold 334 orders, the others 333
  expect(summary.unmatched).toBe(0);
  expect(summary.rows.map((row) => [row.symbol, row.buy.orders, row.buy.filledQty, row.sell.orders, row.sell.filledQty])).toEqual([
    ["AZN.L", 333, 99900, 333, 99900],
    ["BARC.L", 333, 99900, 334, 100200],
    ["VOD.L", 334, 100200, 333, 99900],
  ]);
  expect(summary.rows[2].buy.notional).toBeCloseTo(100200 * 71.25, 4);
  expect(summaryMs).toBeLessThan(1000);

  const [passing, filterMs] = timed(() => applyFilters(r.decoded, { account: "ACC1", senderCompId: null, senderSubId: null, targetCompId: null, targetSubId: null }));
  // 500 orders have ACC1 (o mod 4 is 1); each has four messages, and heartbeats belong to no order
  expect(passing.length).toBe(2000);
  expect(passing.slice(0, 4).map((m) => m.number)).toEqual([6, 7, 8, 9]);
  expect(filterMs).toBeLessThan(1000);

  const [bySender, senderMs] = timed(() => applyFilters(r.decoded, { senderCompId: "BRK2" }));
  // BRK2 sends the execution reports that fall on even message numbers
  expect(bySender.length).toBe(3000);
  expect(senderMs).toBeLessThan(1000);
});

test("10,000 messages padded to just under 10,485,760 bytes: analyse under 5 seconds", () => {
  const text = log(10000, 900);
  const bytes = enc.encode(text).length;
  expect(bytes).toBeGreaterThan(10400000);
  expect(bytes).toBeLessThanOrEqual(10485760);
  const [r, ms] = timed(() => analyse(text));
  expect(r.ok).toBe(true);
  expect([r.decoded.length, r.errors.length, r.limit.bytes, r.limit.messages]).toEqual([10000, 0, bytes, 10000]);
  expect(r.decoded[9999].fields.find((f) => f.tag === 58).value).toBe("x".repeat(900));
  expect(ms).toBeLessThan(5000);
});
