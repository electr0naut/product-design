import { test, expect } from "vitest";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const CSP = "default-src 'self'; connect-src 'none'; form-action 'none'";
const html = () => readFileSync("index.html", "utf8");
// Removes comments before scanning. Repeated until stable so nested fragments such as "<!<!---->--" cannot
// leave a comment opener behind (CodeQL js/incomplete-multi-character-sanitization).
function stripComments(s) {
  let prev;
  do {
    prev = s;
    s = s.replace(/\/\*[\s\S]*?\*\//g, "").replace(/(^|[^:\\])\/\/.*$/gm, "$1").replace(/<!--[\s\S]*?-->/g, "");
  } while (s !== prev);
  return s;
}
function srcFiles(dir = "src") {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n);
    return statSync(p).isDirectory() ? srcFiles(p) : p.endsWith(".js") ? [p] : [];
  });
}

test("exactly one CSP meta tag, first in <head>, with the exact policy", () => {
  const h = html();
  const metas = [...h.matchAll(/<meta[^>]+http-equiv=["']Content-Security-Policy["'][^>]*>/gi)];
  expect(metas.length).toBe(1);
  expect(metas[0][0]).toContain(`content="${CSP}"`);
  const head = h.slice(h.search(/<head[^>]*>/i));
  const firstTag = head.replace(/<head[^>]*>/i, "").trimStart().match(/^<\w+[^>]*>/)[0];
  expect(firstTag).toMatch(/http-equiv=["']Content-Security-Policy["']/i);
});

test("the textarea cannot leak input through autofill, spellcheck or translation", () => {
  const ta = html().match(/<textarea[^>]*>/i)[0];
  for (const a of ['autocomplete="off"', 'spellcheck="false"', 'autocapitalize="off"', 'autocorrect="off"', 'translate="no"']) {
    expect(ta).toContain(a);
  }
});

test("no inline script, inline style or style attribute", () => {
  const h = stripComments(html());
  expect(h).not.toMatch(/<script(?![^>]*\bsrc=)[^>]*>/i);
  expect(h).not.toMatch(/<style[\s>]/i);
  expect(h).not.toMatch(/\sstyle\s*=/i);
  expect(h).not.toMatch(/\son[a-z]+\s*=/i);
});

test("no network, storage, logging or unsafe-markup API anywhere in src", () => {
  const banned = [
    /\bfetch\b/, /XMLHttpRequest/, /WebSocket/, /sendBeacon/, /EventSource/, /window\.open/,
    /\blocalStorage\b/, /\bsessionStorage\b/, /\bindexedDB\b/, /document\.cookie/, /\bcookieStore\b/,
    /\bcaches\b/, /serviceWorker/, /\bWorker\s*\(/, /SharedWorker/,
    /\bconsole\s*\./, /innerHTML/, /outerHTML/, /insertAdjacentHTML/, /document\.write/, /DOMParser/,
    /createContextualFragment/, /setHTMLUnsafe/, /srcdoc/, /\beval\s*\(/, /new\s+Function/,
  ];
  for (const f of srcFiles()) {
    const code = stripComments(readFileSync(f, "utf8"));
    for (const re of banned) expect([f, re.test(code)]).toEqual([f, false]);
  }
});
