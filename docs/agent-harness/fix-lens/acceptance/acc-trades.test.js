// @vitest-environment jsdom
// FXL-16: the trading summary and the filters on the page (PRD v1.2 US-008, US-009; design v1.2 sections 8.2,
// 13 "Figures" and 14). The expected figures come from an independent Python implementation. Runs from the
// repo root.
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
const calls = () => { const log = []; return { log, pick: (id) => log.push(["pick", id]), clear: () => log.push(["clear"]), setFilter: (k, v) => log.push(["setFilter", k, v]) }; };
// Orders (35=D) go CLIENT to BROKER, everything else BROKER to CLIENT; each direction has its own sequence.
const textOf = (lines, begin = "FIX.4.4") => {
  const seq = { CLIENT: 0, BROKER: 0 };
  return lines.map((line) => {
    const f = line.trim().split(/\s+/).map((p) => p.split("="));
    const type = f.find(([t]) => t === "35")[1];
    const [from, to] = type === "D" ? ["CLIENT", "BROKER"] : ["BROKER", "CLIENT"];
    return fixmsg(begin, [[35, type], [49, from], [56, to], [34, ++seq[from]], ...f.filter(([t]) => t !== "35")]);
  }).join("\n");
};
const A = textOf([
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
]);
const rows = () => all("#summary .trades table.trade-table tr").filter((tr) => tr.querySelector("td"))
  .map((tr) => [...tr.children].map((td) => td.textContent.trim()));
const draw = (text, view = {}) => { page(); const h = calls(); render(analyse(text), { orderId: null, filters: NOFILTER, ...view }, h); return h; };
const selects = () => all("#summary .filters label.filter select");
const choose = (i, optionText) => {
  const sel = selects()[i];
  sel.selectedIndex = [...sel.options].findIndex((o) => o.textContent === optionText);
  sel.dispatchEvent(new Event("change", { bubbles: true }));
};

test("the summary holds the strip, then the trades, then the filters", () => {
  draw(A);
  const kids = [...q("#summary").children].map((n) => n.className.split(/\s+/)[0]);
  expect(kids).toEqual(["stats", "trades", "filters"]);
  draw(A, { orderId: "C1" });
  expect([...q("#summary").children].map((n) => n.className.split(/\s+/)[0])).toEqual(["order-story", "stats", "trades", "filters"]);
});

test("the trading table: heads and the figures of log A", () => {
  draw(A);
  expect(texts("#summary .trades table.trade-table th")).toEqual(["Symbol", "Buy orders", "Bought", "Avg buy", "Sell orders", "Sold", "Avg sell", "Net"]);
  expect(rows()).toEqual([
    ["AZN.L", "0", "10", "–", "0", "0", "–", "+10"],
    ["BARC.L", "0", "0", "–", "1", "50", "2.5", "-50"],
    ["VOD.L", "1", "300", "71.2", "1", "260", "72.2", "+40"],
  ]);
});

test("the notes: the fixed note, and the unmatched note in plural and singular", () => {
  draw(A);
  expect(texts("#summary .trades p.note")).toEqual([
    "Bought and sold are filled quantities from execution reports in this log, counted once per ExecID, after trade cancels and corrections.",
    "2 trade cancels or corrections refer to an execution that is not in this log.",
  ]);
  expect(q("#summary .trades p.note.unmatched").textContent.trim()).toBe("2 trade cancels or corrections refer to an execution that is not in this log.");
  draw(textOf(["35=D 11=C1 55=X 54=1 38=1", "35=8 37=O9 11=C9 17=E8 19=ZZ 150=H 55=X 54=1"]));
  expect(q("#summary .trades p.note.unmatched").textContent.trim()).toBe("1 trade cancel or correction refers to an execution that is not in this log.");
  draw(textOf(["35=D 11=C1 55=X 54=1 38=1"]));
  expect(q("#summary .trades p.note.unmatched")).toBeNull();
  expect(texts("#summary .trades p.note").length).toBe(1);
});

