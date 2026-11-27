# FXL-10: the fix pass's change to `test/timeline.test.js` (FXL-10-block-review.md)

Read-only. Nothing unblocked or approved. Gate card `t_587dd3d4` is still blocked.

- base `60b1211023d1f00874e6231d5c98c94501613581` · head of the first gates run `6c7bcd8905e87e3e08252705a9798360bda58d68` · fix head **`80116ec44644d7b6f335f8a99271296b8da16800`** (base, then first, then fix: each an ancestor of the next)

## In short
- **The fix pass only added to the file:** 30 lines, two new tests, **no line removed or changed** (0 removed lines).
- **The existing lines that changed were changed by the first pass,** all in one test, `test_timeline_split_candidates_have_exact_event_keys`: the event list grew from two to three inputs, a `toHaveLength(2)` became an assertion of the four event names, and the key list gained `origClOrdId` and `execRefId`. The ticket says this file is expected to change for those two keys. The implementer recorded it under `modified_existing_tests`.

## 1. Why the first gates run failed
From the host's first gates record for this load (12:46:14, head `6c7bcd8`): `passed: false`, **`missing_acs: ["AC0", "AC9"]`**. That was the only failing item: 8 new tests, all 8 valid, lint passed, `pass_to_pass` passed (exit 0), no removed ids, no deleted test files, nothing over budget. `existing_tests_touched: true`. The fix feedback sent to the implementer was the same two ACs (trigger: gates).
The two added tests are what `implement.json` maps to them (from the run folder):
- AC0: `test_timeline_new_order_events_keep_the_exact_public_shape`
- AC9: `test_timeline_cancel_replace_events_preserve_sequence_rules` (with the two existing PossDup and GapFill tests)

## 2. The fix pass's change: `git diff 6c7bcd8..80116ec -- test/timeline.test.js`, in full
```diff
diff --git a/test/timeline.test.js b/test/timeline.test.js
index 1c09d88..b4dc4da 100644
--- a/test/timeline.test.js
+++ b/test/timeline.test.js
@@ -21,6 +21,23 @@ test("test_timeline_split_candidates_have_exact_event_keys", () => {
   ].sort());
 });
 
+test("test_timeline_new_order_events_keep_the_exact_public_shape", () => {
+  const candidates = messages([
+    ["A", 1], ["D", 2], ["F", 3], ["G", 4], ["9", 5],
+    ["8", 7, [[150, "G"]], "FIX.4.4"]
+  ]);
+  expect(executionKind(candidates[5])).toBe("TradeCorrect");
+  const events = timeline(candidates);
+  expect(names(events)).toEqual([
+    "Logon", "NewOrder", "CancelRequest", "ReplaceRequest", "CancelReject", "SequenceGap", "TradeCorrect"
+  ]);
+  const keys = [
+    "number", "kind", "name", "sendingTime", "sender", "target", "seqNum",
+    "clOrdId", "orderId", "origClOrdId", "execRefId", "detail"
+  ].sort();
+  for (const event of events) expect(Object.keys(event).sort(), event.name).toEqual(keys);
+});
+
 test("test_timeline_out_of_order_sending_times_preserve_log_order", () => {
   const events = timeline(messages([["A", 1, [[52, "20261201-12:00:00"]]], ["5", 2, [[52, "20261101-12:00:00"]]]]));
   expect(events.map(e => [e.number, e.name, e.sendingTime])).toEqual([
@@ -142,6 +159,19 @@ test("test_timeline_gapfill_above_expected_emits_gap_before_event", () => {
 });
 
 
+test("test_timeline_cancel_replace_events_preserve_sequence_rules", () => {
+  const events = timeline(messages([
+    ["0", 7], ["A", 1, [[141, "Y"]]], ["D", 2], ["F", 8, [[43, "Y"]]],
+    ["4", 5, [[123, "Y"], [36, "10"]]], ["G", 10], ["9", 12]
+  ]));
+  expect(events.map(e => [e.name, e.seqNum, e.detail])).toEqual([
+    ["Heartbeat", "7", null], ["Logon", "1", null], ["NewOrder", "2", null],
+    ["CancelRequest", "8", null], ["SequenceGap", "5", "expected 3, received 5"],
+    ["GapFill", "5", null], ["ReplaceRequest", "10", null],
+    ["SequenceGap", "12", "expected 11, received 12"], ["CancelReject", "12", null]
+  ]);
+});
+
 test("test_timeline_logon_reset_without_seqnum_preserves_expected", () => {
   for (const invalid of [null, "abc"]) {
     const events = timeline(messages([["0", 7], ["A", invalid, [[141, "Y"]]], ["0", 10]]));
```

