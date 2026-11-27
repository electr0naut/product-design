import { test, expect } from "vitest";
import { checkLimits } from "../src/limits.js";

const V1 = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";

test("result keys", () => {
  expect(Object.keys(checkLimits(V1)).sort()).toEqual(["bytes", "messages", "ok", "warning"]);
});

// v1.3 (FXL-19): the limits are 10,485,760 bytes and 10,000 messages. The two tests that pinned 1,048,576 and
// 1,000 were retired with a `retire_hidden` decision and replaced by the three below.
test("byte limit is UTF-8 and inclusive at 10,485,760 (v1.3)", () => {
  const at = checkLimits("a".repeat(10485760));
  expect([at.ok, at.bytes, at.warning]).toEqual([true, 10485760, null]);
  const r = checkLimits("a".repeat(10485761));
  expect([r.ok, r.bytes]).toEqual([false, 10485761]);
  // two bytes per character: 5,242,880 characters are exactly at the limit, one more is over it
  expect(checkLimits("é".repeat(5242880)).ok).toBe(true);
  const multi = checkLimits("a".repeat(10485759) + "é");
  expect([multi.ok, multi.bytes]).toEqual([false, 10485761]);
});

test("message limit: 10,000 accepted, 10,001 refused, warning names both numbers (v1.3)", () => {
  const at = checkLimits((V1 + "\n").repeat(10000));
  expect([at.ok, at.messages, at.warning]).toEqual([true, 10000, null]);
  const r = checkLimits((V1 + "\n").repeat(10001));
  expect([r.ok, r.messages]).toEqual([false, 10001]);
  expect(r.bytes).toBeLessThan(10485760);
  const digits = r.warning.replace(/[,.\s\u00a0\u202f']/g, "");
  expect(digits).toContain("10001");
  expect(digits).toContain(String(r.bytes));
  expect(r.warning).toMatch(/split/i);
});

test("what v1.2 refused is accepted: 1,048,577 bytes and 1,001 messages (v1.3)", () => {
  const bytes = checkLimits("a".repeat(1048577));
  expect([bytes.ok, bytes.bytes, bytes.warning]).toEqual([true, 1048577, null]);
  const count = checkLimits((V1 + "\n").repeat(1001));
  expect([count.ok, count.messages, count.warning]).toEqual([true, 1001, null]);
});
