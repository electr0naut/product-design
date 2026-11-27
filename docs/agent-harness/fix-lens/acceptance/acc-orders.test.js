// FXL-11: grouping messages into orders (PRD v1.2 AC-035; design v1.2 section 12).
import { test, expect } from "vitest";
import { analyse } from "../src/analyse.js";
import { orderGroups, findOrder } from "../src/orders.js";

const S = "\x01";
function fixmsg(begin, fields) {
  const body = fields.map(([t, v]) => `${t}=${v}${S}`).join("");
  const head = `8=${begin}${S}9=${new TextEncoder().encode(body).length}${S}`;
  const sum = [...new TextEncoder().encode(head + body)].reduce((a, b) => a + b, 0) % 256;
  return (head + body + `10=${String(sum).padStart(3, "0")}${S}`).replaceAll(S, "|");
}
// A sends the orders and B answers: reports (8) and cancel rejects (9) go from B to A, as in a real log (v1.4).
const log = (...rows) => {
  const text = rows.map(([type, ...extra], i) => {
    const [from, to] = type === "8" || type === "9" ? ["B", "A"] : ["A", "B"];
    return fixmsg("FIX.4.4", [[35, type], [49, from], [56, to], [34, i + 1], ...extra]);
  }).join("\n");
  const r = analyse(text);
  expect(r.errors).toEqual([]);
  return r.decoded;
};

test("group keys, and grouping by a shared ClOrdID or OrderID", () => {
  const g = orderGroups(log(["D", [11, "C1"]], ["8", [11, "C1"], [37, "O1"], [150, "0"]], ["8", [37, "O1"], [150, "F"]], ["0"]));
  expect(g.length).toBe(1);
  expect(Object.keys(g[0]).sort()).toEqual(["clOrdIds", "numbers", "orderIds"]);
  expect(g[0]).toEqual({ clOrdIds: ["C1"], orderIds: ["O1"], numbers: [1, 2, 3] });
});

test("a cancel/replace chain through OrigClOrdID is one order", () => {
  const g = orderGroups(log(["D", [11, "C1"]], ["G", [11, "C2"], [41, "C1"]], ["8", [11, "C2"], [37, "O1"], [150, "5"]], ["F", [11, "C3"], [41, "C2"]]));
  expect(g).toEqual([{ clOrdIds: ["C1", "C2", "C3"], orderIds: ["O1"], numbers: [1, 2, 3, 4] }]);
});

test("two orders joined by a later message become one group, in order of first appearance", () => {
  const g = orderGroups(log(["D", [11, "A"]], ["D", [11, "B"]], ["8", [11, "A"], [37, "X"], [150, "0"]], ["8", [11, "B"], [37, "X"], [150, "0"]], ["D", [11, "Z"]]));
  expect(g).toEqual([{ clOrdIds: ["A", "B"], orderIds: ["X"], numbers: [1, 2, 3, 4] }, { clOrdIds: ["Z"], orderIds: [], numbers: [5] }]);
});

test("37=NONE is not an identifier, and the comparison is exact", () => {
  const d = log(["9", [11, "K1"], [37, "NONE"]], ["9", [11, "K2"], [37, "NONE"]], ["9", [11, "K3"], [37, "None"]], ["9", [11, "K4"], [37, "None"]]);
  const g = orderGroups(d);
  expect(g).toEqual([{ clOrdIds: ["K1"], orderIds: [], numbers: [1] }, { clOrdIds: ["K2"], orderIds: [], numbers: [2] },
    { clOrdIds: ["K3", "K4"], orderIds: ["None"], numbers: [3, 4] }]);
  expect(findOrder(g, "NONE")).toBeNull();
});

test("messages without ids, or with empty ids, are in no group", () => {
  expect(orderGroups(log(["0"], ["A", [98, "0"], [108, "30"]], ["D", [11, ""], [55, "X"]]))).toEqual([]);
});

test("findOrder finds a group by any of its ids, or null", () => {
  const g = orderGroups(log(["D", [11, "C1"]], ["G", [11, "C2"], [41, "C1"]], ["8", [11, "C2"], [37, "O1"], [150, "5"]], ["D", [11, "Q"]]));
  for (const id of ["C1", "C2", "O1"]) expect(findOrder(g, id)).toBe(g[0]);
  expect(findOrder(g, "Q")).toBe(g[1]);
  expect(findOrder(g, "nope")).toBeNull();
});

test("ClOrdID and OrderID are separate namespaces", () => {
  const g = orderGroups(log(["D", [11, "SAME"]], ["8", [11, "OTHER"], [37, "SAME"], [150, "0"]]));
  expect(g.length).toBe(2);
});

test("the first value of a repeated tag counts", () => {
  const g = orderGroups(log(["D", [11, "C1"], [11, "C9"]], ["D", [11, "C9"]]));
  expect(g.map((x) => x.clOrdIds)).toEqual([["C1"], ["C9"]]);
});

test("pure: the argument is unchanged and two calls agree", () => {
  const d = log(["D", [11, "C1"]], ["8", [11, "C1"], [37, "O1"], [150, "0"]]);
  const before = JSON.stringify(d);
  expect(orderGroups(d)).toEqual(orderGroups(d));
  expect(JSON.stringify(d)).toBe(before);
});

test("1,000 order messages in under 1 second", () => {
  const rows = [];
  for (let i = 0; i < 500; i++) rows.push(["D", [11, `C${i}`]], ["8", [11, `C${i}`], [37, `O${i}`], [150, "0"]]);
  const d = log(...rows);
  const t0 = performance.now();
  expect(orderGroups(d).length).toBe(500);
  expect(performance.now() - t0).toBeLessThan(1000);
});
