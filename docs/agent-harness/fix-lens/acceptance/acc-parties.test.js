// FXL-22: ids are read within their parties (PRD v1.4 AC-035, AC-036, AC-051; design v1.4 section 12).
// Every expected group follows from who sends each message; none comes from the product.
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { orderGroups, findOrder } from "../src/orders.js";
import { applyFilters } from "../src/filters.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// m(type, from, to, ...fields): from and to may be null, and the tag is then left out.
const m = (type, from, to, ...extra) => [[35, type], ...(from === null ? [] : [[49, from]]), ...(to === null ? [] : [[56, to]]), ...extra];
const decodeAs = (begin, rows) => {
  const r = analyse(rows.map((fields) => fixmsg(begin, fields)).join("\n"));
  expect(r.errors).toEqual([]);
  return r.decoded;
};
const decode = (...rows) => decodeAs("FIX.4.4", rows);
const numbers = (groups) => groups.map((g) => g.numbers);
const NOFILTER = { account: null, senderCompId: null, senderSubId: null, targetCompId: null, targetSubId: null };

// Two clients of one broker both use ClOrdID 1 (the validation's finding FL-02).
const TWO_CLIENTS = [
  m("D", "CLI1", "BRK", [11, "1"], [1, "ACC1"], [55, "AAA"], [54, "1"], [38, "100"]),
  m("D", "CLI2", "BRK", [11, "1"], [1, "ACC2"], [55, "BBB"], [54, "2"], [38, "50"]),
  m("8", "BRK", "CLI1", [37, "O-1"], [11, "1"], [17, "E1"], [150, "F"], [55, "AAA"], [54, "1"], [32, "100"], [31, "5"]),
  m("8", "BRK", "CLI2", [37, "O-2"], [11, "1"], [17, "E2"], [150, "F"], [55, "BBB"], [54, "2"], [32, "50"], [31, "7"]),
];
// One client, two venues that both number their orders from 1 (FL-01).
const TWO_VENUES = [
  m("D", "CLI", "VENUEA", [11, "A1"], [55, "ACME"], [54, "1"], [38, "100"]),
  m("D", "CLI", "VENUEB", [11, "B1"], [55, "ACME"], [54, "1"], [38, "200"]),
  m("8", "VENUEA", "CLI", [37, "1"], [11, "A1"], [17, "1"], [150, "F"], [55, "ACME"], [54, "1"], [32, "100"], [31, "10"]),
  m("8", "VENUEB", "CLI", [37, "1"], [11, "B1"], [17, "1"], [150, "F"], [55, "ACME"], [54, "1"], [32, "200"], [31, "11"]),
];
// Order A has ClOrdID 1001; order B was given OrderID 1001 by the broker (FL-03).
const SHARED_VALUE = [
  m("D", "CLI1", "BRK", [11, "1001"], [55, "AAA"], [54, "1"], [38, "100"]),
  m("D", "CLI2", "BRK", [11, "ZZ9"], [55, "BBB"], [54, "2"], [38, "50"]),
  m("8", "BRK", "CLI1", [37, "7"], [11, "1001"], [17, "E1"], [150, "0"]),
  m("8", "BRK", "CLI2", [37, "1001"], [11, "ZZ9"], [17, "E2"], [150, "F"], [55, "BBB"], [54, "2"], [32, "50"], [31, "7"]),
];

test("two clients that use the same ClOrdID have two orders", () => {
  expect(orderGroups(decode(...TWO_CLIENTS))).toEqual([
    { clOrdIds: ["1"], orderIds: ["O-1"], numbers: [1, 3] },
    { clOrdIds: ["1"], orderIds: ["O-2"], numbers: [2, 4] },
  ]);
});

test("the same on FIX 4.2", () => {
  const rows = TWO_CLIENTS.map((fields) => fields.map(([t, v]) => (t === 150 ? [150, "2"] : [t, v])));
  expect(numbers(orderGroups(decodeAs("FIX.4.2", rows)))).toEqual([[1, 3], [2, 4]]);
});

test("the Account filter keeps to its own client when ClOrdIDs collide", () => {
  const d = decode(...TWO_CLIENTS);
  expect(applyFilters(d, { ...NOFILTER, account: "ACC1" }).map((x) => x.number)).toEqual([1, 3]);
  expect(applyFilters(d, { ...NOFILTER, account: "ACC2" }).map((x) => x.number)).toEqual([2, 4]);
});

