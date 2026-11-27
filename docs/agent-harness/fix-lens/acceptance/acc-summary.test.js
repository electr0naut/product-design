// FXL-12: the trading summary (PRD v1.2 US-008; design v1.2 section 13).
// The expected figures were computed by an independent Python implementation of section 13.
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
// One line per message: "35=8 37=O1 ..." becomes a valid message from BROKER to CLIENT.
const decodedOf = (begin, lines) => {
  const text = lines.map((line, i) => fixmsg(begin, [[49, "BROKER"], [56, "CLIENT"], [34, i + 1],
    ...line.trim().split(/\s+/).map((p) => p.split("="))].sort((a, b) => (a[0] === "35" ? -1 : b[0] === "35" ? 1 : 0)))).join("\n");
  const r = analyse(text);
  expect(r.errors).toEqual([]);
  expect(r.decoded.length).toBe(lines.length);
  return r.decoded;
};
const A = [
  "35=D 11=C1 1=ACC1 55=VOD.L 54=1 38=1000",
  "35=8 37=O1 11=C1 17=E1 150=F 55=VOD.L 54=1 32=400 31=71.25",
  "35=8 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5",
  "35=8 43=Y 37=O1 11=C1 17=E2 150=F 55=VOD.L 54=1 32=600 31=71.5",
  "35=8 37=O1 11=C1 17=E3 19=E1 150=G 55=VOD.L 54=1 32=300 31=71.2",
  "35=8 37=O1 11=C1 17=E4 19=E2 150=H 55=VOD.L 54=1 32=0 31=0",
  "35=D 11=C2 1=ACC2 55=VOD.L 54=2 38=500",
  "35=8 37=O2 11=C2 17=E5 150=F 55=VOD.L 54=2 32=200 31=72",
  "35=8 37=O2 11=C2 17=E6 19=E5 150=G 55=VOD.L 54=2 32=250 31=72.1",
  "35=8 37=O2 11=C2 17=E7 19=E6 150=G 55=VOD.L 54=2 32=260 31=72.2",
  "35=8 37=O9 11=C9 17=E8 19=ZZ 150=H 55=VOD.L 54=1 32=0",
  "35=8 37=O8 11=C3 17=E9 19=YY 150=G 55=BARC.L 54=5 32=50 31=2.5",
  "35=D 11=C3 1=ACC1 55=BARC.L 54=5 38=50",
  "35=8 37=O3 11=C4 17=E10 150=F 55=AZN.L 54=1 32=10",
  "35=8 37=O3 11=C4 17=E11 150=F 55=AZN.L 54=8 32=10 31=100",
  "35=8 37=O3 11=C4 17=E12 150=F 54=1 32=10 31=100",
  "35=8 37=O3 11=C4 17=E13 150=F 55=AZN.L 54=1 32=0 31=100",
  "35=8 37=O1 11=C1 17=E14 19=E2 150=G 55=VOD.L 54=1 32=999 31=1",
  "35=8 37=O3 11=C4 17=E15 150=0 55=AZN.L 54=1 32=5 31=100",
];
const ZERO = { orders: 0, orderedQty: 0, fills: 0, filledQty: 0, notional: 0, pricedQty: 0 };
const side = (orders, orderedQty, fills, filledQty, notional, pricedQty) => ({ orders, orderedQty, fills, filledQty, notional, pricedQty });
// Compare numbers to 6 decimal places.
const same = (got, want) => {
  expect(got.rows.map((r) => r.symbol)).toEqual(want.rows.map((r) => r.symbol));
  got.rows.forEach((r, i) => {
    for (const s of ["buy", "sell"]) {
      expect(Object.keys(r[s]).sort()).toEqual(Object.keys(ZERO).sort());
      for (const k of Object.keys(ZERO)) expect(r[s][k], `${r.symbol} ${s} ${k}`).toBeCloseTo(want.rows[i][s][k], 6);
    }
  });
  expect(got.unmatched).toBe(want.unmatched);
};
const VOD_SELL = side(1, 500, 1, 260, 18772, 260);
const BARC_SELL = side(1, 50, 1, 50, 125, 50);
const FULL_A = { unmatched: 2, rows: [
  { symbol: "AZN.L", buy: side(0, 0, 1, 10, 0, 0), sell: ZERO },
  { symbol: "BARC.L", buy: ZERO, sell: BARC_SELL },
  { symbol: "VOD.L", buy: side(1, 1000, 1, 300, 21360, 300), sell: VOD_SELL },
] };

