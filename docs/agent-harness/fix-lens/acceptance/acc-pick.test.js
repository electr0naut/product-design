// @vitest-environment jsdom
// FXL-26: an id button opens the order of its message, and figures round a half away from zero
// (PRD v1.4 AC-036, AC-045; design v1.4 sections 8.2, 12 and 13). Runs from the repo root.
import { test, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import { analyse } from "../src/analyse.js";
import { render } from "../src/render.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
const HTML = readFileSync("index.html", "utf8");
const page = () => { document.documentElement.innerHTML = HTML.replace(/^[\s\S]*?<html[^>]*>/i, "").replace(/<\/html>[\s\S]*$/i, ""); };
async function boot() {
  page();
  window.matchMedia = () => ({ matches: false, media: "", onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent() { return false; } });
  vi.resetModules();
  await import("../src/main.js");
}
const q = (sel) => document.querySelector(sel);
const all = (sel) => [...document.querySelectorAll(sel)];
const texts = (sel) => all(sel).map((n) => n.textContent.trim());
const NOFILTER = { account: null, senderCompId: null, senderSubId: null, targetCompId: null, targetSubId: null };
// One line per message, 35 first: "35=8 49=BRK 56=CLI 37=O1 ...".
const textOf = (lines, begin = "FIX.4.4") => lines.map((line) => fixmsg(begin, line.trim().split(/\s+/).map((p) => p.split("=")))).join("\n");
const calls = () => { const log = []; return { log, pick: (...a) => log.push(["pick", ...a]), clear: () => log.push(["clear"]), setFilter: () => {}, setPage: () => {} }; };
const cards = () => texts("#decode article .num");
const banner = () => q("#summary .order-story strong")?.textContent ?? null;
const card = (n) => all("#decode article").find((a) => a.querySelector(".num").textContent === `#${n}`);
const event = (n) => all("#timeline li.event").find((li) => li.querySelector(".num").textContent === `#${n}`);
const button = (node, text) => [...node.querySelectorAll("button.order-link")].find((b) => b.textContent === text);
const rows = () => all("#summary .trades table.trade-table tr").filter((tr) => tr.querySelector("td")).map((tr) => [...tr.children].map((c) => c.textContent));

// Order A (CLI1) has ClOrdID 1001 and OrderID 7. Order B (CLI2) has ClOrdID ZZ9, and the broker gave it OrderID 1001.
const SHARED_VALUE = textOf([
  "35=D 49=CLI1 56=BRK 34=1 11=1001 55=AAA 54=1 38=100 40=1",
  "35=D 49=CLI2 56=BRK 34=1 11=ZZ9 55=BBB 54=2 38=50 40=1",
  "35=8 49=BRK 56=CLI1 34=1 37=7 11=1001 17=E1 150=0 39=0 55=AAA 54=1",
  "35=8 49=BRK 56=CLI2 34=1 37=1001 11=ZZ9 17=E2 150=F 39=2 55=BBB 54=2 32=50 31=7",
]);
// Two clients of one broker both use ClOrdID 1.
const TWO_CLIENTS = textOf([
  "35=D 49=CLI1 56=BRK 34=1 11=1 1=ACC1 55=AAA 54=1 38=100",
  "35=D 49=CLI2 56=BRK 34=1 11=1 1=ACC2 55=BBB 54=2 38=50",
  "35=8 49=BRK 56=CLI1 34=1 37=O-1 11=1 17=E1 150=F 55=AAA 54=1 32=100 31=5",
  "35=8 49=BRK 56=CLI2 34=1 37=O-2 11=1 17=E2 150=F 55=BBB 54=2 32=50 31=7",
]);

test("every id button calls pick with the id and the number of its message", () => {
  page();
  const h = calls();
  render(analyse(SHARED_VALUE), { orderId: null, filters: NOFILTER }, h);
  button(event(4), "OrderID 1001").click();
  button(event(4), "ClOrdID ZZ9").click();
  button(event(1), "ClOrdID 1001").click();
  button(card(4), "1001").click();
  button(card(3), "1001").click();
  button(card(3), "7").click();
  expect(h.log).toEqual([["pick", "1001", 4], ["pick", "ZZ9", 4], ["pick", "1001", 1], ["pick", "1001", 4], ["pick", "1001", 3], ["pick", "7", 3]]);
});

test("an OrigClOrdID button carries its message too", () => {
  page();
  const h = calls();
  render(analyse(textOf([
    "35=D 49=CLI 56=BRK 34=1 11=C1 55=AAA 54=1 38=100",
    "35=G 49=CLI 56=BRK 34=2 11=C2 41=C1 55=AAA 54=1 38=200",
  ])), { orderId: null, filters: NOFILTER }, h);
  button(event(2), "OrigClOrdID C1").click();
  button(card(2), "C1").click();
  expect(h.log).toEqual([["pick", "C1", 2], ["pick", "C1", 2]]);
});

test("view.orderMessage decides which order is shown when a value belongs to two", () => {
  page();
  const result = analyse(SHARED_VALUE);
  render(result, { orderId: "1001", orderMessage: 4, filters: NOFILTER }, calls());
  expect(cards()).toEqual(["#2", "#4"]);
  expect(banner()).toBe("ZZ9 · 1001");
  expect(texts("#timeline li.event .num")).toEqual(["#2", "#4"]);
  render(result, { orderId: "1001", orderMessage: 3, filters: NOFILTER }, calls());
  expect(cards()).toEqual(["#1", "#3"]);
  expect(banner()).toBe("1001 · 7");
});

test("a view without orderMessage still finds the order by its id", () => {
  page();
  const result = analyse(SHARED_VALUE);
  for (const view of [{ orderId: "ZZ9", filters: NOFILTER }, { orderId: "ZZ9", orderMessage: null, filters: NOFILTER }]) {
    render(result, view, calls());
    expect(cards()).toEqual(["#2", "#4"]);
  }
  render(result, { orderId: null, orderMessage: 4, filters: NOFILTER }, calls());
  expect(cards()).toEqual(["#1", "#2", "#3", "#4"]);
  expect(banner()).toBeNull();
});

test("on the page: the OrderID button of message 4 opens order B, not the order whose ClOrdID has that value", async () => {
  await boot();
  q("#paste").value = SHARED_VALUE;
  q("#decode-button").click();
  expect(cards()).toEqual(["#1", "#2", "#3", "#4"]);
  button(card(4), "1001").click();
  expect(cards()).toEqual(["#2", "#4"]);
  expect(banner()).toBe("ZZ9 · 1001");
  expect(texts("#summary .order-story .order-terms")).toEqual(["Sell 50 BBB Market"]);
  q("#summary button.show-all").click();
  expect(cards()).toEqual(["#1", "#2", "#3", "#4"]);
  expect(banner()).toBeNull();
  button(event(1), "ClOrdID 1001").click();
  expect(cards()).toEqual(["#1", "#3"]);
  expect(banner()).toBe("1001 · 7");
  // from inside order A, its own buttons stay in order A
  button(card(3), "1001").click();
  expect(cards()).toEqual(["#1", "#3"]);
  q("#decode-button").click();
  expect(cards()).toEqual(["#1", "#2", "#3", "#4"]);
  expect(banner()).toBeNull();
});

test("on the page: two clients with the same ClOrdID, each button opens its own client's order", async () => {
  await boot();
  q("#paste").value = TWO_CLIENTS;
  q("#decode-button").click();
  expect(texts("#summary .stats .stat").at(-1)).toBe("2 orders");
  button(card(2), "1").click();
  expect(cards()).toEqual(["#2", "#4"]);
  expect(banner()).toBe("1 · O-2");
  expect(rows()).toEqual([["BBB", "0", "0", "–", "1", "50", "7", "-50"]]);
  q("#summary button.show-all").click();
  button(event(3), "ClOrdID 1").click();
  expect(cards()).toEqual(["#1", "#3"]);
  expect(banner()).toBe("1 · O-1");
  expect(rows()).toEqual([["AAA", "1", "100", "5", "0", "0", "–", "+100"]]);
});

const draw = (lines) => { page(); render(analyse(textOf(lines))); };
const fill = (n, symbol, sideOf, qty, px) => `35=8 49=BRK 56=CLI 34=${n} 37=O${n} 17=E${n} 150=F 55=${symbol} 54=${sideOf} 32=${qty} 31=${px}`;

test("an average exactly on a half is rounded away from zero", () => {
  // TIE: (1 x 1.005 + 1 x 1.0001) / 2 = 1.00255. ELEVEN: (10 x 3.1 + 1 x 3.17865) / 11 = 3.10715.
  draw([fill(1, "TIE", 1, 1, 1.005), fill(2, "TIE", 1, 1, 1.0001), fill(3, "ELEVEN", 2, 10, 3.1), fill(4, "ELEVEN", 2, 1, 3.17865)]);
  expect(rows()).toEqual([
    ["ELEVEN", "0", "0", "–", "0", "11", "3.1072", "-11"],
    ["TIE", "0", "2", "1.0026", "0", "0", "–", "+2"],
  ]);
});

test("quantities and the net on a half: away from zero on both sides", () => {
  draw([fill(1, "BUY", 1, 2.00005, 1), fill(2, "SELL", 2, 10.00005, 1), fill(3, "TINY", 1, 0.00015, 1), fill(4, "WIDE", 2, 100000.00005, 1)]);
  expect(rows()).toEqual([
    ["BUY", "0", "2.0001", "1", "0", "0", "–", "+2.0001"],
    ["SELL", "0", "0", "–", "0", "10.0001", "1", "-10.0001"],
    ["TINY", "0", "0.0002", "1", "0", "0", "–", "+0.0002"],
    ["WIDE", "0", "0", "–", "0", "100000.0001", "1", "-100000.0001"],
  ]);
});

test("a half is still found when the whole part has eight, nine or ten digits", () => {
  // Fifteen significant digits reach the fifth decimal of a number with up to ten digits before the point.
  draw([fill(1, "EIGHT", 1, "87654321.00005", 1), fill(2, "NINE", 2, "123456789.12345", 1), fill(3, "TEN", 1, "9876543210.50005", 1), fill(4, "TENUP", 2, "1234567890.99995", 1)]);
  expect(rows()).toEqual([
    ["EIGHT", "0", "87654321.0001", "1", "0", "0", "–", "+87654321.0001"],
    ["NINE", "0", "0", "–", "0", "123456789.1235", "1", "-123456789.1235"],
    ["TEN", "0", "9876543210.5001", "1", "0", "0", "–", "+9876543210.5001"],
    ["TENUP", "0", "0", "–", "0", "1234567891", "1", "-1234567891"],
  ]);
});

test("values that are not on a half round as before", () => {
  // BELOW: (1.005 + 1.000098) / 2 = 1.002549. ABOVE: (1.005 + 1.000102) / 2 = 1.002551. THIRD: 4 / 3.
  draw([
    fill(1, "BELOW", 1, 1, 1.005), fill(2, "BELOW", 1, 1, 1.000098),
    fill(3, "ABOVE", 1, 1, 1.005), fill(4, "ABOVE", 1, 1, 1.000102),
    fill(5, "THIRD", 2, 1, 1), fill(6, "THIRD", 2, 2, 1.5),
    fill(7, "FRAC", 1, 0.1, 1), fill(8, "FRAC", 1, 0.2, 2),
    fill(9, "BIG", 1, 1500000, 1234.56789), fill(10, "LONG", 2, 123456789012.5, 71.25),
    fill(11, "SMALL", 1, 0.00004, 1), fill(12, "SMALLER", 2, 0.00004, 1),
  ]);
  expect(rows()).toEqual([
    ["ABOVE", "0", "2", "1.0026", "0", "0", "–", "+2"],
    ["BELOW", "0", "2", "1.0025", "0", "0", "–", "+2"],
    ["BIG", "0", "1500000", "1234.5679", "0", "0", "–", "+1500000"],
    ["FRAC", "0", "0.3", "1.6667", "0", "0", "–", "+0.3"],
    ["LONG", "0", "0", "–", "0", "123456789012.5", "71.25", "-123456789012.5"],
    ["SMALL", "0", "0", "1", "0", "0", "–", "0"],
    ["SMALLER", "0", "0", "–", "0", "0", "1", "0"],
    ["THIRD", "0", "0", "–", "0", "3", "1.3333", "-3"],
  ]);
});

test("a thousand averages on a half, each checked against decimal arithmetic", () => {
  // Fills of 1 at a and 1 at b, in ten-thousandths: a = 10000 + i, b = 10001 + i + 2k, so the average is
  // (20001 + 2i + 2k) / 2 ten-thousandths = 1.xxxx5 exactly, and away from zero is the next ten-thousandth.
  const lines = [];
  const expected = [];
  let n = 0;
  for (let i = 0; i < 1000; i++) {
    const k = i % 7;
    const a = 10000 + i;
    const b = 10001 + i + 2 * k;
    const symbol = `S${String(i).padStart(4, "0")}`;
    lines.push(fill(++n, symbol, 1, 1, (a / 10000).toFixed(4)), fill(++n, symbol, 1, 1, (b / 10000).toFixed(4)));
    const up = (a + b + 1) / 2; // in ten-thousandths, a whole number
    expected.push([symbol, String(Number(`${Math.floor(up / 10000)}.${String(up % 10000).padStart(4, "0")}`))]);
  }
  draw(lines);
  expect(rows().map((r) => [r[0], r[3]])).toEqual(expected);
});
