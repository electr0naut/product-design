// FXL-13: the five filters (PRD v1.2 US-009; design v1.2 section 14).
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { FILTERS, filterOptions, applyFilters } from "../src/filters.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// [type, sender, target, ...extra fields]
const log = (...rows) => {
  const text = rows.map(([type, from, to, ...extra], i) => fixmsg("FIX.4.4", [[35, type], [49, from], [56, to], [34, i + 1], ...extra])).join("\n");
  const r = analyse(text);
  expect(r.errors).toEqual([]);
  return r.decoded;
};
const numbers = (list) => list.map((m) => m.number);
const NONE = { account: null, senderCompId: null, senderSubId: null, targetCompId: null, targetSubId: null };
const LOG = () => log(
  ["D", "CLI", "BRK", [11, "C1"], [1, "ACC1"], [50, "desk1"], [57, "algo"]],
  ["8", "BRK", "CLI", [11, "C1"], [37, "O1"], [150, "0"]],
  ["D", "CLI", "BRK", [11, "C2"], [1, "ACC2"], [50, "Desk2"]],
  ["8", "BRK", "CLI", [11, "C2"], [37, "O2"], [150, "0"]],
  ["0", "CLI", "BRK"],
  ["0", "BRK", "CLI", [1, "ACC1"]],
  ["8", "BRK", "CLI", [37, "O1"], [150, "F"], [17, "E1"]],
);

test("FILTERS is the five filters, in order", () => {
  expect(FILTERS).toEqual([
    { key: "account", tag: 1, label: "Account" },
    { key: "senderCompId", tag: 49, label: "SenderCompID" },
    { key: "senderSubId", tag: 50, label: "SenderSubID" },
    { key: "targetCompId", tag: 56, label: "TargetCompID" },
    { key: "targetSubId", tag: 57, label: "TargetSubID" },
  ]);
});

test("filterOptions: distinct non-empty values, plain string order, empty list when absent", () => {
  const o = filterOptions(LOG());
  expect(o).toEqual({ account: ["ACC1", "ACC2"], senderCompId: ["BRK", "CLI"], senderSubId: ["Desk2", "desk1"],
    targetCompId: ["BRK", "CLI"], targetSubId: ["algo"] });
  expect(filterOptions(log(["0", "A", "B"])).account).toEqual([]);
});

test("no filter set returns every message, in order", () => {
  const d = LOG();
  expect(numbers(applyFilters(d, NONE))).toEqual([1, 2, 3, 4, 5, 6, 7]);
  expect(numbers(applyFilters(d, {}))).toEqual([1, 2, 3, 4, 5, 6, 7]);
});

test("the four id filters match the message's own field", () => {
  const d = LOG();
  expect(numbers(applyFilters(d, { ...NONE, senderCompId: "CLI" }))).toEqual([1, 3, 5]);
  expect(numbers(applyFilters(d, { ...NONE, targetCompId: "CLI" }))).toEqual([2, 4, 6, 7]);
  expect(numbers(applyFilters(d, { ...NONE, senderSubId: "desk1" }))).toEqual([1]);
  expect(numbers(applyFilters(d, { ...NONE, targetSubId: "algo" }))).toEqual([1]);
  expect(numbers(applyFilters(d, { ...NONE, senderSubId: "nobody" }))).toEqual([]);
});

test("Account keeps whole orders, and a message outside all orders that carries the Account", () => {
  const d = LOG();
  expect(numbers(applyFilters(d, { ...NONE, account: "ACC1" }))).toEqual([1, 2, 6, 7]);
  expect(numbers(applyFilters(d, { ...NONE, account: "ACC2" }))).toEqual([3, 4]);
});

test("filters combine, and order grouping for Account uses the whole log", () => {
  const d = LOG();
  // The Account is only on the client's message, which the sender filter removes.
  expect(numbers(applyFilters(d, { ...NONE, account: "ACC1", senderCompId: "BRK" }))).toEqual([2, 6, 7]);
  expect(numbers(applyFilters(d, { ...NONE, account: "ACC2", senderCompId: "CLI", senderSubId: "Desk2" }))).toEqual([3]);
  expect(numbers(applyFilters(d, { ...NONE, account: "ACC1", targetSubId: "algo", senderCompId: "BRK" }))).toEqual([]);
});

test("the first value of a repeated tag counts", () => {
  const d = log(["D", "A", "B", [11, "C1"], [1, "X"], [1, "Y"]]);
  expect(filterOptions(d).account).toEqual(["X"]);
  expect(numbers(applyFilters(d, { ...NONE, account: "Y" }))).toEqual([]);
});

test("pure, a subset in log order, and 1,000 messages in under 1 second", () => {
  const rows = [];
  for (let i = 0; i < 500; i++) rows.push(["D", "CLI", "BRK", [11, `C${i}`], [1, `ACC${i % 5}`]], ["8", "BRK", "CLI", [11, `C${i}`], [37, `O${i}`], [150, "0"]]);
  const d = log(...rows);
  const before = JSON.stringify(d);
  const t0 = performance.now();
  const kept = applyFilters(d, { ...NONE, account: "ACC3" });
  expect(performance.now() - t0).toBeLessThan(1000);
  expect(kept.length).toBe(200);
  expect(kept.every((m) => d.includes(m))).toBe(true);
  expect(numbers(kept)).toEqual([...numbers(kept)].sort((a, b) => a - b));
  filterOptions(d);
  expect(JSON.stringify(d)).toBe(before);
});
