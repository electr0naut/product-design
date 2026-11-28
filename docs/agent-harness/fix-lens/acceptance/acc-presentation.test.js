// @vitest-environment jsdom
// FXL-14: the presentation (PRD v1.2 US-006, AC-024; design v1.2 section 8). It expects to run from the repo
// root. Order ids are checked by their text only, so these tests hold whether an id is plain text or a button.
import { test, expect, vi } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
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
const CSS = readFileSync("styles.css", "utf8");
const page = () => { document.documentElement.innerHTML = HTML.replace(/^[\s\S]*?<html[^>]*>/i, "").replace(/<\/html>[\s\S]*$/i, ""); };
async function boot(dark = false) {
  page();
  window.matchMedia = () => ({ matches: dark, media: "", onchange: null, addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent() { return false; } });
  vi.resetModules();
  await import("../src/main.js");
}
const q = (sel) => document.querySelector(sel);
const all = (sel) => [...document.querySelectorAll(sel)];
const texts = (sel) => all(sel).map((n) => n.textContent.trim());
const show = (text) => { page(); render(analyse(text)); };

const NEW = fixmsg("FIX.4.4", [[35, "D"], [49, "CLIENT"], [56, "BROKER"], [34, "1"], [52, "20261126-10:00:00.500"], [11, "CL-1"], [55, "VOD.L"], [54, "1"], [38, "500"], [40, "2"], [44, "71.25"]]);
const ACK = fixmsg("FIX.4.4", [[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, "7"], [52, "20261126-10:00:01.000"], [150, "0"], [39, "0"], [11, "CL-1"], [37, "ORD-9"], [17, "E1"]]);
const GAPPED = fixmsg("FIX.4.4", [[35, "0"], [49, "CLIENT"], [56, "BROKER"], [34, "3"]]);
const BAD = "8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|";

test("index.html: header, privacy line, theme button, not-started message and the three sections", () => {
  page();
  expect(q("header").textContent).toContain("Runs entirely in this page. Nothing you paste is sent, stored or logged.");
  expect(q("#theme-button").tagName).toBe("BUTTON");
  expect(q("#theme-button").getAttribute("type")).toBe("button");
  expect(q("p#not-started").textContent.trim()).toBe("FIX Lens did not start. Open it through a web server, not as a file from disk.");
  for (const id of ["summary", "timeline", "decode"]) expect(q(`section#${id}`)).not.toBeNull();
  expect(q(".results #timeline > h2").textContent).toBe("Timeline");
  expect(q(".results #decode > h2").textContent).toBe("Decode");
  expect(q("#paste").tagName).toBe("TEXTAREA");
  expect(q("#decode-button").getAttribute("type")).toBe("button");
});

test("main.js removes the not-started message, and Decode fills the page", async () => {
  await boot();
  expect(q("#not-started")).toBeNull();
  q("#paste").value = [NEW, ACK].join("\n");
  q("#decode-button").click();
  expect(all("#decode article.card").length).toBe(2);
  expect(all("#timeline li.event").length).toBe(2);
});

test("the tool is hidden until the script starts, with the message outside it", async () => {
  page();
  const main = q("main");
  expect(main.hasAttribute("hidden")).toBe(true);
  for (const sel of ["#paste", "#decode-button", "#summary", ".results"]) expect(main.querySelector(sel), sel).not.toBeNull();
  expect(main.querySelector("#not-started")).toBeNull();
  expect(q("#not-started")).not.toBeNull();
  await boot();
  expect(q("main").hidden).toBe(false);
});

test("the summary strip has five counts, with singular forms", () => {
  show([NEW, ACK, GAPPED, BAD].join("\n"));
  expect(texts("#summary .stats .stat")).toEqual(["4 messages", "3 valid", "1 malformed", "1 sequence gap", "1 order"]);
  show(ACK);
  expect(texts("#summary .stats .stat")).toEqual(["1 message", "1 valid", "0 malformed", "0 sequence gaps", "1 order"]);
  show([GAPPED, fixmsg("FIX.4.4", [[35, "0"], [49, "CLIENT"], [56, "BROKER"], [34, "9"]]), fixmsg("FIX.4.4", [[35, "0"], [49, "CLIENT"], [56, "BROKER"], [34, "20"]])].join("\n"));
  expect(texts("#summary .stats .stat")).toEqual(["3 messages", "3 valid", "0 malformed", "2 sequence gaps", "0 orders"]);
});