test("two venues that use the same OrderID have two orders", () => {
  expect(orderGroups(decode(...TWO_VENUES))).toEqual([
    { clOrdIds: ["A1"], orderIds: ["1"], numbers: [1, 3] },
    { clOrdIds: ["B1"], orderIds: ["1"], numbers: [2, 4] },
  ]);
});

test("an order, its reports, a cancel request and a cancel reject on one session are one order", () => {
  const g = orderGroups(decode(
    m("D", "CLI", "BRK", [11, "C1"]),
    m("8", "BRK", "CLI", [11, "C1"], [37, "O1"], [150, "0"]),
    m("F", "CLI", "BRK", [11, "C2"], [41, "C1"], [37, "O1"]),
    m("9", "BRK", "CLI", [11, "C2"], [41, "C1"], [37, "O1"]),
    m("8", "BRK", "CLI", [37, "O1"], [150, "F"]),
  ));
  expect(g).toEqual([{ clOrdIds: ["C1", "C2"], orderIds: ["O1"], numbers: [1, 2, 3, 4, 5] }]);
});

test("the client of a report is its TargetCompID, and of any other message its SenderCompID", () => {
  // BRK is itself the client of an order it sends to CLI, with the ClOrdID that CLI used towards BRK.
  const g = orderGroups(decode(
    m("D", "CLI", "BRK", [11, "X"]),
    m("D", "BRK", "CLI", [11, "X"]),
    m("8", "CLI", "BRK", [11, "X"], [37, "R1"], [150, "0"]),
    m("8", "BRK", "CLI", [11, "X"], [37, "R1"], [150, "0"]),
  ));
  expect(g).toEqual([
    { clOrdIds: ["X"], orderIds: ["R1"], numbers: [1, 4] },
    { clOrdIds: ["X"], orderIds: ["R1"], numbers: [2, 3] },
  ]);
});

test("the executing party of a request is its TargetCompID: a cancel request joins by OrderID alone", () => {
  const g = orderGroups(decode(
    m("8", "BRK", "CLI", [37, "O1"], [150, "0"]),
    m("F", "CLI", "BRK", [11, "C5"], [37, "O1"]),
    m("F", "CLI", "OTHER", [11, "C6"], [37, "O1"]),
  ));
  expect(g).toEqual([
    { clOrdIds: ["C5"], orderIds: ["O1"], numbers: [1, 2] },
    { clOrdIds: ["C6"], orderIds: ["O1"], numbers: [3] },
  ]);
});

test("a copy of a report sent to a third CompID joins its order through the OrderID", () => {
  const g = orderGroups(decode(
    m("D", "CLI", "BRK", [11, "C1"]),
    m("8", "BRK", "CLI", [11, "C1"], [37, "O1"], [17, "E1"], [150, "F"]),
    m("8", "BRK", "DROP", [11, "C1"], [37, "O1"], [17, "E1"], [150, "F"]),
    m("8", "BRK2", "CLI", [11, "C7"], [37, "O1"], [17, "E1"], [150, "F"]),
  ));
  expect(g).toEqual([
    { clOrdIds: ["C1"], orderIds: ["O1"], numbers: [1, 2, 3] },
    { clOrdIds: ["C7"], orderIds: ["O1"], numbers: [4] },
  ]);
});

test("a missing SenderCompID or TargetCompID is the empty party", () => {
  // 1 and 2: client "" on both. 3: client A. 4: a report without 56 has client "", so it joins 1 and 2, not 3.
  const g = orderGroups(decode(
    m("D", null, null, [11, "C1"]),
    m("8", null, null, [11, "C1"], [37, "O1"], [150, "0"]),
    m("D", "A", null, [11, "C1"]),
    m("8", "A", null, [11, "C1"], [37, "O2"], [150, "0"]),
  ));
  expect(g).toEqual([
    { clOrdIds: ["C1"], orderIds: ["O1", "O2"], numbers: [1, 2, 4] },
    { clOrdIds: ["C1"], orderIds: [], numbers: [3] },
  ]);
});

test("the empty party is not a CompID that anyone could send", () => {
  for (const word of ["?", "-", "0", "undefined", "null", "none", "unknown", "UNKNOWN", "N/A"]) {
    // a ClOrdID from no SenderCompID and the same ClOrdID from a sender with that name: two clients
    expect(numbers(orderGroups(decode(m("D", null, "BRK", [11, "C1"]), m("D", word, "BRK", [11, "C1"]))))).toEqual([[1], [2]]);
    // an OrderID from no SenderCompID and the same OrderID from a sender with that name: two executing parties
    expect(numbers(orderGroups(decode(m("8", null, "CLI", [37, "1"], [150, "0"]), m("8", word, "CLI", [37, "1"], [150, "0"]))))).toEqual([[1], [2]]);
    // and the same for a missing TargetCompID
    expect(numbers(orderGroups(decode(m("8", "BRK", null, [11, "C1"], [150, "0"]), m("8", "BRK", word, [11, "C1"], [150, "0"]))))).toEqual([[1], [2]]);
  }
});

