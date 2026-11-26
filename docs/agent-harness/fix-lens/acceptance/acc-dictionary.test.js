import { test, expect } from "vitest";
import { lookup, enumName } from "../src/dictionary.js";

test("argument order is (beginString, tag[, value])", () => {
  expect(lookup("FIX.4.4", 35).name).toBe("MsgType");
  expect(enumName("FIX.4.4", 35, "A")).toBe("Logon");
});

test("core names in both versions", () => {
  for (const v of ["FIX.4.2", "FIX.4.4"]) {
    expect(lookup(v, 8).name).toBe("BeginString");
    expect(lookup(v, 49).name).toBe("SenderCompID");
    expect(lookup(v, 150).name).toBe("ExecType");
    expect(enumName(v, 35, "8")).toBe("ExecutionReport");
    expect(enumName(v, 54, "1")).toBe("Buy");
  }
});

test("ExecType F exists in 4.4 only", () => {
  expect(enumName("FIX.4.4", 150, "F")).toBe("Trade");
  expect(enumName("FIX.4.2", 150, "F")).toBeNull();
});

test("unknown tag, unknown value and unsupported version give null", () => {
  expect(lookup("FIX.4.2", 99999)).toBeNull();
  expect(enumName("FIX.4.4", 54, "Z")).toBeNull();
  expect(lookup("FIX.5.0", 35)).toBeNull();
});

test("lookups ignore Object.prototype built-ins", () => {
  for (const v of ["constructor", "toString", "__proto__", "hasOwnProperty"]) {
    expect(enumName("FIX.4.4", 54, v)).toBeNull();
  }
  expect(lookup("FIX.4.4", "constructor")).toBeNull();
});
