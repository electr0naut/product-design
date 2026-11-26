import { test, expect } from "vitest";
import { checkLimits } from "../src/limits.js";

const V1 = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";

test("result keys", () => {
  expect(Object.keys(checkLimits(V1)).sort()).toEqual(["bytes", "messages", "ok", "warning"]);
});

test("byte limit is UTF-8 and inclusive at 1,048,576", () => {
  expect(checkLimits("a".repeat(1048576)).ok).toBe(true);
  const r = checkLimits("a".repeat(1048577));
  expect([r.ok, r.bytes]).toEqual([false, 1048577]);
  expect(checkLimits("é".repeat(524289)).ok).toBe(false);
});

test("message limit: 1,000 accepted, 1,001 refused, warning names both numbers", () => {
  expect(checkLimits((V1 + "\n").repeat(1000)).ok).toBe(true);
  const r = checkLimits((V1 + "\n").repeat(1001));
  expect([r.ok, r.messages]).toEqual([false, 1001]);
  const digits = r.warning.replace(/[,.\s\u00a0\u202f']/g, "");
  expect(digits).toContain("1001");
  expect(digits).toContain(String(r.bytes));
});