test("a timeline row: number, time part, badge, direction, sequence number and ids", () => {
  show(ACK);
  const li = q("#timeline ol.events > li.event");
  expect(li.querySelector(".num").textContent).toBe("#1");
  expect(li.querySelector(".time").textContent).toBe("10:00:01.000");
  expect(li.querySelector(".badge").textContent).toBe("Acknowledgement");
  expect(li.querySelector(".dir").textContent).toBe("BROKER → CLIENT");
  expect(li.querySelector(".seq").textContent).toBe("seq 7");
  expect(li.textContent).toContain("ClOrdID CL-1");
  expect(li.textContent).toContain("OrderID ORD-9");
  expect(li.classList.contains("order")).toBe(true);
});

test("OrigClOrdID and ExecRefID are shown on the rows that have them", () => {
  const rep = fixmsg("FIX.4.4", [[35, "G"], [49, "CLIENT"], [56, "BROKER"], [34, "1"], [11, "CL-2"], [41, "CL-1"]]);
  const bust = fixmsg("FIX.4.4", [[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, "1"], [150, "H"], [11, "CL-2"], [37, "ORD-9"], [17, "E8"], [19, "E7"]]);
  show([rep, bust].join("\n"));
  const rows = all("#timeline li.event");
  expect(rows[0].querySelector(".badge").textContent).toBe("ReplaceRequest");
  expect(rows[0].textContent).toContain("OrigClOrdID CL-1");
  expect(rows[1].querySelector(".badge").textContent).toBe("TradeCancel");
  expect(rows[1].querySelector(".ref").textContent).toBe("ExecRefID E7");
});

test("row classes: gap, reject, order, session; the badge always names the event", () => {
  const mk = (type, seq, extra = []) => fixmsg("FIX.4.4", [[35, type], [49, "A"], [56, "B"], [34, seq], ...extra]);
  show([mk("A", 1), mk("3", 2), mk("j", 3), mk("9", 4, [[11, "C1"]]), mk("D", 5, [[11, "C1"]]), mk("0", 9)].join("\n"));
  const rows = all("#timeline li.event").map((li) => [li.querySelector(".badge").textContent,
    ["gap", "reject", "order", "session"].filter((c) => li.classList.contains(c))]);
  expect(rows).toEqual([["Logon", ["session"]], ["SessionReject", ["reject"]], ["BusinessReject", ["reject"]],
    ["CancelReject", ["reject"]], ["NewOrder", ["order"]], ["SequenceGap", ["gap"]], ["Heartbeat", ["session"]]]);
  expect(q("#timeline li.event.gap .detail").textContent).toBe("expected 6, received 9");
});

test("a message card: header, four column heads and one row per field", () => {
  show(ACK);
  const card = q("#decode article.card");
  expect(card.querySelector("header.card-head .num").textContent).toBe("#1");
  expect(card.querySelector("header.card-head h3").textContent).toBe("ExecutionReport");
  expect(card.querySelector(".dir").textContent).toBe("BROKER → CLIENT");
  expect(card.querySelector(".seq").textContent).toBe("seq 7");
  expect(card.querySelector(".time").textContent).toBe("10:00:01.000");
  expect([...card.querySelectorAll("table.fields th")].map((n) => n.textContent)).toEqual(["Tag", "Field", "Value", "Meaning"]);
  const rows = [...card.querySelectorAll("table.fields tr")].filter((tr) => tr.querySelector("td"))
    .map((tr) => [...tr.children].map((td) => td.textContent.trim()));
  expect(rows.length).toBe(analyse(ACK).decoded[0].fields.length);
  expect(rows).toContainEqual(["150", "ExecType", "0", "New"]);
  expect(rows).toContainEqual(["11", "ClOrdID", "CL-1", ""]);
  expect(rows).toContainEqual(["49", "SenderCompID", "BROKER", ""]);
});

