// FXL-23: executions with their executing party, and cancels and corrections wherever the execution stands
// (PRD v1.4 AC-041 to AC-044; design v1.4 section 13). Every figure was worked by hand from section 13.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { tradeSummary } from "../src/summary.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// One line per message, 35 first: "35=8 49=BRK 56=CLI 37=O1 ..."; a line without 49 or 56 has none.
const decodedOf = (begin, lines) => {
  const r = analyse(lines.map((line) => fixmsg(begin, line.trim().split(/\s+/).map((p) => p.split("=")))).join("\n"));
  expect(r.errors).toEqual([]);
  expect(r.decoded.length).toBe(lines.length);
  return r.decoded;
};
const summary = (lines, shown, begin = "FIX.4.4") => tradeSummary(decodedOf(begin, lines), shown);
const side = (orders, orderedQty, fills, filledQty, notional, pricedQty) => ({ orders, orderedQty, fills, filledQty, notional, pricedQty });
const ZERO = side(0, 0, 0, 0, 0, 0);
const FILL = "150=F 55=ACME 54=1";

test("two venues that use the same OrderID and ExecID: both fills count", () => {
  expect(summary([
    "35=D 49=CLI 56=VENUEA 11=A1 55=ACME 54=1 38=100",
    "35=D 49=CLI 56=VENUEB 11=B1 55=ACME 54=1 38=200",
    `35=8 49=VENUEA 56=CLI 37=1 11=A1 17=1 ${FILL} 32=100 31=10`,
    `35=8 49=VENUEB 56=CLI 37=1 11=B1 17=1 ${FILL} 32=200 31=11`,
  ])).toEqual({ rows: [{ symbol: "ACME", buy: side(2, 300, 2, 300, 3200, 300), sell: ZERO }], unmatched: 0 });
});

test("the same on FIX 4.2", () => {
  expect(summary([
    "35=8 49=VENUEA 56=CLI 37=1 17=1 20=0 150=2 55=ACME 54=1 32=100 31=10",
    "35=8 49=VENUEB 56=CLI 37=1 17=1 20=0 150=2 55=ACME 54=1 32=200 31=11",
  ], undefined, "FIX.4.2").rows).toEqual([{ symbol: "ACME", buy: side(0, 0, 2, 300, 3200, 300), sell: ZERO }]);
});

test("a report sent again by the same sender, to the same or to another CompID, is counted once", () => {
  expect(summary([
    `35=8 49=BRK 56=CLI 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 49=BRK 56=CLI 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 49=BRK 56=DROP 37=O1 17=E1 ${FILL} 32=100 31=10`,
  ]).rows).toEqual([{ symbol: "ACME", buy: side(0, 0, 1, 100, 1000, 100), sell: ZERO }]);
});

test("reports without a SenderCompID share the empty party", () => {
  expect(summary([
    `35=8 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 56=CLI 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 49=BRK 37=O1 17=E1 ${FILL} 32=40 31=10`,
  ]).rows).toEqual([{ symbol: "ACME", buy: side(0, 0, 2, 140, 1400, 140), sell: ZERO }]);
});

test("a sender and an OrderID never run together", () => {
  // sender "A|B" with OrderID "C" is not sender "A" with OrderID "B|C"
  for (const sep of ["|", ":", ",", "/", "_", "\"", "\\"]) {
    const s = summary([
      `35=8 49=A${sep}B 56=CLI 37=C 17=E1 ${FILL} 32=100 31=10`,
      `35=8 49=A 56=CLI 37=B${sep}C 17=E1 ${FILL} 32=100 31=10`,
    ]);
    expect(s.rows[0].buy.fills).toBe(2);
  }
  // OrderID "A|B" with ExecID "C" is not OrderID "A" with ExecID "B|C"
  expect(summary([
    `35=8 49=BRK 56=CLI 37=A|B 17=C ${FILL} 32=100 31=10`,
    `35=8 49=BRK 56=CLI 37=A 17=B|C ${FILL} 32=100 31=10`,
  ]).rows[0].buy.fills).toBe(2);
});

test("a trade cancel that stands before its fill removes it, and is not unmatched", () => {
  expect(summary([
    "35=D 49=A 56=B 11=C1 55=ACME 54=1 38=100",
    "35=8 49=B 56=A 37=O1 11=C1 17=E2 19=E1 150=H 55=ACME 54=1 32=100 31=10",
    `35=8 49=B 56=A 37=O1 11=C1 17=E1 ${FILL} 32=100 31=10`,
  ])).toEqual({ rows: [{ symbol: "ACME", buy: side(1, 100, 0, 0, 0, 0), sell: ZERO }], unmatched: 0 });
});

test("the same on FIX 4.2, with ExecTransType", () => {
  expect(summary([
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 20=1 150=2 55=ACME 54=2 32=100 31=10",
    "35=8 49=B 56=A 37=O1 17=E1 20=0 150=2 55=ACME 54=2 32=100 31=10",
    "35=8 49=B 56=A 37=O1 17=E3 20=0 150=1 55=ACME 54=2 32=30 31=9",
  ], undefined, "FIX.4.2")).toEqual({ rows: [{ symbol: "ACME", buy: ZERO, sell: side(0, 0, 1, 30, 270, 30) }], unmatched: 0 });
});

