import { test, expect } from "vitest";
import { splitMessages, checkMessage } from "../src/framing.js";

const S = "\x01";
const V1 = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";
const check = (text, i = 0) => checkMessage(splitMessages(text)[i], text);

test("reference vector is valid with SOH and with pipe (CheckSum over SOH)", () => {
  expect(check(V1.replaceAll("|", S))).toBeNull();
  expect(check(V1)).toBeNull();
});

test("a CheckSum computed over pipe bytes is rejected", () => {
  const e = check("8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=095|");
  expect(e.rule).toBe("checksum");
});

test("BodyLength counts UTF-8 bytes", () => {
  expect(check("8=FIX.4.4|9=29|35=0|34=2|49=A|56=B|58=café|10=200|")).toBeNull();
});

test("wrong BodyLength: rule, position of field 9, and plain-words text", () => {
  const e = check("8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|");
  expect(e.rule).toBe("body_length");
  expect(e.position).toBe(11);
  expect(e.text).toMatch(/^Message 1: .*says 21, actual 20.* at position 11$/);
});

test("missing CheckSum is reported, not dropped", () => {
  const text = "8=FIX.4.4|9=5|35=0|\n" + V1;
  const e = check(text, 0);
  expect(e.rule).toBe("missing_checksum");
  expect(e.text).toMatch(/^Message 1: .*CheckSum.* at position \d+$/);
  expect(check(text, 1)).toBeNull();
});

test("CheckSum that is not 3 digits", () => {
  expect(check("8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=12|").rule).toBe("checksum_format");
});

test("header order", () => {
  expect(check("8=FIX.4.4|35=0|9=5|10=000|").rule).toBe("header_order");
});

// v1.2: with a text delimiter, "|ab=x" is not a field boundary (design section 3, step 4), so only all-digit
// forms can be bad tags there. With the SOH character every piece is a field.
test("bad tags: 07 and 0 with a pipe, and a non-number with the SOH character", () => {
  for (const t of ["07", "0"]) {
    expect(check(`8=FIX.4.4|9=20|35=0|${t}=x|10=000|`).rule).toBe("bad_tag");
  }
  expect(check("8=FIX.4.4|9=20|35=0|ab=x|10=000|".replaceAll("|", S)).rule).toBe("bad_tag");
});

test("message numbers count every candidate, valid or not", () => {
  const text = V1 + "\n8=FIX.4.4|9=21|35=0|34=1|49=A|56=B|10=125|\n";
  expect(check(text, 1).number).toBe(2);
  expect(check(text, 1).text.startsWith("Message 2: ")).toBe(true);
});
