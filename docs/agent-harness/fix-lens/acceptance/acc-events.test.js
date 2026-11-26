// FXL-10: cancel and replace requests, trade cancels, trade corrections and order status (PRD v1.2 AC-009,
// AC-010, TR-003; design v1.2 section 7 steps 4 to 6).
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { splitMessages } from "../src/framing.js";
import { timeline } from "../src/timeline.js";
import { executionKind } from "../src/execution.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
let seq = 0;
const m = (type, extra = [], v = "FIX.4.4") => fixmsg(v, [[35, type], [49, "A"], [56, "B"], [34, ++seq], ...extra]);
const er = (extra, v = "FIX.4.4") => m("8", [[37, "O1"], [11, "C1"], [17, "E1"], ...extra], v);
const kindOf = (text) => executionKind(splitMessages(text)[0]);
const events = (...msgs) => { const r = analyse(msgs.join("\n")); expect(r.errors).toEqual([]); return r.timeline; };

test("event keys include origClOrdId and execRefId", () => {
  const [e] = events(m("0"));
  expect(Object.keys(e).sort()).toEqual(["clOrdId", "detail", "execRefId", "kind", "name", "number", "orderId",
    "origClOrdId", "sendingTime", "sender", "seqNum", "target"].sort());
  expect([e.origClOrdId, e.execRefId, e.kind]).toEqual([null, null, "session"]);
});

test("CancelRequest, ReplaceRequest and CancelReject are order events with their ids", () => {
  const evs = events(m("F", [[11, "C2"], [41, "C1"], [37, "O1"]]), m("G", [[11, "C3"], [41, "C2"]]), m("9", [[11, "C3"], [41, "C2"], [37, "NONE"]]));
  expect(evs.map((e) => [e.name, e.kind])).toEqual([["CancelRequest", "order"], ["ReplaceRequest", "order"], ["CancelReject", "order"]]);
  expect(evs.map((e) => [e.clOrdId, e.origClOrdId, e.orderId])).toEqual([["C2", "C1", "O1"], ["C3", "C2", null], ["C3", "C2", "NONE"]]);
  expect(evs.every((e) => e.execRefId === null)).toBe(true);
});

test("FIX 4.4 execution kinds by ExecType", () => {
  const table = [["H", "TradeCancel"], ["G", "TradeCorrect"], ["I", "OrderStatus"], ["F", "Fill"], ["0", "Acknowledgement"],
    ["4", "Cancelled"], ["5", "Replaced"], ["8", "ExecutionReport (ExecType 8)"], ["2", "ExecutionReport (ExecType 2)"]];
  for (const [x, name] of table) expect(kindOf(er([[150, x]]))).toBe(name);
  expect(kindOf(er([]))).toBe("ExecutionReport (no ExecType)");
});

test("FIX 4.2: ExecTransType is checked first, then ExecType", () => {
  const k = (extra) => kindOf(er(extra, "FIX.4.2"));
  expect(k([[20, "1"], [150, "2"]])).toBe("TradeCancel");
  expect(k([[20, "2"], [150, "1"]])).toBe("TradeCorrect");
  expect(k([[20, "3"], [150, "2"]])).toBe("OrderStatus");
  expect(k([[20, "0"], [150, "2"]])).toBe("Fill");
  expect(k([[150, "1"]])).toBe("Fill");
  expect(k([[20, "0"], [150, "0"]])).toBe("Acknowledgement");
});

test("the versions do not borrow each other's rules", () => {
  expect(kindOf(er([[20, "1"], [150, "F"]]))).toBe("Fill");
  expect(kindOf(er([[150, "H"]], "FIX.4.2"))).toBe("ExecutionReport (ExecType H)");
  expect(kindOf(er([[150, "F"]], "FIX.4.2"))).toBe("ExecutionReport (ExecType F)");
});

test("an unsupported version maps only 0, 4 and 5", () => {
  expect(kindOf(er([[20, "1"], [150, "2"]], "FIX.4.1"))).toBe("ExecutionReport (ExecType 2)");
  expect(kindOf(er([[150, "H"]], "FIX.5.0"))).toBe("ExecutionReport (ExecType H)");
  expect(kindOf(er([[150, "4"]], "FIX.4.1"))).toBe("Cancelled");
});

test("executionKind gives the same answer for a candidate and for the decoded message", () => {
  for (const text of [er([[150, "G"], [19, "E0"]]), er([[20, "1"], [150, "2"]], "FIX.4.2"), er([[150, "F"]])]) {
    expect(executionKind(analyse(text).decoded[0])).toBe(kindOf(text));
  }
});

test("the timeline names every ExecutionReport with executionKind", () => {
  const msgs = [er([[150, "H"], [19, "E0"]]), er([[150, "G"], [19, "E0"]]), er([[150, "I"]]), er([[150, "F"]]),
    er([[20, "1"], [150, "2"], [19, "E0"]], "FIX.4.2"), er([[20, "3"], [150, "2"]], "FIX.4.2"), er([[150, "A"]])];
  const text = msgs.join("\n");
  const cands = splitMessages(text);
  expect(timeline(cands).filter((e) => e.name !== "SequenceGap").map((e) => e.name)).toEqual(cands.map(executionKind));
});

test("execRefId is tag 19 on TradeCancel and TradeCorrect only", () => {
  const evs = events(er([[150, "H"], [19, "E7"]]), er([[150, "G"], [19, "E8"]]), er([[150, "F"], [19, "E9"]]),
    er([[20, "2"], [150, "1"], [19, "X3"]], "FIX.4.2"));
  expect(evs.filter((e) => e.name !== "SequenceGap").map((e) => [e.name, e.execRefId]))
    .toEqual([["TradeCancel", "E7"], ["TradeCorrect", "E8"], ["Fill", null], ["TradeCorrect", "X3"]]);
});

test("a FIX 4.2 trade cancel is no longer shown as a Fill", () => {
  const evs = events(er([[20, "0"], [150, "2"], [32, "100"], [31, "50"]], "FIX.4.2"), er([[20, "1"], [150, "2"], [19, "E1"]], "FIX.4.2"));
  expect(evs.filter((e) => e.kind === "order").map((e) => e.name)).toEqual(["Fill", "TradeCancel"]);
});

test("sequence gaps still work around the new events", () => {
  const a = fixmsg("FIX.4.4", [[35, "F"], [49, "X"], [56, "Y"], [34, "1"], [11, "C2"], [41, "C1"]]);
  const b = fixmsg("FIX.4.4", [[35, "G"], [49, "X"], [56, "Y"], [34, "4"], [11, "C3"], [41, "C2"]]);
  const evs = events(a, b);
  expect(evs.map((e) => e.name)).toEqual(["CancelRequest", "SequenceGap", "ReplaceRequest"]);
  expect(evs[1].detail).toBe("expected 2, received 4");
});