## 3. The whole ticket's change to the file: `git diff 60b1211..80116ec -- test/timeline.test.js`, in full
```diff
diff --git a/test/timeline.test.js b/test/timeline.test.js
index d693ec3..b4dc4da 100644
--- a/test/timeline.test.js
+++ b/test/timeline.test.js
@@ -1,6 +1,8 @@
 import { test, expect } from "vitest";
+import { analyse } from "../src/analyse.js";
 import { splitMessages } from "../src/framing.js";
 import { buildMessage } from "./helpers/fix.js";
+import { executionKind } from "../src/execution.js";
 import { timeline } from "../src/timeline.js";
 
 function messages(specs) {
@@ -12,13 +14,30 @@ const names = events => events.map(e => e.name);
 const gaps = events => events.filter(e => e.name === "SequenceGap");
 
 test("test_timeline_split_candidates_have_exact_event_keys", () => {
-  const events = timeline(messages([["A", 1], ["D", 2, [[11, "C1"]]]]));
-  expect(events).toHaveLength(2);
+  const events = timeline(messages([["A", 1], ["D", 2, [[11, "C1"]]], ["8", 4, [[150, "0"]]]]));
+  expect(names(events)).toEqual(["Logon", "NewOrder", "SequenceGap", "Acknowledgement"]);
   for (const e of events) expect(Object.keys(e).sort()).toEqual([
-    "number", "kind", "name", "sendingTime", "sender", "target", "seqNum", "clOrdId", "orderId", "detail"
+    "number", "kind", "name", "sendingTime", "sender", "target", "seqNum", "clOrdId", "orderId", "origClOrdId", "execRefId", "detail"
   ].sort());
 });
 
+test("test_timeline_new_order_events_keep_the_exact_public_shape", () => {
+  const candidates = messages([
+    ["A", 1], ["D", 2], ["F", 3], ["G", 4], ["9", 5],
+    ["8", 7, [[150, "G"]], "FIX.4.4"]
+  ]);
+  expect(executionKind(candidates[5])).toBe("TradeCorrect");
+  const events = timeline(candidates);
+  expect(names(events)).toEqual([
+    "Logon", "NewOrder", "CancelRequest", "ReplaceRequest", "CancelReject", "SequenceGap", "TradeCorrect"
+  ]);
+  const keys = [
+    "number", "kind", "name", "sendingTime", "sender", "target", "seqNum",
+    "clOrdId", "orderId", "origClOrdId", "execRefId", "detail"
+  ].sort();
+  for (const event of events) expect(Object.keys(event).sort(), event.name).toEqual(keys);
+});
+
 test("test_timeline_out_of_order_sending_times_preserve_log_order", () => {
   const events = timeline(messages([["A", 1, [[52, "20261201-12:00:00"]]], ["5", 2, [[52, "20261101-12:00:00"]]]]));
   expect(events.map(e => [e.number, e.name, e.sendingTime])).toEqual([
@@ -140,6 +159,19 @@ test("test_timeline_gapfill_above_expected_emits_gap_before_event", () => {
 });
 
 
+test("test_timeline_cancel_replace_events_preserve_sequence_rules", () => {
+  const events = timeline(messages([
+    ["0", 7], ["A", 1, [[141, "Y"]]], ["D", 2], ["F", 8, [[43, "Y"]]],
+    ["4", 5, [[123, "Y"], [36, "10"]]], ["G", 10], ["9", 12]
+  ]));
+  expect(events.map(e => [e.name, e.seqNum, e.detail])).toEqual([
+    ["Heartbeat", "7", null], ["Logon", "1", null], ["NewOrder", "2", null],
+    ["CancelRequest", "8", null], ["SequenceGap", "5", "expected 3, received 5"],
+    ["GapFill", "5", null], ["ReplaceRequest", "10", null],
+    ["SequenceGap", "12", "expected 11, received 12"], ["CancelReject", "12", null]
+  ]);
+});
+
 test("test_timeline_logon_reset_without_seqnum_preserves_expected", () => {
   for (const invalid of [null, "abc"]) {
     const events = timeline(messages([["0", 7], ["A", invalid, [[141, "Y"]]], ["0", 10]]));
@@ -169,3 +201,119 @@ test("test_timeline_missing_and_empty_direction_fields_share_key", () => {
       .toEqual(["expected 2, received 5"]);
   }
 });
+
+
+test("test_timeline_cancel_replace_message_types_emit_order_events", () => {
+  const ids = [[11, "CL-1"], [37, "ORD-2"], [41, "ORIG-3"]];
+  for (const [type, name] of [["F", "CancelRequest"], ["G", "ReplaceRequest"], ["9", "CancelReject"]]) {
+    const subsets = [ids, [], ...ids.map((_, missing) => ids.filter((_, index) => index !== missing))];
+    const events = timeline(messages(subsets.map((fields, index) => [type, index + 1, fields])));
+    expect(events.map(e => [e.kind, e.name, e.clOrdId, e.orderId, e.origClOrdId])).toEqual(
+      subsets.map(fields => ["order", name, ...ids.map(pair => fields.includes(pair) ? pair[1] : null)])
+    );
+  }
+});
+
+const fallback = execType => execType === null ? "ExecutionReport (no ExecType)" : `ExecutionReport (ExecType ${execType})`;
+const fix44Cases = [
+  ["H", null, "TradeCancel"], ["G", null, "TradeCorrect"], ["I", null, "OrderStatus"],
+  ["F", null, "Fill"], ["0", null, "Acknowledgement"], ["4", null, "Cancelled"], ["5", null, "Replaced"],
+  ...["X", "1", "2", null].map(execType => [execType, null, fallback(execType)])
+];
+const fix42Cases = [
+  ...[["1", "TradeCancel"], ["2", "TradeCorrect"], ["3", "OrderStatus"]].flatMap(([transType, name]) =>
+    ["2", "0", null].map(execType => [execType, transType, name])
+  ),
+  ...["0", null].flatMap(transType => ["1", "2"].map(execType => [execType, transType, "Fill"]))
+];
+const unsupportedCases = [
+  ["0", "1", "Acknowledgement"], ["4", "1", "Cancelled"], ["5", "1", "Replaced"],
+  ...["1", "2", "F", "H", "G", "I", null].map(execType => [execType, "1", fallback(execType)])
+];
+const crossVersionCases = [
+  ["FIX.4.4", "F", "1", "Fill"], ["FIX.4.2", "H", null, fallback("H")]
+];
+const reportCases = [
+  ...[["FIX.4.4", fix44Cases], ["FIX.4.2", fix42Cases], ["FIX.4.1", unsupportedCases]]
+    .flatMap(([version, cases]) => cases.map(row => [version, ...row])),
+  ...crossVersionCases
+];
+
+function reportSpec(version, execType, transType, seq = 1, extras = []) {
+  return ["8", seq, [
+    ...(transType === null ? [] : [[20, transType]]),
+    ...(execType === null ? [] : [[150, execType]]),
+    ...extras
+  ], version];
+}
+
+function expectExecutionKind(version, execType, transType, expected) {
+  const [candidate] = messages([reportSpec(version, execType, transType)]);
+  expect(executionKind(candidate), `${version} 150=${execType} 20=${transType}`).toBe(expected);
+}
+
+test("test_execution_kind_fix44_exec_type_maps_to_report_name", () => {
+  for (const row of fix44Cases) expectExecutionKind("FIX.4.4", ...row);
+});
+
+test("test_execution_kind_fix42_exec_trans_type_takes_precedence", () => {
+  for (const row of fix42Cases) expectExecutionKind("FIX.4.2", ...row);
+});
+
+test("test_execution_kind_cross_version_fields_do_not_override_rules", () => {
+  for (const row of crossVersionCases) expectExecutionKind(...row);
+});
+
+test("test_execution_kind_unsupported_version_uses_common_mappings_only", () => {
+  for (const row of unsupportedCases) expectExecutionKind("FIX.4.1", ...row);
+});
+
+test("test_execution_kind_candidates_and_decoded_messages_use_first_field_values", () => {
+  const cases = [
+    ["FIX.4.4", [[150, "H"]], { tag: 8, value: "unsupported" }, "TradeCancel"],
+    ["FIX.4.2", [[20, "2"], [20, "1"], [150, "2"]], null, "TradeCorrect"],
+    ["FIX.4.4", [[150, "I"], [150, "F"]], null, "OrderStatus"]
+  ];
+  for (const [version, fields, duplicateBeginString, expected] of cases) {
+    const text = buildMessage([[8, version], [35, "8"], ...fields]);
+    const [candidate] = splitMessages(text);
+    const { decoded, errors } = analyse(text);
+    expect(errors).toEqual([]);
+    expect(decoded).toHaveLength(1);
+    for (const message of [candidate, decoded[0]]) {
+      // A second BeginString denotes a new frame, so test that duplicate at field level.
+      const input = duplicateBeginString ? { ...message, fields: [...message.fields, duplicateBeginString] } : message;
+      expect(executionKind(input)).toBe(expected);
+    }
+  }
+});
+
+test("test_timeline_execution_reports_use_execution_kind_names", () => {
+  const candidates = messages(reportCases.map(([version, execType, transType], index) =>
+    reportSpec(version, execType, transType, index + 1)
+  ));
+  expect(candidates).toHaveLength(reportCases.length);
+  expect(timeline(candidates).map(e => [e.number, e.kind, e.name])).toEqual(
+    candidates.map(candidate => [candidate.number, "order", executionKind(candidate)])
+  );
+});
+
+test("test_timeline_order_reference_ids_respect_event_kind", () => {
+  const refs = [[19, "EXEC-19"], [41, "ORIG-41"]];
+  const reports = timeline(messages(reportCases.map(([version, execType, transType], index) =>
+    reportSpec(version, execType, transType, index + 1, refs)
+  )));
+  expect(reports.map(e => [e.name, e.origClOrdId, e.execRefId])).toEqual(reportCases.map(([, , , name]) =>
+    [name, "ORIG-41", ["TradeCancel", "TradeCorrect"].includes(name) ? "EXEC-19" : null]
+  ));
+
+  const events = timeline(messages([
+    ["A", 1, refs], ["D", 3, refs], ["F", 4, refs], ["G", 5, refs], ["9", 6, refs],
+    reportSpec("FIX.4.4", "H", null, 7), reportSpec("FIX.4.2", null, "2", 8), ["D", 9]
+  ]));
+  expect(events.map(e => [e.name, e.origClOrdId, e.execRefId])).toEqual([
+    ["Logon", null, null], ["SequenceGap", null, null], ["NewOrder", "ORIG-41", null],
+    ["CancelRequest", "ORIG-41", null], ["ReplaceRequest", "ORIG-41", null], ["CancelReject", "ORIG-41", null],
+    ["TradeCancel", null, null], ["TradeCorrect", null, null], ["NewOrder", null, null]
+  ]);
+});
```

