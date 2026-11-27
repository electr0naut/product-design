// FXL-20: the paging module (PRD v1.3 AC-057, AC-058, AC-060; design v1.3 section 16). Every expected value
// here was worked out by hand from the design.
import { test, expect } from "vitest";
import * as paging from "../src/paging.js";
import { PAGE_SIZE, pageOf, pageLabel } from "../src/paging.js";

const list = (n) => Array.from({ length: n }, (_, i) => ({ n: i + 1 }));

test("the module exports PAGE_SIZE 200, pageOf and pageLabel", () => {
  expect(PAGE_SIZE).toBe(200);
  expect(typeof pageOf).toBe("function");
  expect(typeof pageLabel).toBe("function");
  expect(Object.keys(paging).sort()).toEqual(["PAGE_SIZE", "pageLabel", "pageOf"]);
});

test("pageOf result keys", () => {
  expect(Object.keys(pageOf(list(3), 1)).sort()).toEqual(["from", "items", "page", "pages", "to", "total"]);
});

test("pages is at least 1 and rounds up at 200 per page", () => {
  const want = [[0, 1], [1, 1], [199, 1], [200, 1], [201, 2], [400, 2], [401, 3], [450, 3], [10000, 50]];
  expect(want.map(([n]) => [n, pageOf(list(n), 1).pages])).toEqual(want);
  expect(want.map(([n]) => pageOf(list(n), 1).total)).toEqual(want.map(([n]) => n));
});

test("450 entries: three pages with their from, to and items", () => {
  const e = list(450);
  const p1 = pageOf(e, 1);
  expect([p1.page, p1.pages, p1.from, p1.to, p1.total, p1.items.length]).toEqual([1, 3, 1, 200, 450, 200]);
  const p2 = pageOf(e, 2);
  expect([p2.page, p2.pages, p2.from, p2.to, p2.total, p2.items.length]).toEqual([2, 3, 201, 400, 450, 200]);
  expect([p2.items[0].n, p2.items[199].n]).toEqual([201, 400]);
  const p3 = pageOf(e, 3);
  expect([p3.page, p3.pages, p3.from, p3.to, p3.total, p3.items.length]).toEqual([3, 3, 401, 450, 450, 50]);
  expect(p3.items.map((x) => x.n)).toEqual(list(450).slice(400).map((x) => x.n));
});

test("items are the same objects, in order", () => {
  const e = list(201);
  const p1 = pageOf(e, 1);
  expect(p1.items.every((x, i) => x === e[i])).toBe(true);
  const p2 = pageOf(e, 2);
  expect([p2.from, p2.to, p2.items.length]).toEqual([201, 201, 1]);
  expect(p2.items[0]).toBe(e[200]);
});

test("exactly 200 and exactly 400 entries end on a full page", () => {
  const one = pageOf(list(200), 1);
  expect([one.page, one.pages, one.from, one.to, one.items.length]).toEqual([1, 1, 1, 200, 200]);
  const two = pageOf(list(400), 2);
  expect([two.page, two.pages, two.from, two.to, two.items.length]).toEqual([2, 2, 201, 400, 200]);
});

test("a page that is not an integer becomes 1", () => {
  const e = list(450);
  for (const bad of [undefined, null, NaN, 1.5, 2.5, "2", "x", true, {}, [2]]) {
    const p = pageOf(e, bad);
    expect([String(bad), p.page, p.from, p.to], String(bad)).toEqual([String(bad), 1, 1, 200]);
  }
  expect(pageOf(e).page).toBe(1);
});

test("a page below 1 becomes 1 and a page above the last becomes the last", () => {
  const e = list(450);
  for (const low of [0, -1, -99]) expect([low, pageOf(e, low).page, pageOf(e, low).from]).toEqual([low, 1, 1]);
  for (const high of [4, 99, 1000000]) {
    const p = pageOf(e, high);
    expect([high, p.page, p.from, p.to, p.items.length]).toEqual([high, 3, 401, 450, 50]);
  }
});

test("no entries: one empty page, from and to are 0", () => {
  for (const page of [1, 2, 0, undefined]) {
    expect(pageOf([], page)).toEqual({ page: 1, pages: 1, from: 0, to: 0, total: 0, items: [] });
  }
});

test("pageOf never changes entries and returns a new array", () => {
  const e = Object.freeze(list(250));
  const copy = [...e];
  const p1 = pageOf(e, 1);
  const p2 = pageOf(e, 2);
  expect(e.length).toBe(250);
  expect(e.every((x, i) => x === copy[i])).toBe(true);
  expect(p1.items).not.toBe(e);
  expect(p2.items.length).toBe(50);
  const small = Object.freeze(list(5));
  const whole = pageOf(small, 1);
  expect(whole.items).not.toBe(small);
  expect(whole.items).toEqual([...small]);
});

test("pageLabel: the examples of the design", () => {
  expect(pageLabel({ from: 201, to: 400, total: 10000 }, false)).toBe("Messages 201 to 400 of 10,000");
  expect(pageLabel({ from: 1, to: 200, total: 1240 }, true)).toBe("Messages 1 to 200 of 1,240 shown");
});

test("pageLabel: commas between thousands in all three numbers, none below 1,000", () => {
  expect(pageLabel({ from: 9801, to: 10000, total: 10000 }, false)).toBe("Messages 9,801 to 10,000 of 10,000");
  expect(pageLabel({ from: 801, to: 1000, total: 1000 }, false)).toBe("Messages 801 to 1,000 of 1,000");
  expect(pageLabel({ from: 1, to: 200, total: 999 }, false)).toBe("Messages 1 to 200 of 999");
  expect(pageLabel({ from: 1001, to: 1200, total: 1234567 }, true)).toBe("Messages 1,001 to 1,200 of 1,234,567 shown");
  expect(pageLabel({ from: 0, to: 0, total: 0 }, false)).toBe("Messages 0 to 0 of 0");
});

test("pageLabel: ' shown' only when narrowed is true, and it reads a pageOf result", () => {
  const info = pageOf(list(450), 2);
  expect(pageLabel(info, false)).toBe("Messages 201 to 400 of 450");
  expect(pageLabel(info)).toBe("Messages 201 to 400 of 450");
  expect(pageLabel(info, true)).toBe("Messages 201 to 400 of 450 shown");
});

test("the label does not depend on the language of the browser", () => {
  const original = Number.prototype.toLocaleString;
  // a browser set to German writes 10.000 when no locale is named
  Number.prototype.toLocaleString = function (locales, options) { return original.call(this, locales ?? "de-DE", options); };
  try {
    expect(pageLabel({ from: 9801, to: 10000, total: 10000 }, false)).toBe("Messages 9,801 to 10,000 of 10,000");
  } finally {
    Number.prototype.toLocaleString = original;
  }
});
