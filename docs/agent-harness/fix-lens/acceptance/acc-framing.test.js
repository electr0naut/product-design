import { test, expect } from "vitest";
import { splitMessages } from "../src/framing.js";

const S = "\x01";
const V1 = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";

test("candidate and field keys are exactly as the ticket specifies", () => {
  const [m] = splitMessages(V1);
  expect(Object.keys(m).sort()).toEqual(["end", "fields", "number", "start"]);
  expect(Object.keys(m.fields[0]).sort()).toEqual(["position", "tag", "value"]);
});

test("pipe and SOH forms give the same tags and values", () => {
  const a = splitMessages(V1)[0].fields.map((f) => [f.tag, f.value]);
  const b = splitMessages(V1.replaceAll("|", S))[0].fields.map((f) => [f.tag, f.value]);
  expect(a).toEqual(b);
  expect(a[0]).toEqual([8, "FIX.4.4"]);
  expect(a.at(-1)).toEqual([10, "125"]);
});

test("field positions are 0-based offsets of the tag", () => {
  const [m] = splitMessages(V1);
  expect(m.fields[1].position).toBe(10);
  expect(m.fields[2].position).toBe(15);
});

test("a timestamp prefix is ignored and start points at 8=FIX", () => {
  const text = "2026-11-26 10:00:01 IN " + V1;
  const [m] = splitMessages(text);
  expect(m.start).toBe(23);
  expect(m.end).toBe(text.length);
});

test("a prefix containing = does not hide the message", () => {
  const ms = splitMessages("session=ABC " + V1);
  expect(ms.length).toBe(1);
  expect(ms[0].start).toBe(12);
});

test("two messages on one line and on two CRLF lines", () => {
  expect(splitMessages(V1 + V1).length).toBe(2);
  const crlf = splitMessages(V1.slice(0, -1) + "\r\n" + V1.slice(0, -1) + "\r\n");
  expect(crlf.length).toBe(2);
  expect(crlf[0].fields.at(-1).value).toBe("125");
  expect(crlf[1].number).toBe(2);
});

test("448=FIXCLIENT and 110=100 inside a message neither start nor end a message", () => {
  const m = "8=FIX.4.4|9=42|35=0|34=1|49=A|56=B|448=FIXCLIENT|110=100|10=102|";
  const ms = splitMessages(m);
  expect(ms.length).toBe(1);
  expect(ms[0].fields.map((f) => f.tag)).toEqual([8, 9, 35, 34, 49, 56, 448, 110, 10]);
});

test("text with no 8=FIX gives an empty list", () => {
  expect(splitMessages("hello world\n35=0|10=000|")).toEqual([]);
});

test("a candidate without CheckSum is still returned, and the next message still found", () => {
  const ms = splitMessages("8=FIX.4.4|9=5|35=0|\n" + V1);
  expect(ms.length).toBe(2);
  expect(ms[1].fields.at(-1).value).toBe("125");
});