## 4. Other files the fix pass touched
```
 test/timeline.test.js | 30 ++++++++++++++++++++++++++++++
 1 file changed, 30 insertions(+)
```
**None.** For context, the whole ticket (base to fix head):
```
 src/execution.js      |  25 ++++++++
 src/timeline.js       |  29 +++++-----
 test/timeline.test.js | 154 +++++++++++++++++++++++++++++++++++++++++++++++++-
 3 files changed, 190 insertions(+), 18 deletions(-)
```

## 5. The latest gates record (12:49:46, head `80116ec`)
`passed: true` · missing ACs: none · new tests 10, **valid 10** · lint passed · `pass_to_pass` passed (exit 0) · `existing_tests_touched: true` · critic not needed.
**Mutation: Stryker wrote a report this time:** 109 mutants in 2 files; in the gate's count (changed lines) **104 killed, 5 survived**, 0 timeouts, 0 without tests, 0 unrun, no error. Its first run succeeded (73 tests). The first gates run's mutation also succeeded (104 killed, 5 survived; 71 tests): the FXL-9 crash did not recur, as expected.

## State
Reviewer card `t_f1b97542` and FXL-10's scribe wait; `accept FXL-10` is open, so FXL-11 has not started. No card is running. Waiting for your decision file (`approve_test_edit` for head `80116ec44644d7b6f335f8a99271296b8da16800`, file `test/timeline.test.js`, and `unblock_once` for `t_587dd3d4`; or a reset).
