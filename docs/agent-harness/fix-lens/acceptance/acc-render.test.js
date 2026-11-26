// @vitest-environment jsdom
import { test, expect, beforeEach } from "vitest";
import { analyse } from "../src/analyse.js";
import { render } from "../src/render.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
const ORDER = fixmsg("FIX.4.4", [[35, "8"], [49, "BROKER"], [56, "CLIENT"], [34, "7"],
  [52, "20261126-10:00:01.000"], [150, "0"], [11, "CL-1"], [37, "ORD-9"]]);

beforeEach(() => {
  document.body.replaceChildren();
  for (const id of ["decode", "timeline"]) {
    const s = document.createElement("section");
    s.id = id;
    s.append(document.createElement("h2"));
    document.body.append(s);
  }
});
const text = (id) => document.querySelector(`#${id}`).textContent;

test("timeline rows show every AC-010 field for an order event", () => {
  render(analyse(ORDER));
  const t = text("timeline");
  for (const part of ["Message 1", "Acknowledgement", "20261126-10:00:01.000", "BROKER", "CLIENT", "7", "CL-1", "ORD-9"]) {
    expect(t).toContain(part);
  }
});

test("decode rows show tag, name, raw value and enum meaning", () => {
  render(analyse(ORDER));
  const d = text("decode");
  expect(d).toContain("Message 1: ExecutionReport");
  expect(d).toMatch(/35\s+MsgType/);
  expect(d).toContain("ExecutionReport");
  expect(d).toMatch(/49\s+SenderCompID/);
  expect(d).toContain("BROKER");
});

test("pasted markup is shown as text and creates no element", () => {
  const evil = fixmsg("FIX.4.4", [[35, "0"], [49, "A"], [56, "B"], [34, "1"], [58, "<img src=x onerror=alert(1)>"]]);
  render(analyse(evil));
  expect(document.querySelector("img")).toBeNull();
  expect(document.querySelectorAll("script").length).toBe(0);
  expect(text("decode")).toContain("<img src=x onerror=alert(1)>");
});

test("a second render replaces the first, and errors and the size warning are shown", () => {
  render(analyse(ORDER));
  const bad = "8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|";
  render(analyse(bad));
  expect(text("decode")).not.toContain("ExecutionReport");
  expect(text("decode")).toMatch(/Message 1: .* at position 11/);
  expect(text("timeline")).not.toContain("Acknowledgement");
  render(analyse((ORDER + "\n").repeat(1001)));
  expect(text("decode")).toContain("1001");
  expect(document.querySelectorAll("#decode article").length).toBe(0);
});

test("an unsupported version is labelled and its fields are shown raw, without made-up names", () => {
  render(analyse("8=FIX.4.1|9=20|35=0|34=1|49=A|56=B|10=122|"));
  const d = text("decode");
  expect(d).toContain("Message 1: unsupported version FIX.4.1");
  expect(d).not.toContain("Unknown tag");
  expect(d).toMatch(/49\s*:\s*A/);
});
