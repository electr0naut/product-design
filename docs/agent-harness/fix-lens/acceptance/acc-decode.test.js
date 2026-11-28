import { test, expect } from "vitest";
import { splitMessages } from "../src/framing.js";
import { decode } from "../src/decode.js";

const LOGON = "8=FIX.4.4|9=67|35=A|34=1|49=CLIENT|56=BROKER|52=20261126-10:00:00.000|98=0|108=30|10=108|";
const UNK = "8=FIX.4.4|9=36|35=0|34=3|49=A|56=B|9999=x|54=Z|58=|10=204|";
const OLD = "8=FIX.4.1|9=20|35=0|34=1|49=A|56=B|10=122|";
const dec = (t) => decode(splitMessages(t)[0], t);

test("result and field keys", () => {
  const d = dec(LOGON);
  expect(Object.keys(d).sort()).toEqual(["beginString", "fields", "label", "number", "supported"]);
  expect(Object.keys(d.fields[0]).sort()).toEqual(["enumName", "known", "name", "tag", "value"]);
});

test("label, names and enum meanings", () => {
  const d = dec(LOGON);
  expect(d.label).toBe("Message 1: Logon");
  expect(d.supported).toBe(true);
  const f35 = d.fields.find((f) => f.tag === 35);
  expect([f35.name, f35.value, f35.enumName, f35.known]).toEqual(["MsgType", "A", "Logon", true]);
  expect(d.fields.find((f) => f.tag === 49).enumName).toBeNull();
  expect(d.fields.map((f) => f.tag)).toEqual([8, 9, 35, 34, 49, 56, 52, 98, 108, 10]);
});

test("unknown tag, unknown enum value and empty value", () => {
  const d = dec(UNK);
  const u = d.fields.find((f) => f.tag === 9999);
  expect([u.name, u.value, u.known]).toEqual(["Unknown tag 9999", "x", false]);
  const side = d.fields.find((f) => f.tag === 54);
  expect([side.value, side.enumName]).toEqual(["Z", "unknown value"]);
  expect(d.fields.find((f) => f.tag === 58).value).toBe("");
});

test("unsupported version", () => {
  const d = dec(OLD);
  expect(d.supported).toBe(false);
  expect(d.label).toBe("Message 1: unsupported version FIX.4.1");
});

test("enum values that name JavaScript built-ins are unknown values", () => {
  const t = "8=FIX.4.4|9=35|35=0|34=1|49=A|56=B|54=constructor|10=240|";
  const f = dec(t).fields.find((x) => x.tag === 54);
  expect([f.value, f.enumName]).toEqual(["constructor", "unknown value"]);
});
