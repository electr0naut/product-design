// FXL-25: single-byte text outside ASCII (PRD v1.4 TR-002; design v1.4 section 3, step 7).
// BodyLength and CheckSum are computed here both ways, independently of the product.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { tradeSummary } from "../src/summary.js";

const SOH = "\x01";
const utf8 = (text) => [...new TextEncoder().encode(text)];
// one byte per character, its value the code point; only for text up to U+00FF
const latin1 = (text) => [...text].map((c) => c.codePointAt(0));
// build(bytesOf, fields, sep): a message whose counts are right for that way of counting
function build(bytesOf, fields, sep = "|", fix = {}) {
  const body = fields.map(([t, v]) => `${t}=${v}${SOH}`).join("");
  const length = fix.length ?? bytesOf(body).length;
  const head = `8=FIX.4.4${SOH}9=${length}${SOH}`;
  const sum = fix.sum ?? bytesOf(head + body).reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${SOH}`).replaceAll(SOH, sep);
}
const HB = (text) => [[35, "0"], [49, "A"], [56, "B"], [34, "1"], [52, "20261127-09:00:00.000"], [58, text]];
const NAME = "Société Générale order";

test("the validation's message: counts right for one byte per character, valid", () => {
  const line = "8=FIX.4.4|9=71|35=0|49=A|56=B|34=1|52=20261127-09:00:00.000|58=Société Générale order|10=075|";
  expect(build(latin1, HB(NAME))).toBe(line);
  const r = analyse(line);
  expect(r.errors).toEqual([]);
  expect(r.decoded.length).toBe(1);
  expect(r.decoded[0].fields.find((f) => f.tag === 58).value).toBe(NAME);
  expect(r.timeline.map((e) => e.name)).toEqual(["Heartbeat"]);
});

test("the same text counted in UTF-8 is valid as before", () => {
  const line = build(utf8, HB(NAME));
  expect(line).toContain("|9=75|");
  expect(analyse(line).errors).toEqual([]);
});

test("each delimiter form, and both ways of counting in one paste", () => {
  for (const sep of [SOH, "|", "^A", "<SOH>"]) {
    const text = [build(latin1, HB(NAME), sep), build(utf8, HB(NAME), sep), build(latin1, HB("plain"), sep)].join("\n");
    const r = analyse(text);
    expect(r.errors).toEqual([]);
    expect(r.decoded.length).toBe(3);
  }
});

test("every character from U+0080 to U+00FF counts as one byte with its own value", () => {
  for (const ch of ["\u0080", " ", "é", "ÿ"]) {
    expect(analyse(build(latin1, HB(`x${ch}y${ch}`))).errors).toEqual([]);
  }
  // the checksum must use the value of the character: a sum that takes every such character as 0x3F ("?") is wrong
  const asQuestionMark = (text) => [...text].map((c) => (c.codePointAt(0) > 127 ? 63 : c.codePointAt(0)));
  const wrong = build(asQuestionMark, HB("café"));
  expect(analyse(wrong).errors.length).toBe(1);
});

test("a character above U+00FF anywhere in the message: only the UTF-8 count is tried", () => {
  // counted one per character, as a single-byte link could never have sent it
  const perCharacter = (text) => [...text].map((c) => c.codePointAt(0) % 256);
  for (const text of ["Société €", "Łódź", "café 😀"]) {
    const r = analyse(build(perCharacter, HB(text)));
    expect(r.decoded).toEqual([]);
    expect(r.errors.length).toBe(1);
    expect(r.errors[0].rule).toBe("body_length");
    const said = perCharacter(HB(text).map(([t, v]) => `${t}=${v}${SOH}`).join("")).length;
    const actual = utf8(HB(text).map(([t, v]) => `${t}=${v}${SOH}`).join("")).length;
    expect(r.errors[0].text).toBe(`Message 1: BodyLength (9) says ${said}, actual ${actual} at position 11`);
  }
  // and counted in UTF-8 it is valid
  expect(analyse(build(utf8, HB("Société €"))).errors).toEqual([]);
});

test("when neither count holds, the error is the UTF-8 one, unchanged", () => {
  const body = HB(NAME).map(([t, v]) => `${t}=${v}${SOH}`).join("");
  const one = latin1(body).length; // 71
  const two = utf8(body).length; // 75
  expect([one, two]).toEqual([71, 75]);
  // BodyLength right for one byte per character, CheckSum wrong for it
  const badSum = analyse(build(latin1, HB(NAME), "|", { sum: (latin1(`8=FIX.4.4${SOH}9=71${SOH}${body}`).reduce((a, b) => a + b, 0) + 1) % 256 }));
  expect(badSum.errors.map((e) => [e.rule, e.text])).toEqual([["body_length", "Message 1: BodyLength (9) says 71, actual 75 at position 11"]]);
  // BodyLength right for neither
  const badLength = analyse(build(latin1, HB(NAME), "|", { length: 73 }));
  expect(badLength.errors.map((e) => [e.rule, e.text])).toEqual([["body_length", "Message 1: BodyLength (9) says 73, actual 75 at position 11"]]);
  // BodyLength right for UTF-8, CheckSum wrong for it: one byte per character fails on the length, so `checksum` is reported
  const utfBadSum = analyse(build(utf8, HB(NAME), "|", { sum: (utf8(`8=FIX.4.4${SOH}9=75${SOH}${body}`).reduce((a, b) => a + b, 0) + 1) % 256 }));
  expect(utfBadSum.errors.map((e) => e.rule)).toEqual(["checksum"]);
});

test("a message of plain ASCII with a wrong count is malformed as before", () => {
  const r = analyse(build(utf8, HB("plain"), "|", { length: 1 }));
  expect(r.errors.map((e) => e.rule)).toEqual(["body_length"]);
});

test("a fill with an accented account name, counted one byte per character, is in the trading summary", () => {
  const fill = [[35, "8"], [49, "BRK"], [56, "CLI"], [34, "1"], [1, "Générale"], [37, "O1"], [17, "E1"], [150, "F"], [55, "ACME"], [54, "1"], [32, "100"], [31, "10"]];
  const r = analyse(build(latin1, fill));
  expect(r.errors).toEqual([]);
  const s = tradeSummary(r.decoded);
  expect([s.rows.length, s.rows[0].buy.filledQty, s.rows[0].buy.notional]).toEqual([1, 100, 1000]);
});

test("the neighbours of a malformed single-byte message are untouched", () => {
  const body = HB(NAME).map(([t, v]) => `${t}=${v}${SOH}`).join("");
  const bad = build(latin1, HB(NAME), "|", { sum: (latin1(`8=FIX.4.4${SOH}9=71${SOH}${body}`).reduce((a, b) => a + b, 0) + 7) % 256 });
  const r = analyse([build(latin1, HB(NAME)), bad, build(latin1, HB(NAME))].join("\n"));
  expect(r.errors.map((e) => e.number)).toEqual([2]);
  expect(r.decoded.map((d) => d.number)).toEqual([1, 3]);
});