test("result, row and side keys", () => {
  const s = tradeSummary(decodedOf("FIX.4.4", A));
  expect(Object.keys(s).sort()).toEqual(["rows", "unmatched"]);
  expect(Object.keys(s.rows[0]).sort()).toEqual(["buy", "sell", "symbol"]);
});

test("log A: resends, corrections, a correction of a correction, cancels and unmatched reports", () => {
  same(tradeSummary(decodedOf("FIX.4.4", A)), FULL_A);
});

test("a cancel that names the ExecID of a correction removes the execution", () => {
  const s = tradeSummary(decodedOf("FIX.4.4", [
    "35=8 37=O1 11=C1 17=E1 150=F 55=VOD.L 54=1 32=100 31=10",
    "35=8 37=O1 11=C1 17=E2 19=E1 150=G 55=VOD.L 54=1 32=120 31=10.5",
    "35=8 37=O1 11=C1 17=E3 19=E2 150=H 55=VOD.L 54=1",
  ]));
  expect(s).toEqual({ rows: [], unmatched: 0 });
});

test("FIX 4.2: ExecTransType cancels and corrects, and a status report counts for nothing", () => {
  same(tradeSummary(decodedOf("FIX.4.2", [
    "35=8 37=O1 11=C1 17=X1 20=0 150=2 39=2 55=IBM 54=1 32=100 31=50",
    "35=8 37=O1 11=C1 17=X2 19=X1 20=1 150=2 39=2 55=IBM 54=1 32=100 31=50",
    "35=8 37=O1 11=C1 17=X3 150=1 39=1 55=IBM 54=1 32=40 31=51",
    "35=8 37=O1 11=C1 17=X4 19=X3 20=2 150=1 39=1 55=IBM 54=1 32=45 31=51.5",
    "35=8 37=O1 11=C1 17=0 20=3 150=2 39=1 55=IBM 54=1 32=45 31=51.5",
  ])), { unmatched: 0, rows: [{ symbol: "IBM", buy: side(0, 0, 1, 45, 2317.5, 45), sell: ZERO }] });
});

test("shown limits what is counted: a corrected execution keeps the number of its original Fill", () => {
  const d = decodedOf("FIX.4.4", A);
  const without2 = new Set(d.map((m) => m.number).filter((n) => n !== 2));
  same(tradeSummary(d, without2), { unmatched: 2, rows: [FULL_A.rows[0], FULL_A.rows[1],
    { symbol: "VOD.L", buy: side(1, 1000, 0, 0, 0, 0), sell: VOD_SELL }] });
});

test("shown 7 to 12: only those orders, executions and unmatched reports", () => {
  same(tradeSummary(decodedOf("FIX.4.4", A), new Set([7, 8, 9, 10, 11, 12])), { unmatched: 2, rows: [
    { symbol: "BARC.L", buy: ZERO, sell: side(0, 0, 1, 50, 125, 50) },
    { symbol: "VOD.L", buy: ZERO, sell: VOD_SELL },
  ] });
});

test("shown that leaves out the unmatched reports does not count them", () => {
  expect(tradeSummary(decodedOf("FIX.4.4", A), new Set([7, 8, 9, 10])).unmatched).toBe(0);
});

test("sides: 1 and 3 buy; 2, 4, 5 and 6 sell; others not counted", () => {
  const lines = ["1", "3", "2", "4", "5", "6", "7", "8", "9"].flatMap((s, i) => [
    `35=D 11=C${i} 55=X 54=${s} 38=10`, `35=8 37=O${i} 11=C${i} 17=E${i} 150=F 55=X 54=${s} 32=10 31=1`]);
  same(tradeSummary(decodedOf("FIX.4.4", lines)), { unmatched: 0, rows: [
    { symbol: "X", buy: side(2, 20, 2, 20, 20, 20), sell: side(4, 40, 4, 40, 40, 40) }] });
});