test("figures: four decimals at most, no trailing zeros, no thousands separator, zero net without a sign", () => {
  draw(textOf([
    "35=8 37=O1 17=E1 150=F 55=BIG 54=1 32=1500000 31=1234.56789",
    "35=8 37=O2 17=E2 150=F 55=FRAC 54=1 32=0.1 31=1",
    "35=8 37=O2 17=E3 150=F 55=FRAC 54=1 32=0.2 31=2",
    "35=8 37=O3 17=E4 150=F 55=FRAC 54=2 32=0.3 31=3",
    "35=8 37=O4 17=E5 150=F 55=THIRD 54=2 32=1 31=1",
    "35=8 37=O4 17=E6 150=F 55=THIRD 54=2 32=2 31=1.5",
  ]));
  expect(rows()).toEqual([
    ["BIG", "0", "1500000", "1234.5679", "0", "0", "–", "+1500000"],
    ["FRAC", "0", "0.3", "1.6667", "0", "0.3", "3", "0"],
    ["THIRD", "0", "0", "–", "0", "3", "1.3333", "-3"],
  ]);
});

test("no orders and no fills: the empty text and no table", () => {
  draw(fixmsg("FIX.4.4", [[35, "0"], [49, "A"], [56, "B"], [34, "1"]]));
  expect(q("#summary .trades p.empty").textContent).toBe("No orders or fills in the messages shown.");
  expect(q("#summary .trades table")).toBeNull();
});

test("five filters with their labels, All first, values in plain order, disabled when empty", () => {
  draw(A);
  expect(texts("#summary .filters label.filter > span")).toEqual(["Account", "SenderCompID", "SenderSubID", "TargetCompID", "TargetSubID"]);
  const opts = selects().map((s) => [...s.options].map((o) => o.textContent));
  expect(opts).toEqual([["All", "ACC1", "ACC2"], ["All", "BROKER", "CLIENT"], ["All"], ["All", "BROKER", "CLIENT"], ["All"]]);
  expect(selects().map((s) => s.disabled)).toEqual([false, false, true, false, true]);
  expect(selects().map((s) => s.selectedIndex)).toEqual([0, 0, 0, 0, 0]);
  expect(q("#summary .filters button.clear-filters")).toBeNull();
});

test("changing a select calls setFilter with the value, or null for All", () => {
  const h = draw(A);
  choose(0, "ACC2");
  choose(1, "CLIENT");
  choose(1, "All");
  expect(h.log).toEqual([["setFilter", "account", "ACC2"], ["setFilter", "senderCompId", "CLIENT"], ["setFilter", "senderCompId", null]]);
});

test("a set filter is the selected option, and Clear filters appears and calls setFilter(null, null)", () => {
  const h = draw(A, { filters: { ...NOFILTER, account: "ACC2", targetCompId: "CLIENT" } });
  expect(selects().map((s) => s.options[s.selectedIndex].textContent)).toEqual(["ACC2", "All", "All", "CLIENT", "All"]);
  const clear = q("#summary .filters button.clear-filters");
  expect([clear.textContent, clear.type]).toEqual(["Clear filters", "button"]);
  clear.click();
  expect(h.log).toEqual([["setFilter", null, null]]);
});

test("the Account filter narrows the cards, the timeline, the strip and the trading summary", () => {
  draw(A, { filters: { ...NOFILTER, account: "ACC2" } });
  expect(texts("#decode article .num")).toEqual(["#7", "#8", "#9", "#10"]);
  expect(texts("#timeline li.event .badge")).toEqual(["NewOrder", "Fill", "TradeCorrect", "TradeCorrect"]);
  expect(texts("#summary .stats .stat")).toEqual(["4 of 19 messages", "0 sequence gaps", "1 order"]);
  expect(rows()).toEqual([["VOD.L", "0", "0", "–", "1", "260", "72.2", "-260"]]);
  expect(q("#summary .trades p.note.unmatched")).toBeNull();
});