test("a trade correction that stands before its fill corrects it; the execution keeps the fill's number", () => {
  const lines = [
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=G 55=ACME 54=1 32=60 31=11",
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
  ];
  expect(summary(lines)).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 1, 60, 660, 60), sell: ZERO }], unmatched: 0 });
  // the execution is message 2, the fill, so it shows with message 2 and not with message 1
  expect(summary(lines, new Set([2])).rows).toEqual([{ symbol: "ACME", buy: side(0, 0, 1, 60, 660, 60), sell: ZERO }]);
  expect(summary(lines, new Set([1]))).toEqual({ rows: [], unmatched: 0 });
});

test("a correction and then a cancel of that correction, both before the fill", () => {
  expect(summary([
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=G 55=ACME 54=1 32=60 31=11",
    "35=8 49=B 56=A 37=O1 17=E3 19=E2 150=H 55=ACME 54=1 32=0 31=0",
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 49=B 56=A 37=O1 17=E4 ${FILL} 32=7 31=10`,
  ])).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 1, 7, 70, 7), sell: ZERO }], unmatched: 0 });
});

test("a fill sent again after its cancel stays cancelled", () => {
  expect(summary([
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=H 55=ACME 54=1 32=0 31=0",
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=H 55=ACME 54=1 32=0 31=0",
  ])).toEqual({ rows: [], unmatched: 0 });
});

test("a cancel or a correction only finds an execution of its own sender and OrderID", () => {
  expect(summary([
    `35=8 49=VENUEA 56=CLI 37=1 17=1 ${FILL} 32=100 31=10`,
    "35=8 49=VENUEB 56=CLI 37=1 17=2 19=1 150=H 55=ACME 54=1 32=0 31=0",
    "35=8 49=VENUEA 56=CLI 37=2 17=3 19=1 150=H 55=ACME 54=1 32=0 31=0",
    "35=8 49=VENUEB 56=CLI 37=1 17=4 19=1 150=G 55=ACME 54=1 32=5 31=20",
  ])).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 2, 105, 1100, 105), sell: ZERO }], unmatched: 3 });
});

test("an execution not in the log is still unmatched, and the list stays in log order", () => {
  const lines = [
    "35=8 49=B 56=A 37=O7 17=E9 19=GONE 150=H 55=ACME 54=1 32=0 31=0",
    "35=8 49=B 56=A 37=O7 17=E8 19=AWAY 150=G 55=ACME 54=1 32=50 31=0.1",
    `35=8 49=B 56=A 37=O7 17=E7 ${FILL} 32=100 31=0.2`,
  ];
  // the unmatched correction makes an execution of 50 at 0.1 (message 2); the fill is message 3
  const s = summary(lines);
  expect(s.unmatched).toBe(2);
  expect(s.rows[0].buy.fills).toBe(2);
  expect(s.rows[0].buy.filledQty).toBe(150);
  // summed in log order: 50 * 0.1 first, then 100 * 0.2
  expect(s.rows[0].buy.notional).toBe(50 * 0.1 + 100 * 0.2);
  expect(summary(lines, new Set([1]))).toEqual({ rows: [], unmatched: 1 });
  expect(summary(lines, new Set([2]))).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 1, 50, 50 * 0.1, 50), sell: ZERO }], unmatched: 1 });
  expect(summary(lines, new Set([3]))).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 1, 100, 100 * 0.2, 100), sell: ZERO }], unmatched: 0 });
});

test("the usual order still works: fill, correction, cancel of the correction", () => {
  expect(summary([
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=G 55=ACME 54=1 32=60 31=11",
    `35=8 49=B 56=A 37=O1 17=E5 ${FILL} 32=1 31=1`,
    "35=8 49=B 56=A 37=O1 17=E3 19=E2 150=H 55=ACME 54=1 32=0 31=0",
  ])).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 1, 1, 1, 1), sell: ZERO }], unmatched: 0 });
});

test("pure: the argument is unchanged and two calls agree", () => {
  const d = decodedOf("FIX.4.4", [
    "35=8 49=B 56=A 37=O1 17=E2 19=E1 150=H 55=ACME 54=1 32=0 31=0",
    `35=8 49=B 56=A 37=O1 17=E1 ${FILL} 32=100 31=10`,
  ]);
  const before = JSON.stringify(d);
  expect(tradeSummary(d)).toEqual(tradeSummary(d));
  expect(JSON.stringify(d)).toBe(before);
});

test("10,000 reports, every cancel before its fill, in under 1 second", () => {
  // Pair p: a cancel naming E<p>, then the fill E<p>, for p below 2,500; then 5,000 plain fills of 2.
  const lines = [];
  for (let p = 0; p < 2500; p++) {
    lines.push(`35=8 49=B${p % 7} 56=A 37=O${p % 100} 17=X${p} 19=E${p} 150=H 55=ACME 54=1 32=0 31=0`,
      `35=8 49=B${p % 7} 56=A 37=O${p % 100} 17=E${p} ${FILL} 32=100 31=10`);
  }
  for (let p = 0; p < 5000; p++) lines.push(`35=8 49=B${p % 7} 56=A 37=O${p % 100} 17=F${p} ${FILL} 32=2 31=10`);
  const d = decodedOf("FIX.4.4", lines);
  const t0 = performance.now();
  const s = tradeSummary(d);
  const ms = performance.now() - t0;
  expect(s).toEqual({ rows: [{ symbol: "ACME", buy: side(0, 0, 5000, 10000, 100000, 10000), sell: ZERO }], unmatched: 0 });
  expect(ms).toBeLessThan(1000);
});
