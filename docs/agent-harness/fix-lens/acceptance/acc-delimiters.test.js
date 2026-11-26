// FXL-9: the four delimiter forms and a delimiter inside a value (PRD v1.2 TR-002, design v1.2 section 3).
// Every literal message was computed in Python, BodyLength and CheckSum over SOH, independently of the product.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";

const S = "\x01";
const PIPE = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";
const CARET = "8=FIX.4.4^A9=20^A35=0^A34=1^A49=A^A56=B^A10=125^A";
const SOHTAG = "8=FIX.4.4<SOH>9=20<SOH>35=0<SOH>34=1<SOH>49=A<SOH>56=B<SOH>10=125<SOH>";
const SOHCHAR = PIPE.replaceAll("|", S);
const pairs = (m) => m.fields.map((f) => [f.tag, f.value]);
const REF = [[8, "FIX.4.4"], [9, "20"], [35, "0"], [34, "1"], [49, "A"], [56, "B"], [10, "125"]];
const one = (text) => {
  const r = analyse(text);
  expect(r.errors).toEqual([]);
  expect(r.messages.length).toBe(1);
  return r.messages[0];
};
const value = (m, tag) => m.fields.find((f) => f.tag === tag).value;
const rule = (text) => {
  const r = analyse(text);
  expect(r.errors.length).toBe(1);
  return r.errors[0].rule;
};

test("the reference message is valid in all four delimiter forms, with the same tags and values", () => {
  for (const text of [PIPE, CARET, SOHTAG, SOHCHAR]) expect(pairs(one(text))).toEqual(REF);
});

test("the delimiter is chosen per message: four forms on four lines", () => {
  const r = analyse([PIPE, CARET, SOHTAG, SOHCHAR].join("\n"));
  expect(r.errors).toEqual([]);
  expect(r.decoded.length).toBe(4);
  for (const m of r.messages) expect(pairs(m)).toEqual(REF);
});

test("field positions are offsets in the pasted text for ^A and <SOH>", () => {
  expect(one(CARET).fields.map((f) => f.position)).toEqual([0, 11, 17, 23, 29, 35, 41]);
  expect(one(SOHTAG).fields.map((f) => f.position)).toEqual([0, 14, 23, 32, 41, 50, 59]);
});

test("a text delimiter not followed by digits and = is part of the value", () => {
  const cases = [
    ["8=FIX.4.4|9=27|35=0|34=1|49=A|56=B|58=a|b|10=110|", "a|b"],
    ["8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=x||y|10=025|", "x||y"],
    ["8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=end||10=227|", "end|"],
    ["8=FIX.4.4^A9=28^A35=0^A34=1^A49=A^A56=B^A58=a^Ab^A10=146^A", "a^Ab"],
    ["8=FIX.4.4<SOH>9=31<SOH>35=0<SOH>34=1<SOH>49=A<SOH>56=B<SOH>58=a<SOH>b<SOH>10=081<SOH>", "a<SOH>b"],
  ];
  for (const [text, v] of cases) expect(value(one(text), 58)).toBe(v);
});

test("BodyLength counts UTF-8 bytes of a value that holds a delimiter character", () => {
  expect(value(one("8=FIX.4.4|9=33|35=0|34=1|49=A|56=B|58=café|€|10=078|"), 58)).toBe("café|€");
});

test("the other delimiter forms are ordinary text inside a message", () => {
  expect(value(one("8=FIX.4.4^A9=27^A35=0^A34=1^A49=A^A56=B^A58=a|b^A10=110^A"), 58)).toBe("a|b");
  expect(value(one("8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=a^Ab|10=146|"), 58)).toBe("a^Ab");
});

test("a value holding the delimiter followed by digits and = reads as a new field: CheckSum error, no second reading", () => {
  expect(rule("8=FIX.4.4|9=31|35=0|34=1|49=A|56=B|58=a|112=b|10=058|")).toBe("checksum");
  const m = one("8=FIX.4.4|9=31|35=0|34=1|49=A|56=B|58=a|112=b|10=191|");
  expect([value(m, 58), value(m, 112)]).toEqual(["a", "b"]);
});

test("the delimiter after the CheckSum ends the message even when text follows", () => {
  expect(pairs(one("10:00:00 OUT " + PIPE + " trailing text"))).toEqual(REF);
});

test("two ^A messages on one line, after a prefix", () => {
  const r = analyse("10:00:00 OUT " + CARET + "8=FIX.4.2^A9=20^A35=0^A34=2^A49=A^A56=B^A10=124^A");
  expect(r.errors).toEqual([]);
  expect(r.messages.map((m) => value(m, 8))).toEqual(["FIX.4.4", "FIX.4.2"]);
  expect(r.messages[1].start).toBe(13 + CARET.length);
});

test("a CheckSum computed over the delimiter's own text bytes is rejected", () => {
  expect(rule("8=FIX.4.4^A9=20^A35=0^A34=1^A49=A^A56=B^A10=049^A")).toBe("checksum");
});

test("a wrong BodyLength with ^A keeps the error form and the position in the pasted text", () => {
  const r = analyse("8=FIX.4.4^A9=21^A35=0^A34=1^A49=A^A56=B^A10=126^A");
  expect(r.errors[0].rule).toBe("body_length");
  expect(r.errors[0].text).toBe("Message 1: BodyLength (9) says 21, actual 20 at position 12");
  expect(r.decoded).toEqual([]);
});

test("no delimiter form after BeginString is header_order; lower-case <soh> is not a delimiter", () => {
  expect(rule("8=FIX.4.4 9=20 35=0")).toBe("header_order");
  expect(rule(SOHTAG.replaceAll("<SOH>", "<soh>"))).toBe("header_order");
});

test("with the SOH character nothing changes: an empty piece is an error and text forms are ordinary text", () => {
  expect(rule(SOHCHAR.replace(`${S}35=0${S}`, `${S}35=0${S}${S}`))).toBe("field_without_equals");
  const body = `35=0${S}34=1${S}49=A${S}56=B${S}58=a|b^A<SOH>c${S}`;
  const head = `8=FIX.4.4${S}9=${body.length}${S}`;
  const sum = [...(head + body)].reduce((a, c) => a + c.charCodeAt(0), 0) % 256;
  expect(value(one(`${head}${body}10=${String(sum).padStart(3, "0")}${S}`), 58)).toBe("a|b^A<SOH>c");
});

test("a malformed text-delimited message does not stop the next one", () => {
  const r = analyse(["8=FIX.4.4^A9=21^A35=0^A34=1^A49=A^A56=B^A10=126^A", SOHTAG].join("\n"));
  expect(r.errors.map((e) => e.number)).toEqual([1]);
  expect(r.decoded.map((d) => d.number)).toEqual([2]);
});