test("parties are compared exactly, and a party and a value never run together", () => {
  expect(numbers(orderGroups(decode(m("D", "CLI", "BRK", [11, "C1"]), m("D", "cli", "BRK", [11, "C1"]))))).toEqual([[1], [2]]);
  // client "A:B" with ClOrdID "C" is not client "A" with ClOrdID "B:C", whatever joins the two parts
  for (const sep of [":", "|", ",", " ", "/", "\"", "\\"]) {
    const g = orderGroups(decode(m("D", `A${sep}B`, "BRK", [11, "C"]), m("D", "A", "BRK", [11, `B${sep}C`])));
    expect(numbers(g)).toEqual([[1], [2]]);
  }
  expect(numbers(orderGroups(decode(m("8", "B", "A:O", [37, "1"], [150, "0"]), m("8", "B:A", "O", [37, "1"], [150, "0"]))))).toEqual([[1], [2]]);
});

test("ClOrdID and OrderID stay separate namespaces within one pair of parties", () => {
  // One CompID is client and executing party at once: its ClOrdID "SAME" is still not its OrderID "SAME".
  const g = orderGroups(decode(m("D", "CLI", "CLI", [11, "SAME"]), m("8", "CLI", "CLI", [11, "OTHER"], [37, "SAME"], [150, "0"])));
  expect(g.length).toBe(2);
});

test("findOrder with a message number returns the order of that message", () => {
  const g = orderGroups(decode(...SHARED_VALUE));
  expect(numbers(g)).toEqual([[1, 3], [2, 4]]);
  expect(findOrder(g, "1001", 4)).toBe(g[1]);
  expect(findOrder(g, "1001", 2)).toBe(g[1]);
  expect(findOrder(g, "1001", 3)).toBe(g[0]);
  expect(findOrder(g, "1001", 1)).toBe(g[0]);
  // the message decides, also when the id is one of another order
  expect(findOrder(g, "7", 4)).toBe(g[1]);
});

test("findOrder without a usable message number looks for the id, as before", () => {
  const g = orderGroups(decode(...SHARED_VALUE));
  expect(findOrder(g, "1001")).toBe(g[0]);
  expect(findOrder(g, "1001", null)).toBe(g[0]);
  expect(findOrder(g, "1001", undefined)).toBe(g[0]);
  expect(findOrder(g, "ZZ9")).toBe(g[1]);
  // no group holds message 99: the id decides
  expect(findOrder(g, "ZZ9", 99)).toBe(g[1]);
  expect(findOrder(g, "nope", 99)).toBeNull();
  expect(findOrder(g, "nope")).toBeNull();
});

test("findOrder with the colliding ClOrdID of two clients", () => {
  const g = orderGroups(decode(...TWO_CLIENTS));
  expect(findOrder(g, "1", 1)).toBe(g[0]);
  expect(findOrder(g, "1", 2)).toBe(g[1]);
  expect(findOrder(g, "1", 4)).toBe(g[1]);
});

test("pure: the argument is unchanged and two calls agree", () => {
  const d = decode(...TWO_CLIENTS);
  const before = JSON.stringify(d);
  expect(orderGroups(d)).toEqual(orderGroups(d));
  expect(JSON.stringify(d)).toBe(before);
});

test("10,000 messages of 50 clients that all count their orders from 0, in under 1 second", () => {
  // Order o: client CLI<o mod 50>, ClOrdID and OrderID both floor(o / 50). 5,000 orders of two messages each.
  const rows = [];
  for (let o = 0; o < 5000; o++) {
    const cli = `CLI${o % 50}`;
    const id = String(Math.floor(o / 50));
    rows.push(m("D", cli, `BRK${o % 50}`, [11, id]), m("8", `BRK${o % 50}`, cli, [11, id], [37, id], [150, "0"]));
  }
  const d = decode(...rows);
  const t0 = performance.now();
  const g = orderGroups(d);
  const ms = performance.now() - t0;
  expect(g.length).toBe(5000);
  expect(g[4999]).toEqual({ clOrdIds: ["99"], orderIds: ["99"], numbers: [9999, 10000] });
  expect(ms).toBeLessThan(1000);
});