test("nothing passes: the empty text, and malformed cards are hidden while a filter is set", () => {
  const bad = "8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|";
  draw(A + "\n" + bad);
  expect(all("#decode article.malformed").length).toBe(1);
  draw(A + "\n" + bad, { filters: { ...NOFILTER, account: "ACC1", senderCompId: "nobody" } });
  expect(all("#decode article").length).toBe(0);
  expect(q("#decode p.empty").textContent).toBe("No messages match the current filters.");
  expect(texts("#summary .stats .stat")[0]).toBe("0 of 20 messages");
});

test("a filter and a selected order apply together", () => {
  draw(A, { orderId: "C1", filters: { ...NOFILTER, senderCompId: "BROKER" } });
  expect(texts("#decode article .num")).toEqual(["#2", "#3", "#4", "#5", "#6", "#18"]);
  expect(rows()).toEqual([["VOD.L", "0", "300", "71.2", "0", "0", "–", "+300"]]);
});

test("filtering never changes a result: gaps keep their detail and no gap is invented", () => {
  const cli = (seq) => fixmsg("FIX.4.4", [[35, "0"], [49, "CLIENT"], [56, "BROKER"], [34, seq]]);
  const brk = (seq) => fixmsg("FIX.4.4", [[35, "0"], [49, "BROKER"], [56, "CLIENT"], [34, seq]]);
  const text = [cli(1), brk(1), cli(2), brk(2), cli(5), brk(3)].join("\n");
  draw(text, { filters: { ...NOFILTER, senderCompId: "CLIENT" } });
  expect(texts("#timeline li.event .badge")).toEqual(["Heartbeat", "Heartbeat", "SequenceGap", "Heartbeat"]);
  expect(q("#timeline li.event.gap .detail").textContent).toBe("expected 3, received 5");
  draw(text, { filters: { ...NOFILTER, senderCompId: "BROKER" } });
  expect(texts("#timeline li.event .badge")).toEqual(["Heartbeat", "Heartbeat", "Heartbeat"]);
  expect(texts("#decode article .num")).toEqual(["#2", "#4", "#6"]);
});

test("on the page: choose a filter, clear it, and Decode again resets the filters", async () => {
  await boot();
  q("#paste").value = A;
  q("#decode-button").click();
  expect(all("#decode article").length).toBe(19);
  choose(0, "ACC2");
  expect(texts("#decode article .num")).toEqual(["#7", "#8", "#9", "#10"]);
  expect(selects()[0].options[selects()[0].selectedIndex].textContent).toBe("ACC2");
  choose(1, "BROKER");
  expect(texts("#decode article .num")).toEqual(["#8", "#9", "#10"]);
  q("#summary .filters button.clear-filters").click();
  expect(all("#decode article").length).toBe(19);
  expect(q("#summary .filters button.clear-filters")).toBeNull();
  choose(0, "ACC1");
  expect(all("#decode article").length).toBeLessThan(19);
  q("#decode-button").click();
  expect(all("#decode article").length).toBe(19);
  expect(selects().map((s) => s.selectedIndex)).toEqual([0, 0, 0, 0, 0]);
});

test("option texts made of markup stay text, and option values never hold pasted text", () => {
  const evil = "<img src=x onerror=alert(1)>";
  draw(fixmsg("FIX.4.4", [[35, "D"], [49, evil], [56, "B"], [34, "1"], [1, evil], [11, "C1"], [55, "X"], [54, "1"], [38, "1"]]));
  expect(document.querySelector("img")).toBeNull();
  expect([...selects()[0].options].map((o) => o.textContent)).toEqual(["All", evil]);
  for (const n of all("#summary *")) for (const a of n.attributes) expect(a.value.includes("<img"), `${n.tagName} ${a.name}`).toBe(false);
});