test("malformed messages are error cards at their place in log order", () => {
  show([NEW, BAD, ACK].join("\n"));
  const cards = all("#decode article");
  expect(cards.map((c) => [c.querySelector(".num").textContent, c.classList.contains("malformed")]))
    .toEqual([["#1", false], ["#2", true], ["#3", false]]);
  expect(cards[1].querySelector("h3").textContent).toBe("Malformed message");
  expect(cards[1].querySelector("p.error-text").textContent).toBe(analyse([NEW, BAD, ACK].join("\n")).errors[0].text);
  expect(cards[1].querySelector("p.error-text").textContent).toMatch(/^Message 2: BodyLength \(9\) says 21, actual 20 at position \d+$/);
});

// v1.3 (FXL-19): replaces "empty states and the size warning", which pinned 1,001 messages.
test("empty states and the size warning at the v1.3 limit", () => {
  show("no fix here");
  expect(q("#decode p.empty").textContent).toBe("No FIX messages found in the pasted text.");
  expect(q("#timeline p.empty")).not.toBeNull();
  const big = analyse((ACK + "\n").repeat(10001));
  expect(big.ok).toBe(false);
  page();
  render(big);
  expect(all("#decode article").length).toBe(0);
  expect(all("#decode p").length).toBe(1);
  expect(q("#decode p.warning").textContent.replace(/[,.\s\u00a0\u202f']/g, "")).toContain("10001");
  expect(all("#timeline li").length).toBe(0);
  expect(q("#summary").children.length).toBe(0);
  expect(q("#decode > h2")).not.toBeNull();
  expect(all("nav.pager").length).toBe(0);
});

test("a second render replaces the first", () => {
  page();
  render(analyse([NEW, ACK].join("\n")));
  render(analyse(GAPPED));
  expect(all("#decode article").length).toBe(1);
  expect(q("#decode").textContent).not.toContain("ExecutionReport");
  expect(all("#timeline li.event").length).toBe(1);
  expect(all("#summary .stats").length).toBe(1);
});

test("pasted markup stays text, in cards and in the timeline", () => {
  const evil = "<img src=x onerror=alert(1)>";
  show(fixmsg("FIX.4.4", [[35, "D"], [49, evil], [56, "B"], [34, "1"], [11, evil], [58, evil]]));
  expect(document.querySelector("img")).toBeNull();
  expect(all("script").filter((s) => !s.getAttribute("src")).length).toBe(0);
  expect(q("#decode").textContent).toContain(evil);
  expect(q("#timeline").textContent).toContain(evil);
  for (const n of all("#summary *, #timeline *, #decode *")) {
    for (const a of n.attributes) expect(a.value.includes("<img"), `${n.tagName} ${a.name}`).toBe(false);
  }
});

test("an unsupported version is labelled, without made-up field names", () => {
  show("8=FIX.4.1|9=20|35=0|34=1|49=A|56=B|10=122|");
  expect(q("#decode article.card h3").textContent).toBe("unsupported version FIX.4.1");
  expect(q("#decode").textContent).not.toContain("Unknown tag");
});

test("the theme button switches the class on <html> and names the theme it would switch to", async () => {
  await boot(false);
  const b = q("#theme-button");
  expect(b.textContent).toBe("Dark theme");
  b.click();
  expect(document.documentElement.className).toBe("theme-dark");
  expect(b.textContent).toBe("Light theme");
  b.click();
  expect(document.documentElement.className).toBe("theme-light");
  expect(b.textContent).toBe("Dark theme");
  document.documentElement.className = "";
  await boot(true);
  expect(q("#theme-button").textContent).toBe("Light theme");
  q("#theme-button").click();
  expect(document.documentElement.className).toBe("theme-light");
});

// ---- styles.css ----
const NAMES = ["--bg", "--panel", "--ink", "--muted", "--line", "--soft", "--accent", "--accent-ink", "--ok", "--warn",
  "--warn-bg", "--bad", "--bad-bg", "--order", "--order-bg", "--session-bg"];
const css = CSS.replace(/\/\*[\s\S]*?\*\//g, "");
function block(re) {
  const m = re.exec(css);
  expect(m, String(re)).not.toBeNull();
  const start = m.index + m[0].length;
  return [start, css.indexOf("}", start)];
}
const SPANS = () => [
  block(/:root\s*\{/),
  block(/@media\s*\(\s*prefers-color-scheme\s*:\s*dark\s*\)\s*\{\s*:root:not\(\s*\.theme-light\s*\)\s*\{/),
  block(/:root\.theme-dark\s*\{/),
];
const vars = ([a, b]) => Object.fromEntries([...css.slice(a, b).matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)].map((m) => [m[1], m[2].trim().toLowerCase()]));
const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (fg, bg) => { const [hi, lo] = [lum(fg), lum(bg)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };

test("the colour properties are declared three times, as hex, with equal dark blocks", () => {
  const [light, media, dark] = SPANS().map(vars);
  for (const set of [light, media, dark]) for (const n of NAMES) expect(set[n], n).toMatch(/^#[0-9a-f]{6}$/);
  for (const n of NAMES) expect(media[n], n).toBe(dark[n]);
});

test("every colour in the stylesheet is one of the properties", () => {
  const spans = SPANS();
  let rest = "";
  let at = 0;
  for (const [a, b] of [...spans].sort((x, y) => x[0] - y[0])) { rest += css.slice(at, a); at = b; }
  rest += css.slice(at);
  expect(rest).not.toMatch(/#[0-9a-f]{3,8}\b/i);
  expect(rest).not.toMatch(/\b(rgb|rgba|hsl|hsla)\(/i);
});

test("text contrast is at least 4.5 to 1 in both themes", () => {
  const [light, , dark] = SPANS().map(vars);
  const pairs = [["--ink", "--bg"], ["--ink", "--panel"], ["--muted", "--panel"], ["--muted", "--bg"], ["--accent-ink", "--accent"],
    ["--ok", "--panel"], ["--warn", "--warn-bg"], ["--bad", "--bad-bg"], ["--order", "--order-bg"], ["--ink", "--session-bg"]];
  for (const [name, set] of [["light", light], ["dark", dark]]) {
    for (const [fg, bg] of pairs) expect(ratio(set[fg], set[bg]), `${name}: ${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
  }
});

test("two columns from 900px with a sticky timeline", () => {
  expect(css).toMatch(/@media[^{]*\(\s*min-width\s*:\s*900px\s*\)/);
  expect(css).toMatch(/position\s*:\s*sticky/);
  expect(css).toMatch(/\.results\b/);
});

// ---- source rules ----
const strip = (s) => { let p; do { p = s; s = s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:\\])\/\/.*$/gm, "$1"); } while (s !== p); return s; };
const SRC = readdirSync("src").filter((n) => n.endsWith(".js")).map((n) => [n, strip(readFileSync(`src/${n}`, "utf8"))]);

test("no dynamic import, no setAttribute, and no attribute-like property is assigned anywhere in src", () => {
  for (const [name, code] of SRC) {
    expect(code, name).not.toMatch(/\bimport\s*\(/);
    expect(code, name).not.toMatch(/\bsetAttribute\s*\(/);
    expect(code, name).not.toMatch(/\.(id|name|title|src|href|value|style|cssText)\s*=[^=]/);
    expect(code, name).not.toMatch(/\.style\b/);
  }
});

test("index.html has no inline script, style element, style attribute or event attribute", () => {
  // Repeated until stable, so a nested fragment such as "<!<!---->--" cannot leave a comment opener behind.
  let h = HTML;
  for (let prev = null; prev !== h;) { prev = h; h = h.replace(/<!--[\s\S]*?-->/g, ""); }
  expect(h).not.toMatch(/<style\b/i);
  expect(h).not.toMatch(/\sstyle\s*=/i);
  expect(h).not.toMatch(/\son[a-z]+\s*=/i);
  for (const m of h.matchAll(/<script\b[^>]*>/gi)) expect(m[0]).toMatch(/\ssrc\s*=/i);
});

test("the dictionary modules are export default plus one JSON object", () => {
  for (const f of ["src/dictionary/fix42.js", "src/dictionary/fix44.js"]) {
    const t = readFileSync(f, "utf8").trim();
    expect(t.startsWith("export default ")).toBe(true);
    const v = JSON.parse(t.slice("export default ".length).replace(/;$/, ""));
    expect(typeof v === "object" && v !== null).toBe(true);
  }
});
