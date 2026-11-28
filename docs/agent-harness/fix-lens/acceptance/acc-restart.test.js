// FXL-24: a session that starts again at 1 (PRD v1.4 TR-003; design v1.4 section 7, step 1).
// Every expected gap follows from the sequence numbers written in the test.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// Each row: [type, from, to, seq, ...more fields]
const timelineOf = (rows, begin = "FIX.4.4") => {
  const r = analyse(rows.map(([type, from, to, seq, ...extra]) => fixmsg(begin, [[35, type], [49, from], [56, to], [34, seq], ...extra])).join("\n"));
  expect(r.errors).toEqual([]);
  return r.timeline;
};
const gaps = (timeline) => timeline.filter((e) => e.name === "SequenceGap").map((e) => [e.number, e.detail]);
const LOGON = [[98, "0"], [108, "30"]];
// A to B: numbers 1 to 8, ending in a Logout (messages 1 to 8).
const FIRST_SESSION = [["A", "A", "B", 1, ...LOGON], ...[2, 3, 4, 5, 6, 7].map((n) => ["0", "A", "B", n]), ["5", "A", "B", 8]];

test("a gap after a Logon numbered 1 without ResetSeqNumFlag is found", () => {
  const t = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 2], ["0", "A", "B", 5]]);
  expect(gaps(t)).toEqual([[11, "expected 3, received 5"]]);
  // the restart itself adds no event: eleven messages and one gap
  expect(t.map((e) => e.name)).toEqual(["Logon", "Heartbeat", "Heartbeat", "Heartbeat", "Heartbeat", "Heartbeat", "Heartbeat", "Logout",
    "Logon", "Heartbeat", "SequenceGap", "Heartbeat"]);
});

test("the same on FIX 4.2", () => {
  const t = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 2], ["0", "A", "B", 5]], "FIX.4.2");
  expect(gaps(t)).toEqual([[11, "expected 3, received 5"]]);
});

test("after the restart the numbers are followed from 1: no gap when they run on", () => {
  const t = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 2], ["0", "A", "B", 3], ["0", "A", "B", 4]]);
  expect(gaps(t)).toEqual([]);
});

test("a second restart is followed too", () => {
  const t = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 2], ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 3]]);
  expect(gaps(t)).toEqual([[12, "expected 2, received 3"]]);
});

test("only the direction of the Logon restarts", () => {
  const t = timelineOf([
    ["A", "A", "B", 1, ...LOGON], ["A", "B", "A", 1, ...LOGON],
    ["0", "A", "B", 2], ["0", "B", "A", 2], ["0", "A", "B", 3], ["0", "B", "A", 3],
    ["A", "A", "B", 1, ...LOGON],
    ["0", "B", "A", 4],
    ["0", "B", "A", 6],
    ["0", "A", "B", 2],
  ]);
  // B to A was not restarted: 4 runs on, and 6 is a gap against 5. A to B runs on from 1 to 2.
  expect(gaps(t)).toEqual([[9, "expected 5, received 6"]]);
});

test("when the other side answers with its own Logon numbered 1, both directions restart", () => {
  const t = timelineOf([
    ["A", "A", "B", 1, ...LOGON], ["A", "B", "A", 1, ...LOGON], ["0", "A", "B", 2], ["0", "B", "A", 2], ["0", "B", "A", 3],
    ["A", "A", "B", 1, ...LOGON], ["A", "B", "A", 1, ...LOGON],
    ["0", "B", "A", 3],
    ["0", "A", "B", 4],
  ]);
  expect(gaps(t)).toEqual([[8, "expected 2, received 3"], [9, "expected 2, received 4"]]);
});

test("a Logon numbered 1 with PossDupFlag restarts nothing", () => {
  const t = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, [43, "Y"], ...LOGON], ["0", "A", "B", 9], ["0", "A", "B", 12]]);
  expect(gaps(t)).toEqual([[11, "expected 10, received 12"]]);
});

test("another message numbered 1 restarts nothing: only a Logon does", () => {
  for (const type of ["0", "5", "1", "D"]) {
    const extra = type === "1" ? [[112, "T"]] : type === "D" ? [[11, "C1"]] : [];
    const t = timelineOf([...FIRST_SESSION, [type, "A", "B", 1, ...extra], ["0", "A", "B", 2], ["0", "A", "B", 11]]);
    expect(gaps(t)).toEqual([[11, "expected 9, received 11"]]);
  }
});

test("a Logon with a lower number other than 1 restarts nothing, and one that runs on is no gap", () => {
  const lower = timelineOf([...FIRST_SESSION, ["A", "A", "B", 2, ...LOGON], ["0", "A", "B", 3], ["0", "A", "B", 10]]);
  expect(gaps(lower)).toEqual([[11, "expected 9, received 10"]]);
  // a reconnection that continues the numbers
  const runsOn = timelineOf([...FIRST_SESSION, ["A", "A", "B", 9, ...LOGON], ["0", "A", "B", 10], ["0", "A", "B", 11]]);
  expect(gaps(runsOn)).toEqual([]);
});

test("a Logon numbered 1 as the first message of its direction makes no gap and is followed", () => {
  const t = timelineOf([["0", "B", "A", 40], ["A", "A", "B", 1, ...LOGON], ["0", "A", "B", 3]]);
  expect(gaps(t)).toEqual([[3, "expected 2, received 3"]]);
});

test("ResetSeqNumFlag still restarts, with or without the number 1", () => {
  const withOne = timelineOf([...FIRST_SESSION, ["A", "A", "B", 1, [141, "Y"], ...LOGON], ["0", "A", "B", 3]]);
  expect(gaps(withOne)).toEqual([[10, "expected 2, received 3"]]);
  // 141=Y on a Logon numbered 4: expected becomes 1, so 4 is itself a gap against 1, and 5 runs on
  const withFour = timelineOf([...FIRST_SESSION, ["A", "A", "B", 4, [141, "Y"], ...LOGON], ["0", "A", "B", 5]]);
  expect(gaps(withFour)).toEqual([[9, "expected 1, received 4"]]);
});
