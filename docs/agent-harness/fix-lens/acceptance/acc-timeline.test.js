import { test, expect } from "vitest";
import { splitMessages } from "../src/framing.js";
import { timeline } from "../src/timeline.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
const m = (seq, type, extra = [], dir = ["A", "B"], v = "FIX.4.4") =>
  fixmsg(v, [[35, type], [49, dir[0]], [56, dir[1]], [34, seq], ...extra]);
const run = (...msgs) => {
  const text = msgs.join("\n");
  return timeline(splitMessages(text));
};
const names = (evs) => evs.map((e) => e.name);

// The exact event keys are checked in acc-events.test.js (v1.2 adds origClOrdId and execRefId).
test("an event carries its sender, target and message number", () => {
  const [e] = run(m(1, "A"));
  expect([e.sender, e.target, e.number]).toEqual(["A", "B", 1]);
});

test("session event names from the PRD table", () => {
  expect(names(run(m(1, "A"), m(2, "0"), m(3, "1"), m(4, "2"), m(5, "3"), m(6, "j"), m(7, "5"))))
    .toEqual(["Logon", "Heartbeat", "TestRequest", "ResendRequest", "SessionReject", "BusinessReject", "Logout"]);
});

test("a gap comes before the message, with expected and received", () => {
  const evs = run(m(1, "0"), m(2, "0"), m(5, "0"));
  expect(names(evs)).toEqual(["Heartbeat", "Heartbeat", "SequenceGap", "Heartbeat"]);
  expect(evs[2].detail).toBe("expected 3, received 5");
});

test("directions are tracked separately; first message never gaps", () => {
  expect(names(run(m(7, "0"), m(1, "0", [], ["B", "A"]), m(8, "0"), m(2, "0", [], ["B", "A"]))))
    .not.toContain("SequenceGap");
});

test("lower number: no event and expected unchanged", () => {
  expect(names(run(m(8, "0"), m(9, "0"), m(5, "0"), m(10, "0")))).not.toContain("SequenceGap");
});

test("PossDup does not gap or advance", () => {
  expect(names(run(m(1, "0"), m(9, "0", [[43, "Y"]]), m(2, "0")))).not.toContain("SequenceGap");
});

test("GapFill and Reset, NewSeqNo sets the expected number", () => {
  const evs = run(m(1, "0"), m(2, "4", [[123, "Y"], [36, "10"]]), m(10, "0"));
  expect(names(evs)).toEqual(["Heartbeat", "GapFill", "Heartbeat"]);
  expect(names(run(m(1, "0"), m(50, "4", [[36, "60"]]), m(60, "0")))).toEqual(["Heartbeat", "Reset", "Heartbeat"]);
});

test("Logon with 141=Y resets the expected number to 1", () => {
  expect(names(run(m(7, "0"), m(1, "A", [[141, "Y"]]), m(2, "0")))).not.toContain("SequenceGap");
});

test("ExecutionReport mapping per version, and order fields", () => {
  const er = (v, x) => run(m(1, "8", [[150, x], [11, "C1"], [37, "O1"]], ["A", "B"], v))[0];
  expect(er("FIX.4.4", "0").name).toBe("Acknowledgement");
  expect(er("FIX.4.4", "F").name).toBe("Fill");
  expect(er("FIX.4.2", "2").name).toBe("Fill");
  expect(er("FIX.4.4", "2").name).toBe("ExecutionReport (ExecType 2)");
  expect(er("FIX.4.4", "4").name).toBe("Cancelled");
  expect(er("FIX.4.4", "5").name).toBe("Replaced");
  const e = er("FIX.4.4", "0");
  expect([e.kind, e.clOrdId, e.orderId]).toEqual(["order", "C1", "O1"]);
  expect(run(m(1, "D", [[11, "C1"]]))[0].name).toBe("NewOrder");
});

test("a message without a usable 34 changes nothing, even a Logon with 141=Y", () => {
  const noSeq = fixmsg("FIX.4.4", [[35, "A"], [49, "A"], [56, "B"], [141, "Y"]]);
  const evs = run(m(7, "0"), noSeq, m(10, "0"));
  expect(evs.find((e) => e.name === "SequenceGap").detail).toBe("expected 8, received 10");
});

test("a NewSeqNo that is not a positive integer falls back to 34 + 1", () => {
  expect(names(run(m(1, "0"), m(5, "4", [[36, "0"]]), m(6, "0")))).not.toContain("SequenceGap");
});

test("a missing 49 and an empty 49 are the same direction", () => {
  const a = fixmsg("FIX.4.4", [[35, "0"], [56, "SELL"], [34, "1"]]);
  const b = fixmsg("FIX.4.4", [[35, "0"], [49, ""], [56, "SELL"], [34, "5"]]);
  expect(run(a, b).find((e) => e.name === "SequenceGap").detail).toBe("expected 2, received 5");
});

test("event kinds are session or order only", () => {
  const evs = run(m(1, "0"), m(3, "D", [[11, "C1"]]));
  expect(evs.map((e) => e.kind)).toEqual(["session", "session", "order"]);
});

test("a GapFill above the expected number is preceded by a SequenceGap", () => {
  const evs = run(m(1, "0"), m(5, "4", [[123, "Y"], [36, "10"]]), m(10, "0"));
  expect(names(evs)).toEqual(["Heartbeat", "SequenceGap", "GapFill", "Heartbeat"]);
  expect(evs[1].detail).toBe("expected 2, received 5");
});
