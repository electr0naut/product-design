// @vitest-environment jsdom
// FXL-15: the story of one order (PRD v1.2 US-007; design v1.2 sections 8.2 and 12). Runs from the repo root.
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
const cli = (seq, type, extra) => fixmsg("FIX.4.4", [[35, type], [49, "CLIENT"], [56, "BROKER"], [34, seq], ...extra]);
const brk = (seq, extra) => fixmsg("FIX.4.4", [[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, seq], ...extra]);
// Order 1: C1/O1, filled. Order 2: C2 replaced by C3, O2, with a gap on the broker side. Then a heartbeat and a bad line.
const LOG = [
  cli(1, "D", [[11, "C1"], [54, "1"], [38, "500"], [55, "VOD.L"], [44, "71.25"], [40, "2"]]),
  brk(1, [[11, "C1"], [37, "O1"], [17, "E1"], [150, "0"], [39, "0"], [14, "0"], [6, "0"]]),
  cli(2, "D", [[11, "C2"], [54, "2"], [38, "200"], [55, "BARC.L"], [40, "1"]]),
  brk(2, [[11, "C1"], [37, "O1"], [17, "E2"], [150, "F"], [39, "2"], [14, "500"], [6, "71.25"], [32, "500"], [31, "71.25"]]),
  cli(3, "G", [[11, "C3"], [41, "C2"], [54, "2"], [38, "300"], [55, "BARC.L"], [40, "1"]]),
  brk(5, [[11, "C3"], [41, "C2"], [37, "O2"], [17, "E3"], [150, "5"], [39, "0"], [14, "0"], [6, "0"]]),
  cli(4, "0", []),
  "8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|",
  cli(5, "9", [[11, "C9"], [41, "C8"], [37, "NONE"]]),
].join("\n");
const calls = () => { const log = []; return { log, pick: (id) => log.push(["pick", id]), clear: () => log.push(["clear"]), setFilter: (k, v) => log.push(["setFilter", k, v]) }; };

test("render(result) alone still shows the whole log", () => {
  page();
  render(analyse(LOG));
  expect(all("#decode article").length).toBe(9);
  expect(q("#summary .order-story")).toBeNull();
});

test("order ids are buttons in the timeline and in the cards, and call pick with the id alone", () => {
  page();
  const h = calls();
  render(analyse(LOG), { orderId: null, filters: NOFILTER }, h);
  const replaced = all("#timeline li.event").find((li) => li.querySelector(".badge").textContent === "Replaced");
  const links = [...replaced.querySelectorAll("button.order-link")];
  expect(links.map((b) => b.textContent).sort()).toEqual(["ClOrdID C3", "OrderID O2", "OrigClOrdID C2"]);
  expect(links.every((b) => b.type === "button")).toBe(true);
  links.find((b) => b.textContent === "OrigClOrdID C2").click();
  links.find((b) => b.textContent === "OrderID O2").click();
  expect(h.log).toEqual([["pick", "C2"], ["pick", "O2"]]);
  const card = all("#decode article.card")[1];
  const cell = (tag) => [...card.querySelectorAll("table.fields tr")].find((tr) => tr.children[0].textContent === tag).children[2];
  expect(cell("11").querySelector("button.order-link").textContent).toBe("C1");
  expect(cell("37").querySelector("button.order-link").textContent).toBe("O1");
  expect(cell("17").querySelector("button")).toBeNull();
  cell("37").querySelector("button.order-link").click();
  expect(h.log.at(-1)).toEqual(["pick", "O1"]);
  expect(all("#timeline a, #decode a, #summary a").length).toBe(0);
});

test("an OrderID of NONE is plain text, not a button", () => {
  page();
  render(analyse(LOG), { orderId: null, filters: NOFILTER }, calls());
  const reject = all("#timeline li.event").find((li) => li.querySelector(".badge").textContent === "CancelReject");
  expect([...reject.querySelectorAll("button.order-link")].map((b) => b.textContent).sort()).toEqual(["ClOrdID C9", "OrigClOrdID C8"]);
  expect(reject.textContent).toContain("NONE");
  const card = all("#decode article.card").at(-1);
  const cell = [...card.querySelectorAll("table.fields tr")].find((tr) => tr.children[0].textContent === "37").children[2];
  expect(cell.textContent.trim()).toBe("NONE");
  expect(cell.querySelector("button")).toBeNull();
});

