// Framing rules that mutation testing of FXL-9 showed no test was holding (design v1.2 section 3, steps 2, 4,
// 8, 9 and 10). Every literal message was computed in Python, BodyLength and CheckSum over SOH, independently
// of the product.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { splitMessages } from "../src/framing.js";

const S = "\x01";
const one = (text) => {
  const r = analyse(text);
  expect(r.errors).toEqual([]);
  expect(r.messages.length).toBe(1);
  return r.messages[0];
};
const value = (m, tag) => m.fields.find((f) => f.tag === tag).value;
const error = (text) => {
  const r = analyse(text);
  expect(r.messages.length).toBe(0);
  expect(r.errors.length).toBe(1);
  return r.errors[0];
};

test("a text delimiter followed by digits but no = is part of the value", () => {
  const cases = [
    ["8=FIX.4.4|9=33|35=0|34=1|49=A|56=B|58=5|10 lots|10=032|", "5|10 lots"],
    ["8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=a|12|10=112|", "a|12"],
    ["8=FIX.4.4^A9=29^A35=0^A34=1^A49=A^A56=B^A58=x^A7y^A10=248^A", "x^A7y"],
    ["8=FIX.4.4<SOH>9=33<SOH>35=0<SOH>34=1<SOH>49=A<SOH>56=B<SOH>58=x<SOH>7 y<SOH>10=216<SOH>", "x<SOH>7 y"],
  ];
  for (const [text, v] of cases) expect(value(one(text), 58)).toBe(v);
});

test("a text delimiter followed by = with no digits is part of the value", () => {
  expect(value(one("8=FIX.4.4|9=28|35=0|34=1|49=A|56=B|58=a|=b|10=172|"), 58)).toBe("a|=b");
  expect(value(one("8=FIX.4.4^A9=29^A35=0^A34=1^A49=A^A56=B^A58=a^A=b^A10=208^A"), 58)).toBe("a^A=b");
});

test("a text delimiter at the end of the text is a separator, not part of the last value", () => {
  for (const d of ["|", "^A", "<SOH>"]) {
    const text = ["8=FIX.4.4", "9=5", "35=0"].join(d) + d;
    const [c] = splitMessages(text);
    expect(c.fields.map((f) => [f.tag, f.value])).toEqual([[8, "FIX.4.4"], [9, "5"], [35, "0"]]);
    expect(error(text).rule).toBe("missing_checksum");
  }
});

test("missing CheckSum is reported at the candidate's end, with or without a last delimiter", () => {
  // the end is the offset after the candidate's last character; positions are 1-based
  for (const [text, position] of [
    ["8=FIX.4.4|9=5|35=0|", 20], ["8=FIX.4.4|9=5|35=0", 19],
    [`8=FIX.4.4${S}9=5${S}35=0${S}`, 20], [`8=FIX.4.4${S}9=5${S}35=0`, 19],
    ["8=FIX.4.4|9=5|35=0|\n8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|", 20],
  ]) {
    const r = analyse(text);
    const e = r.errors[0];
    expect([e.rule, e.position], JSON.stringify(text)).toEqual(["missing_checksum", position]);
    expect(e.text).toBe(`Message 1: missing CheckSum (tag 10) at position ${position}`);
  }
});

test("8=FIX right after a digit never starts a message", () => {
  for (const text of ["18=FIX.4.4|9=5|35=0|10=000|", "448=FIXCLIENT|35=0|", "log 98=FIX.4.4|9=5|35=0|"]) {
    const r = analyse(text);
    expect(r.messages.length).toBe(0);
    expect(r.errors).toEqual([]);
  }
});

test("a tag with a letter after its digits is a bad tag", () => {
  const e = error(`8=FIX.4.4${S}9=16${S}35=0${S}34=1${S}12x=1${S}10=245${S}`);
  expect(e.rule).toBe("bad_tag");
  expect(e.position).toBe(26);
});

test("a CheckSum of four digits, or of two, has the wrong format", () => {
  for (const cs of ["10=1234", "10=12"]) {
    const e = error(`8=FIX.4.4${S}9=10${S}35=0${S}34=1${S}${cs}${S}`);
    expect(e.rule).toBe("checksum_format");
    expect(e.position).toBe(26);
  }
});

test("fewer than three fields is a header order error", () => {
  for (const text of ["8=FIX.4.4|9=5|", `8=FIX.4.4${S}9=5${S}`, "8=FIX.4.4|"]) {
    expect(error(text).rule).toBe("header_order");
  }
});

test("the second field must be 9 and the third 35, and the error points at the field that is wrong", () => {
  const second = error(`8=FIX.4.4${S}35=0${S}9=5${S}10=000${S}`);
  expect([second.rule, second.position]).toEqual(["header_order", 11]);
  const third = error(`8=FIX.4.4${S}9=5${S}34=1${S}10=000${S}`);
  expect([third.rule, third.position]).toEqual(["header_order", 15]);
});

test("a BodyLength that is not a whole number is a body length error at field 9", () => {
  for (const v of ["x", "1.5", "5a", ""]) {
    const e = error(`8=FIX.4.4${S}9=${v}${S}35=0${S}10=000${S}`);
    expect([e.rule, e.position]).toEqual(["body_length", 11]);
  }
});

test("every error text is Message N: <problem> at position P, and the problem is never empty", () => {
  const malformed = [
    `8=FIX.4.4${S}9=5${S}35A${S}10=000${S}`,
    `8=FIX.4.4${S}9=5${S}35=0${S}0=x${S}10=000${S}`,
    `8=FIX.4.4${S}35=0${S}9=5${S}10=000${S}`,
    `8=FIX.4.4${S}9=5${S}35=0${S}`,
    `8=FIX.4.4${S}9=5${S}35=0${S}10=12${S}`,
    `8=FIX.4.4${S}9=x${S}35=0${S}10=000${S}`,
    `8=FIX.4.4${S}9=6${S}35=0${S}10=000${S}`,
    `8=FIX.4.4${S}9=5${S}35=0${S}10=000${S}`,
  ];
  const rules = [];
  for (const text of malformed) {
    const e = error(text);
    rules.push(e.rule);
    const m = /^Message 1: (\S.*) at position (\d+)$/.exec(e.text);
    expect(m, e.text).not.toBeNull();
    expect(m[1].trim().length).toBeGreaterThan(2);
    expect(Number(m[2])).toBe(e.position);
  }
  expect(rules).toEqual([
    "field_without_equals", "bad_tag", "header_order", "missing_checksum", "checksum_format",
    "body_length", "body_length", "checksum",
  ]);
});
