import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";

const V1 = "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|";
const V2 = "8=FIX.4.4|9=20|35=0|34=2|49=A|56=B|10=126|";
const BAD = "8=FIX.4.4|9=21|35=0|34=9|49=A|56=B|10=125|";

test("result keys", () => {
  expect(Object.keys(analyse(V1)).sort()).toEqual(["decoded", "errors", "limit", "messages", "ok", "timeline"]);
});

test("a malformed message between two valid ones", () => {
  const r = analyse([V1, BAD, V2].join("\n"));
  expect(r.ok).toBe(true);
  expect(r.errors.length).toBe(1);
  expect(r.errors[0].number).toBe(2);
  expect(r.decoded.length).toBe(2);
  expect(r.timeline.map((e) => e.number)).toEqual([1, 3]);
});

test("over a limit nothing is decoded", () => {
  const r = analyse((V1 + "\n").repeat(1001));
  expect(r.ok).toBe(false);
  expect([r.messages.length, r.errors.length, r.decoded.length, r.timeline.length]).toEqual([0, 0, 0, 0]);
});

test("100 messages in under 5 seconds", () => {
  const t0 = performance.now();
  analyse((V1 + "\n").repeat(100));
  expect(performance.now() - t0).toBeLessThan(5000);
});