test("a Fill that makes no execution is not remembered: a cancel naming it is unmatched", () => {
  const s = tradeSummary(decodedOf("FIX.4.4", [
    "35=8 37=O1 11=C1 17=E1 150=F 54=1 32=10 31=1",
    "35=8 37=O1 11=C1 17=E2 19=E1 150=H 54=1",
  ]));
  expect(s).toEqual({ rows: [], unmatched: 1 });
});

test("reports without an ExecID are never resends", () => {
  const line = "35=8 37=O1 11=C1 150=F 55=X 54=1 32=10 31=2";
  same(tradeSummary(decodedOf("FIX.4.4", [line, line])), { unmatched: 0, rows: [{ symbol: "X", buy: side(0, 0, 2, 20, 40, 20), sell: ZERO }] });
});

test("the same ExecID under another OrderID is another execution", () => {
  same(tradeSummary(decodedOf("FIX.4.4", ["35=8 37=O1 17=E1 150=F 55=X 54=1 32=10 31=2", "35=8 37=O2 17=E1 150=F 55=X 54=1 32=5 31=4"])),
    { unmatched: 0, rows: [{ symbol: "X", buy: side(0, 0, 2, 15, 40, 15), sell: ZERO }] });
});

test("an unsupported version counts for nothing: no execution and no order", () => {
  expect(tradeSummary(decodedOf("FIX.4.1", ["35=8 37=O1 17=E1 150=2 55=X 54=1 32=10 31=2", "35=D 11=C1 55=X 54=1 38=10"])))
    .toEqual({ rows: [], unmatched: 0 });
});

test("a correction without a usable quantity changes nothing, and no figure is NaN", () => {
  for (const qty of ["32=abc", "32=0", "32=-5", ""]) {
    const s = tradeSummary(decodedOf("FIX.4.4", [
      "35=8 37=O1 17=E1 150=F 55=X 54=1 32=100 31=10",
      `35=8 37=O1 17=E2 19=E1 150=G 55=X 54=1 ${qty} 31=99`.replace(/\s+/g, " "),
    ]));
    same(s, { unmatched: 0, rows: [{ symbol: "X", buy: side(0, 0, 1, 100, 1000, 100), sell: ZERO }] });
  }
});

test("a resent unmatched report is counted once", () => {
  const cancel = "35=8 37=O9 17=E8 19=ZZ 150=H 55=X 54=1";
  const correct = "35=8 37=O9 17=E9 19=YY 150=G 55=X 54=1 32=0";
  expect(tradeSummary(decodedOf("FIX.4.4", [cancel, cancel, correct, correct]))).toEqual({ rows: [], unmatched: 2 });
});

test("an empty Symbol or ExecID counts as missing", () => {
  const s = tradeSummary(decodedOf("FIX.4.4", [
    "35=8 37=O1 17=E1 150=F 55= 54=1 32=10 31=2",
    "35=D 11=C1 55= 54=1 38=10",
    "35=8 37=O2 17= 150=F 55=X 54=1 32=10 31=2",
    "35=8 37=O2 17= 150=F 55=X 54=1 32=10 31=2",
  ]));
  same(s, { unmatched: 0, rows: [{ symbol: "X", buy: side(0, 0, 2, 20, 40, 20), sell: ZERO }] });
});

test("rows are sorted with plain string comparison", () => {
  const s = tradeSummary(decodedOf("FIX.4.4", ["35=D 11=C1 55=alpha 54=1 38=1", "35=D 11=C2 55=Zeta 54=1 38=1", "35=D 11=C3 55=Beta 54=1 38=1"]));
  expect(s.rows.map((r) => r.symbol)).toEqual(["Beta", "Zeta", "alpha"]);
});

test("pure, and 1,000 messages in under 1 second", () => {
  const lines = [];
  for (let i = 0; i < 500; i++) lines.push(`35=D 11=C${i} 55=S${i % 7} 54=${1 + (i % 2)} 38=100`, `35=8 37=O${i} 11=C${i} 17=E${i} 150=F 55=S${i % 7} 54=${1 + (i % 2)} 32=100 31=${10 + (i % 5)}`);
  const d = decodedOf("FIX.4.4", lines);
  const before = JSON.stringify(d);
  const t0 = performance.now();
  const s = tradeSummary(d);
  expect(performance.now() - t0).toBeLessThan(1000);
  expect(s.rows.length).toBe(7);
  expect(JSON.stringify(d)).toBe(before);
});