test("a selected order shows only its messages and events, with full-log numbers", () => {
  page();
  render(analyse(LOG), { orderId: "C2", filters: NOFILTER }, calls());
  expect(texts("#decode article .num")).toEqual(["#3", "#5", "#6"]);
  expect(texts("#timeline li.event .badge")).toEqual(["NewOrder", "ReplaceRequest", "SequenceGap", "Replaced"]);
  expect(q("#timeline li.event.gap .detail").textContent).toBe("expected 3, received 5");
  expect(all("#decode article.malformed").length).toBe(0);
});

test("the banner: ids, terms from the first NewOrder, state from the last ExecutionReport", () => {
  page();
  const h = calls();
  render(analyse(LOG), { orderId: "O1", filters: NOFILTER }, h);
  const b = q("#summary > .order-story");
  expect(q("#summary").firstElementChild).toBe(b);
  expect(b.querySelector("strong").textContent).toBe("C1 · O1");
  expect(b.querySelector(".order-terms").textContent).toBe("Buy 500 VOD.L @ 71.25 Limit");
  expect(b.querySelector(".order-state").textContent).toBe("Filled · 500 filled @ 71.25");
  const back = b.querySelector("button.show-all");
  expect([back.textContent, back.type]).toEqual(["Show all messages", "button"]);
  back.click();
  expect(h.log).toEqual([["clear"]]);
});

test("the banner of a replaced order: every id, no price, and a state without fills", () => {
  page();
  render(analyse(LOG), { orderId: "C3", filters: NOFILTER }, calls());
  const b = q("#summary .order-story");
  expect(b.querySelector("strong").textContent).toBe("C2 · C3 · O2");
  expect(b.querySelector(".order-terms").textContent).toBe("Sell 200 BARC.L Market");
  expect(b.querySelector(".order-state").textContent).toBe("New");
});

test("an order with no ExecutionReport has no state", () => {
  page();
  render(analyse(LOG), { orderId: "C9", filters: NOFILTER }, calls());
  expect(q("#summary .order-story strong").textContent).toBe("C9 · C8");
  expect(q("#summary .order-story .order-state")).toBeNull();
  expect(texts("#decode article .num")).toEqual(["#9"]);
});

test("the summary strip is narrowed while an order is selected", () => {
  page();
  render(analyse(LOG), { orderId: "C2", filters: NOFILTER }, calls());
  expect(texts("#summary .stats .stat")).toEqual(["3 of 9 messages", "1 sequence gap", "1 order"]);
  render(analyse(LOG), { orderId: null, filters: NOFILTER }, calls());
  expect(texts("#summary .stats .stat")).toEqual(["9 messages", "8 valid", "1 malformed", "1 sequence gap", "3 orders"]);
});

test("an order id that matches nothing shows the whole log without a banner", () => {
  page();
  render(analyse(LOG), { orderId: "nope", filters: NOFILTER }, calls());
  expect(all("#decode article").length).toBe(9);
  expect(q("#summary .order-story")).toBeNull();
});

test("on the page: click an id, show all, and Decode again clears the selection", async () => {
  await boot();
  q("#paste").value = LOG;
  q("#decode-button").click();
  expect(all("#decode article").length).toBe(9);
  all("#timeline button.order-link").find((b) => b.textContent === "OrderID O2").click();
  expect(texts("#decode article .num")).toEqual(["#3", "#5", "#6"]);
  expect(q("#summary .order-story strong").textContent).toBe("C2 · C3 · O2");
  q("#summary button.show-all").click();
  expect(all("#decode article").length).toBe(9);
  expect(q("#summary .order-story")).toBeNull();
  all("#decode button.order-link").find((b) => b.textContent === "C1").click();
  expect(texts("#decode article .num")).toEqual(["#1", "#2", "#4"]);
  q("#decode-button").click();
  expect(all("#decode article").length).toBe(9);
  expect(q("#summary .order-story")).toBeNull();
});

test("ids made of markup stay text and never become attributes", () => {
  const evil = "<img src=x onerror=alert(1)>";
  page();
  render(analyse(cli(1, "D", [[11, evil], [55, "X"], [54, "1"], [38, "1"]])), { orderId: evil, filters: NOFILTER }, calls());
  expect(document.querySelector("img")).toBeNull();
  expect(q("#summary .order-story strong").textContent).toBe(evil);
  for (const n of all("#summary *, #timeline *, #decode *")) {
    for (const a of n.attributes) expect(a.value.includes("<img"), `${n.tagName} ${a.name}`).toBe(false);
  }
});
