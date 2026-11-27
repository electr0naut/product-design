// @vitest-environment jsdom
// FXL-21: paging on the page (PRD v1.3 US-010, AC-057 to AC-062; design v1.3 section 16). The logs are built
// here and every expected number was worked out from how they are built. Runs from the repo root.
import { test, expect, vi } from "vitest";
import { readFileSync } from "node:fs";
import { analyse } from "../src/analyse.js";
import { render } from "../src/render.js";

const S = "\x01";
const enc = new TextEncoder();
function fixmsg(fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=FIX.4.4${S}9=${enc.encode(body).length}${S}`;
  let sum = 0;
  for (const b of enc.encode(head + body)) sum += b;
  return (head + body + `10=${String(sum % 256).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
const HTML = readFileSync("index.html", "utf8");
const CSS = readFileSync("styles.css", "utf8");
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
const view = (pageNumber, filters = {}, orderId = null) => ({ orderId, filters, page: pageNumber });
const draw = (result, v, handlers) => { page(); render(result, v, handlers); };
const labels = () => texts("nav.pager span.page-info");
const cardNums = () => texts("#decode > article.card .card-head .num");
const rowNums = () => texts("#timeline li.event .num");
const range = (a, b) => Array.from({ length: b - a + 1 }, (_, i) => `#${a + i}`);
const TIME = "20261127-10:00:00";
const beat = (from, to, seq) => fixmsg([[35, "0"], [49, from], [56, to], [34, seq], [52, TIME]]);

// n heartbeats from A to B, MsgSeqNum 1 to n: one timeline row each and no sequence gap
const beats = (n) => Array.from({ length: n }, (_, i) => beat("A", "B", i + 1)).join("\n");
const R200 = analyse(beats(200));
const R201 = analyse(beats(201));
const R450 = analyse(beats(450));

test("a log of 200 messages is shown whole, with no pager", () => {
  draw(R200);
  expect(all("#decode > article.card").length).toBe(200);
  expect(all("#timeline li.event").length).toBe(200);
  expect(all("nav.pager").length).toBe(0);
  expect(all(".pager, .page-info, .page-first, .page-prev, .page-next, .page-last").length).toBe(0);
  draw(R200, view(2));
  expect(cardNums()).toEqual(range(1, 200));
  expect(all("nav.pager").length).toBe(0);
});

test("a log of 201 messages has two pages: 200 cards, then one", () => {
  draw(R201);
  expect(cardNums()).toEqual(range(1, 200));
  expect(all("nav.pager").length).toBe(2);
  expect(labels()).toEqual(["Messages 1 to 200 of 201", "Messages 1 to 200 of 201"]);
  draw(R201, view(2));
  expect(cardNums()).toEqual(["#201"]);
  expect(rowNums()).toEqual(["#201"]);
  expect(labels()).toEqual(["Messages 201 to 201 of 201", "Messages 201 to 201 of 201"]);
});

test("the two pagers: last in #summary after the filters, last in #decode after the cards", () => {
  draw(R450, view(2));
  const pagers = all("nav.pager");
  expect(pagers.length).toBe(2);
  const top = q("#summary").lastElementChild;
  expect(top).toBe(pagers[0]);
  expect(top.parentElement.id).toBe("summary");
  expect(top.previousElementSibling.matches("div.filters")).toBe(true);
  const bottom = q("#decode").lastElementChild;
  expect(bottom).toBe(pagers[1]);
  expect(bottom.previousElementSibling.matches("article.card")).toBe(true);
  expect(q("#decode").firstElementChild.matches("h2")).toBe(true);
  expect(all("#timeline nav, #timeline .pager").length).toBe(0);
});

test("each pager holds the page line and four buttons, in order, and nothing else", () => {
  draw(R450, view(2));
  expect(all("nav.pager").length).toBe(2);
  for (const pager of all("nav.pager")) {
    expect([...pager.children].map((n) => `${n.tagName.toLowerCase()}.${n.className}`)).toEqual([
      "span.page-info", "button.page-first", "button.page-prev", "button.page-next", "button.page-last",
    ]);
    expect([...pager.querySelectorAll("button")].map((b) => b.textContent)).toEqual(["First", "Previous", "Next", "Last"]);
    expect([...pager.querySelectorAll("button")].map((b) => b.type)).toEqual(["button", "button", "button", "button"]);
    expect(pager.querySelector("span.page-info").children.length).toBe(0);
    expect(pager.querySelectorAll("a").length).toBe(0);
  }
});

test("450 messages: the page line and the cards of pages 1, 2 and 3", () => {
  draw(R450, view(1));
  expect(labels()).toEqual(["Messages 1 to 200 of 450", "Messages 1 to 200 of 450"]);
  expect(cardNums()).toEqual(range(1, 200));
  draw(R450, view(2));
  expect(labels()).toEqual(["Messages 201 to 400 of 450", "Messages 201 to 400 of 450"]);
  expect(cardNums()).toEqual(range(201, 400));
  draw(R450, view(3));
  expect(labels()).toEqual(["Messages 401 to 450 of 450", "Messages 401 to 450 of 450"]);
  expect(cardNums()).toEqual(range(401, 450));
});

test("First and Previous are disabled on page 1, Next and Last on the last page", () => {
  const disabled = () => all("nav.pager").map((p) => [...p.querySelectorAll("button")].map((b) => b.disabled));
  draw(R450, view(1));
  expect(disabled()).toEqual([[true, true, false, false], [true, true, false, false]]);
  draw(R450, view(2));
  expect(disabled()).toEqual([[false, false, false, false], [false, false, false, false]]);
  draw(R450, view(3));
  expect(disabled()).toEqual([[false, false, true, true], [false, false, true, true]]);
});

test("the buttons of both pagers call handlers.setPage with a page number", () => {
  const log = [];
  const handlers = { pick() {}, clear() {}, setFilter() {}, setPage: (n) => log.push(n) };
  draw(R450, view(2), handlers);
  for (const pager of all("nav.pager")) {
    for (const cls of ["page-first", "page-prev", "page-next", "page-last"]) pager.querySelector(`button.${cls}`).click();
  }
  expect(log).toEqual([1, 1, 3, 3, 1, 1, 3, 3]);
  log.length = 0;
  draw(R450, view(1), handlers);
  q("#summary nav.pager button.page-next").click();
  q("#decode nav.pager button.page-last").click();
  expect(log).toEqual([2, 3]);
  log.length = 0;
  draw(R450, view(3), handlers);
  q("#decode nav.pager button.page-prev").click();
  q("#summary nav.pager button.page-first").click();
  expect(log).toEqual([2, 1]);
});

test("a page that does not exist is made valid, and a missing page is page 1", () => {
  draw(R450, view(99));
  expect(labels()[0]).toBe("Messages 401 to 450 of 450");
  expect(cardNums()).toEqual(range(401, 450));
  for (const v of [view(0), view(-2), { orderId: null, filters: {} }, undefined]) {
    draw(R450, v);
    expect(labels()[0]).toBe("Messages 1 to 200 of 450");
    expect(cardNums().slice(0, 2)).toEqual(["#1", "#2"]);
  }
});

test("the timeline shows the events of the messages on the page, and no others", () => {
  draw(R450, view(1));
  expect(rowNums()).toEqual(range(1, 200));
  draw(R450, view(2));
  expect(rowNums()).toEqual(range(201, 400));
  draw(R450, view(3));
  expect(rowNums()).toEqual(range(401, 450));
});

// 450 heartbeats; message 201 jumps from MsgSeqNum 200 to 205, so it has two events: a SequenceGap and its own
const GAP_AT_201 = analyse(Array.from({ length: 450 }, (_, i) => beat("A", "B", i < 200 ? i + 1 : i + 5)).join("\n"));

test("both events of a message are on its page: a sequence gap follows its message", () => {
  expect(GAP_AT_201.timeline.filter((e) => e.name === "SequenceGap").map((e) => e.number)).toEqual([201]);
  draw(GAP_AT_201, view(1));
  expect(all("#timeline li.event.gap").length).toBe(0);
  expect(all("#timeline li.event").length).toBe(200);
  expect(texts("#summary .stat")).toContain("1 sequence gap");
  draw(GAP_AT_201, view(2));
  expect(texts("#timeline li.event.gap .num")).toEqual(["#201"]);
  expect(all("#timeline li.event").length).toBe(201);
  expect(cardNums()).toEqual(range(201, 400));
  expect(texts("#summary .stat")).toContain("1 sequence gap");
});

// 250 messages of which the third is malformed (its CheckSum is wrong). The valid ones carry MsgSeqNum 1 to
// 249 without a gap.
function withMalformedThird(n) {
  const rows = [];
  let seq = 0;
  for (let i = 1; i <= n; i++) {
    if (i === 3) rows.push(beat("A", "B", 999).replace(/10=(\d{3})\|$/, (_, c) => `10=${c === "000" ? "001" : "000"}|`));
    else rows.push(beat("A", "B", ++seq));
  }
  return analyse(rows.join("\n"));
}

test("malformed messages count, at their place in the log", () => {
  const r = withMalformedThird(250);
  expect([r.decoded.length, r.errors.length, r.errors[0].number]).toEqual([249, 1, 3]);
  draw(r, view(1));
  expect(labels()).toEqual(["Messages 1 to 200 of 250", "Messages 1 to 200 of 250"]);
  const cards = all("#decode > article.card");
  expect(cards.length).toBe(200);
  expect(cards.map((c, i) => (c.classList.contains("malformed") ? i : -1)).filter((i) => i >= 0)).toEqual([2]);
  expect(cardNums()).toEqual(range(1, 200));
  expect(rowNums()).toEqual([...range(1, 2), ...range(4, 200)]);
  draw(r, view(2));
  expect(labels()[0]).toBe("Messages 201 to 250 of 250");
  expect(cardNums()).toEqual(range(201, 250));
  expect(rowNums()).toEqual(range(201, 250));
});

test("a malformed message alone on the last page", () => {
  const rows = Array.from({ length: 200 }, (_, i) => beat("A", "B", i + 1));
  rows.push("8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|");
  const r = analyse(rows.join("\n"));
  expect([r.decoded.length, r.errors.length]).toEqual([200, 1]);
  draw(r, view(1));
  expect(labels()[0]).toBe("Messages 1 to 200 of 201");
  expect(all("#decode > article.card.malformed").length).toBe(0);
  draw(r, view(2));
  expect(labels()[0]).toBe("Messages 201 to 201 of 201");
  expect(all("#decode > article.card").length).toBe(1);
  expect(all("#decode > article.card.malformed").length).toBe(1);
  expect(all("#timeline li.event").length).toBe(0);
});

// 450 heartbeats in blocks of nine: five from A to B, then four from C to D. 250 have SenderCompID A and 200
// have C. The n-th message from A in block b (from 0) at place o (from 0) is message 9b + o + 1.
const MIXED = analyse(Array.from({ length: 450 }, (_, i) => {
  const b = Math.floor(i / 9);
  const o = i % 9;
  return o < 5 ? beat("A", "B", b * 5 + o + 1) : beat("C", "D", b * 4 + (o - 5) + 1);
}).join("\n"));
const numbersOfA = Array.from({ length: 250 }, (_, k) => `#${9 * Math.floor(k / 5) + (k % 5) + 1}`);

test("with a filter set the pages run over the messages shown, and the line says so", () => {
  expect(MIXED.timeline.filter((e) => e.name === "SequenceGap").length).toBe(0);
  draw(MIXED, view(1, { senderCompId: "A" }));
  expect(labels()).toEqual(["Messages 1 to 200 of 250 shown", "Messages 1 to 200 of 250 shown"]);
  expect(cardNums()).toEqual(numbersOfA.slice(0, 200));
  expect(cardNums()[199]).toBe("#356");
  expect(rowNums()).toEqual(numbersOfA.slice(0, 200));
  expect(texts("#summary .stat")[0]).toBe("250 of 450 messages");
  draw(MIXED, view(2, { senderCompId: "A" }));
  expect(labels()).toEqual(["Messages 201 to 250 of 250 shown", "Messages 201 to 250 of 250 shown"]);
  expect(cardNums()).toEqual(numbersOfA.slice(200));
  expect([cardNums()[0], cardNums()[49]]).toEqual(["#361", "#446"]);
  expect(rowNums()).toEqual(numbersOfA.slice(200));
  expect(texts("#summary .stat")[0]).toBe("250 of 450 messages");
  draw(MIXED, view(9, { senderCompId: "A" }));
  expect(labels()[0]).toBe("Messages 201 to 250 of 250 shown");
});

test("a filter that leaves 200 messages or fewer shows no pager", () => {
  draw(MIXED, view(1, { senderCompId: "C" }));
  expect(all("#decode > article.card").length).toBe(200);
  expect(all("nav.pager").length).toBe(0);
  draw(MIXED, view(2, { senderCompId: "C" }));
  expect(all("#decode > article.card").length).toBe(200);
  expect(all("nav.pager").length).toBe(0);
  draw(MIXED, view(1, { senderCompId: "NOBODY" }));
  expect(q("#decode p.empty").textContent).toBe("No messages match the current filters.");
  expect(all("nav.pager").length).toBe(0);
  draw(MIXED, view(1));
  expect(labels()[0]).toBe("Messages 1 to 200 of 450");
});

// One order of 250 messages (a NewOrder and 249 fills of 1 at 10) with 200 heartbeats of another session in
// between: after every five order messages come four heartbeats. 450 messages in all.
function orderLog() {
  const rows = [];
  let k = 0;
  let cli = 0;
  let brk = 0;
  let hb = 0;
  for (let i = 0; i < 450; i++) {
    if (i % 9 < 5) {
      if (k === 0) rows.push(fixmsg([[35, "D"], [49, "CLIENT"], [56, "BROKER"], [34, ++cli], [52, TIME], [11, "C1"], [1, "ACC1"], [55, "VOD.L"], [54, 1], [38, 1000], [40, 2], [44, 10]]));
      else rows.push(fixmsg([[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, ++brk], [52, TIME], [37, "O1"], [11, "C1"], [17, `E${k}`], [150, "F"], [39, 1], [55, "VOD.L"], [54, 1], [32, 1], [31, 10], [14, k], [6, 10], [151, 1000 - k]]));
      k++;
    } else {
      rows.push(beat("A", "B", ++hb));
    }
  }
  return rows.join("\n");
}
const ORDER_TEXT = orderLog();
const ORDER = analyse(ORDER_TEXT);

test("with an order selected the pages run over its messages, and the banner is the same on every page", () => {
  expect([ORDER.decoded.length, ORDER.errors.length]).toEqual([450, 0]);
  draw(ORDER, view(1, {}, "C1"));
  expect(labels()).toEqual(["Messages 1 to 200 of 250 shown", "Messages 1 to 200 of 250 shown"]);
  expect(cardNums()).toEqual(numbersOfA.slice(0, 200));
  const banner = q("#summary .order-story").textContent;
  const stats = texts("#summary .stat");
  expect(stats[0]).toBe("250 of 450 messages");
  expect(banner).toContain("C1");
  expect(q("#summary").firstElementChild.matches("div.order-story")).toBe(true);
  expect(q("#summary").lastElementChild.matches("nav.pager")).toBe(true);
  draw(ORDER, view(2, {}, "C1"));
  expect(labels()).toEqual(["Messages 201 to 250 of 250 shown", "Messages 201 to 250 of 250 shown"]);
  expect(cardNums()).toEqual(numbersOfA.slice(200));
  expect(rowNums()).toEqual(numbersOfA.slice(200));
  expect(q("#summary .order-story").textContent).toBe(banner);
  expect(texts("#summary .stat")).toEqual(stats);
});

// 450 messages: message 1 is a NewOrder (buy 1,000 VOD.L), message 300 a fill of 400 at 71.25 and message 450
// a fill of 100 at 72; the rest are heartbeats from A to B, with one jump in MsgSeqNum at message 420.
// Bought 500, average (400 x 71.25 + 100 x 72) / 500 = 71.4.
function spreadLog() {
  const rows = [];
  let hb = 0;
  for (let i = 1; i <= 450; i++) {
    if (i === 1) rows.push(fixmsg([[35, "D"], [49, "CLIENT"], [56, "BROKER"], [34, 1], [52, TIME], [11, "C1"], [1, "ACC1"], [55, "VOD.L"], [54, 1], [38, 1000], [40, 2], [44, 72]]));
    else if (i === 300) rows.push(fixmsg([[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, 1], [52, TIME], [37, "O1"], [11, "C1"], [17, "E1"], [150, "F"], [39, 1], [55, "VOD.L"], [54, 1], [32, 400], [31, 71.25], [14, 400], [6, 71.25], [151, 600]]));
    else if (i === 450) rows.push(fixmsg([[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, 2], [52, TIME], [37, "O1"], [11, "C1"], [17, "E2"], [150, "F"], [39, 1], [55, "VOD.L"], [54, 1], [32, 100], [31, 72], [14, 500], [6, 71.4], [151, 500]]));
    else { hb += i === 420 ? 5 : 1; rows.push(beat("A", "B", hb)); }
  }
  return rows.join("\n");
}
const SPREAD = analyse(spreadLog());
const snapshot = () => ({
  stats: texts("#summary div.stats span.stat"),
  trades: all("#summary table.trade-table tbody tr").map((tr) => [...tr.cells].map((c) => c.textContent)),
  notes: texts("#summary div.trades p"),
  filters: all("#summary div.filters label.filter").map((l) => [l.querySelector("span").textContent, l.querySelector("select").disabled, ...[...l.querySelectorAll("option")].map((o) => o.textContent)]),
});

test("the summary strip, the trading summary and the filter lists are those of the whole log on every page", () => {
  draw(SPREAD, view(1));
  const first = snapshot();
  expect(first.stats).toEqual(["450 messages", "450 valid", "0 malformed", "1 sequence gap", "1 order"]);
  expect(first.trades).toEqual([["VOD.L", "1", "500", "71.4", "0", "0", "–", "+500"]]);
  expect(first.filters.map((f) => f.slice(2))).toEqual([["All", "ACC1"], ["All", "A", "BROKER", "CLIENT"], ["All"], ["All", "B", "BROKER", "CLIENT"], ["All"]]);
  expect(all("#timeline li.event.gap").length).toBe(0);
  expect(cardNums()).toEqual(range(1, 200));
  draw(SPREAD, view(2));
  expect(snapshot()).toEqual(first);
  expect(cardNums()).toEqual(range(201, 400));
  expect(all("#timeline li.event.gap").length).toBe(0);
  draw(SPREAD, view(3));
  expect(snapshot()).toEqual(first);
  expect(cardNums()).toEqual(range(401, 450));
  expect(texts("#timeline li.event.gap .num")).toEqual(["#420"]);
});

test("with a filter set the trading summary is that of the whole filtered log on every page", () => {
  // SenderCompID A keeps the 447 heartbeats: no order and no fill is shown, on any page
  draw(SPREAD, view(1, { senderCompId: "A" }));
  const first = snapshot();
  expect(first.stats[0]).toBe("447 of 450 messages");
  expect(first.trades).toEqual([]);
  expect(q("#summary div.trades p.empty").textContent).toBe("No orders or fills in the messages shown.");
  expect(labels()[0]).toBe("Messages 1 to 200 of 447 shown");
  draw(SPREAD, view(3, { senderCompId: "A" }));
  expect(snapshot()).toEqual(first);
  expect(labels()[0]).toBe("Messages 401 to 447 of 447 shown");
  expect(all("#decode > article.card").length).toBe(47);
});

test("10,000 messages: only one page of cards and timeline rows is built", () => {
  const big = analyse(beats(10000));
  expect([big.ok, big.decoded.length]).toEqual([true, 10000]);
  draw(big);
  expect(labels()).toEqual(["Messages 1 to 200 of 10,000", "Messages 1 to 200 of 10,000"]);
  expect(all("#decode > article.card").length).toBe(200);
  expect(all("#timeline li.event").length).toBe(200);
  expect(texts("#summary .stat")[0]).toBe("10000 messages");
  draw(big, view(50));
  expect(labels()).toEqual(["Messages 9,801 to 10,000 of 10,000", "Messages 9,801 to 10,000 of 10,000"]);
  expect(cardNums()).toEqual(range(9801, 10000));
  expect(rowNums()).toEqual(range(9801, 10000));
});

// ---- src/main.js, through the page ----
const press = (sel) => q(sel).click();
const choose = (labelText, optionText) => {
  const sel = all("#summary div.filters label.filter").find((l) => l.querySelector("span").textContent === labelText).querySelector("select");
  sel.selectedIndex = [...sel.options].findIndex((o) => o.textContent === optionText);
  sel.dispatchEvent(new Event("change", { bubbles: true }));
};
async function decoded(text) {
  await boot();
  q("#paste").value = text;
  press("#decode-button");
}

test("main.js: the page buttons move through the pages and bring the results back into view", async () => {
  await decoded(beats(450));
  expect(labels()).toEqual(["Messages 1 to 200 of 450", "Messages 1 to 200 of 450"]);
  let scrolls = 0;
  const results = q(".results");
  results.scrollIntoView = () => { scrolls += 1; };
  press("#summary nav.pager button.page-next");
  expect(labels()).toEqual(["Messages 201 to 400 of 450", "Messages 201 to 400 of 450"]);
  expect(cardNums()).toEqual(range(201, 400));
  expect(scrolls).toBe(1);
  expect(q(".results")).toBe(results);
  press("#decode nav.pager button.page-last");
  expect(labels()[0]).toBe("Messages 401 to 450 of 450");
  expect(cardNums()).toEqual(range(401, 450));
  expect(scrolls).toBe(2);
  press("#decode nav.pager button.page-prev");
  expect(labels()[0]).toBe("Messages 201 to 400 of 450");
  press("#summary nav.pager button.page-first");
  expect(labels()[0]).toBe("Messages 1 to 200 of 450");
  expect(rowNums()).toEqual(range(1, 200));
  expect(scrolls).toBe(4);
});

test("main.js: where the results have no scrollIntoView, changing the page still works", async () => {
  await decoded(beats(450));
  q(".results").scrollIntoView = undefined;
  // an error thrown inside a click listener does not reach click(); jsdom reports it on the window
  const errors = [];
  const onError = (event) => { errors.push(String(event.message ?? event)); event.preventDefault?.(); };
  window.addEventListener("error", onError);
  try {
    press("#summary nav.pager button.page-next");
    expect(labels()[0]).toBe("Messages 201 to 400 of 450");
    press("#decode nav.pager button.page-last");
    expect(labels()[0]).toBe("Messages 401 to 450 of 450");
  } finally {
    window.removeEventListener("error", onError);
  }
  expect(errors).toEqual([]);
});

test("main.js: choosing, changing and clearing a filter each go back to page 1", async () => {
  await decoded(ORDER_TEXT);
  press("#summary nav.pager button.page-next");
  expect(labels()[0]).toBe("Messages 201 to 400 of 450");
  choose("SenderCompID", "BROKER");
  expect(labels()[0]).toBe("Messages 1 to 200 of 249 shown");
  expect(cardNums()[0]).toBe("#2");
  press("#decode nav.pager button.page-next");
  expect(labels()[0]).toBe("Messages 201 to 249 of 249 shown");
  choose("TargetCompID", "CLIENT");
  expect(labels()[0]).toBe("Messages 1 to 200 of 249 shown");
  press("#summary nav.pager button.page-last");
  expect(labels()[0]).toBe("Messages 201 to 249 of 249 shown");
  press("#summary .filters button.clear-filters");
  expect(labels()[0]).toBe("Messages 1 to 200 of 450");
  expect(cardNums()[0]).toBe("#1");
});

test("main.js: picking an order, returning to all messages and decoding again each go back to page 1", async () => {
  await decoded(ORDER_TEXT);
  press("#summary nav.pager button.page-next");
  expect(labels()[0]).toBe("Messages 201 to 400 of 450");
  all("#decode button.order-link").find((b) => b.textContent === "C1").click();
  expect(labels()[0]).toBe("Messages 1 to 200 of 250 shown");
  expect(cardNums()[0]).toBe("#1");
  press("#decode nav.pager button.page-next");
  expect(labels()[0]).toBe("Messages 201 to 250 of 250 shown");
  press("#summary button.show-all");
  expect(labels()[0]).toBe("Messages 1 to 200 of 450");
  expect(cardNums()[0]).toBe("#1");
  press("#summary nav.pager button.page-last");
  expect(labels()[0]).toBe("Messages 401 to 450 of 450");
  press("#decode-button");
  expect(labels()[0]).toBe("Messages 1 to 200 of 450");
  expect(cardNums()).toEqual(range(1, 200));
});

test("main.js: a second decode of a short log leaves no pager behind", async () => {
  await decoded(beats(450));
  press("#summary nav.pager button.page-last");
  q("#paste").value = beats(3);
  press("#decode-button");
  expect(all("nav.pager").length).toBe(0);
  expect(cardNums()).toEqual(["#1", "#2", "#3"]);
});

// ---- styles.css ----
const css = CSS.replace(/\/\*[\s\S]*?\*\//g, "");
// the declarations of every rule whose selector list names the selector, merged
function declarations(selector) {
  const out = {};
  for (const m of css.matchAll(/([^{}]+)\{([^{}]*)\}/g)) {
    const selectors = m[1].split(",").map((s) => s.trim().replace(/\s+/g, " "));
    if (!selectors.includes(selector)) continue;
    for (const d of m[2].split(";")) {
      const at = d.indexOf(":");
      if (at > 0) out[d.slice(0, at).trim().toLowerCase()] = d.slice(at + 1).trim().replace(/\s+/g, " ").toLowerCase();
    }
  }
  return out;
}

test("styles: the pager is a wrapping row, its buttons are quiet, a disabled one is muted", () => {
  const pager = declarations(".pager");
  expect([pager.display, pager["flex-wrap"]]).toEqual(["flex", "wrap"]);
  const button = declarations(".pager button");
  expect([button.background ?? button["background-color"], button.color]).toEqual(["var(--panel)", "var(--ink)"]);
  expect(declarations(".pager button:disabled").color).toBe("var(--muted)");
});
