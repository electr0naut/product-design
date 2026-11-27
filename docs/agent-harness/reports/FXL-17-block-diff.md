# FXL-17: the fix pass's change to `test/filters.test.js` (FXL-17-block-review.md)

Read-only. Nothing unblocked or approved. Gate card `t_bb611a50` is blocked.
base `8881fce6a69d5a4b504ea27ef03848aa0acb1e22` · first gates head `3f4b42b23663f43da4088bc8922d1610d06f6bb9` · fix head **`bfb67b789917b5f15fa0cbfdc1b3bffcf76bc1ee`** (each an ancestor of the next)

## In short
- **Fix pass, in the test file: 4 lines added, 1 removed.** All of it is inside `..._account_choice_keeps_linked_order_and_matching_heartbeat`, a test **added by this ticket's first pass**, so no test that exists on base is edited by the fix pass (the block names the file, which exists on base). The removed assertion (same call, messages 0, 1, 2) is there again with the options in a variable, and one assertion is added before it (the first two messages alone give 0, 1).
- **Whole ticket, in that file: 3 lines removed** (shown in section 3). The host record lists one removed test id, `test_apply_filters_heartbeat_with_matching_account_is_excluded`, which the ticket says is replaced; the implementer recorded it under `modified_existing_tests` ("the other 17 original filter tests are unchanged": its words).

## 1. Why the first gates run failed
First gates record (14:23:06, head `3f4b42b`): `passed: false`, **`missing_acs: ["AC5"]`**, the only failing item. 3 new tests, all 3 valid; lint passed; `pass_to_pass` passed (exit 0); `removed_ids`: the one replaced test above; `existing_tests_touched: true`.
`implement.json` now maps AC5 to `..._account_choice_keeps_linked_order_and_matching_heartbeat`, `..._account_choice_keeps_only_matching_order_members` and `..._repeated_account_tag_propagates_only_first_occurrence`.

## 2. The fix pass: `git diff 3f4b42b..bfb67b7 -- test/filters.test.js`, in full
```diff
diff --git a/test/filters.test.js b/test/filters.test.js
index f7b1955..b775180 100644
--- a/test/filters.test.js
+++ b/test/filters.test.js
@@ -103,7 +103,10 @@ test('test_apply_filters_account_choice_keeps_linked_order_and_matching_heartbea
     ['D', [11, 'C1'], [1, 'ACC1']], ['8', [11, 'C1'], [37, 'O1']],
     ['0', [1, 'ACC1']], ['0'],
   );
-  expectSelection(applyFilters(decoded, { account: 'ACC1' }), decoded, 0, 1, 2);
+  const chosen = { account: 'ACC1' };
+  // Including a matching Heartbeat must not narrow or widen the existing order selection.
+  expectSelection(applyFilters(decoded.slice(0, 2), chosen), decoded, 0, 1);
+  expectSelection(applyFilters(decoded, chosen), decoded, 0, 1, 2);
 });
 
 test('test_apply_filters_ungrouped_account_choice_matches_regardless_of_type', () => {
```

## 3. The whole ticket: `git diff 8881fce..bfb67b7 -- test/filters.test.js src/filters.js`, in full
```diff
diff --git a/src/filters.js b/src/filters.js
index c36c95e..012804e 100644
--- a/src/filters.js
+++ b/src/filters.js
@@ -48,7 +48,7 @@ export function applyFilters(decoded, chosen) {
 
   const accountNumbers = account == null ? null : accountMatches(decoded, account);
   return decoded.filter(message => {
-    if (accountNumbers !== null && (!accountNumbers.has(message.number) || firstValue(message, 35) === '0')) {
+    if (accountNumbers !== null && !accountNumbers.has(message.number)) {
       return false;
     }
     return activeParties.every(({ key, tag }) => firstValue(message, tag) === chosen[key]);
diff --git a/test/filters.test.js b/test/filters.test.js
index c27aac0..b775180 100644
--- a/test/filters.test.js
+++ b/test/filters.test.js
@@ -98,9 +98,34 @@ test('test_apply_filters_ungrouped_matching_account_keeps_message', () => {
   expectSelection(applyFilters(decoded, { account: 'ACC1' }), decoded, 0);
 });
 
-test('test_apply_filters_heartbeat_with_matching_account_is_excluded', () => {
-  const decoded = decodeLog(['0', [1, 'ACC1']], ['A', [1, 'ACC1']]);
-  expectSelection(applyFilters(decoded, { account: 'ACC1' }), decoded, 1);
+test('test_apply_filters_account_choice_keeps_linked_order_and_matching_heartbeat', () => {
+  const decoded = decodeLog(
+    ['D', [11, 'C1'], [1, 'ACC1']], ['8', [11, 'C1'], [37, 'O1']],
+    ['0', [1, 'ACC1']], ['0'],
+  );
+  const chosen = { account: 'ACC1' };
+  // Including a matching Heartbeat must not narrow or widen the existing order selection.
+  expectSelection(applyFilters(decoded.slice(0, 2), chosen), decoded, 0, 1);
+  expectSelection(applyFilters(decoded, chosen), decoded, 0, 1, 2);
+});
+
+test('test_apply_filters_ungrouped_account_choice_matches_regardless_of_type', () => {
+  const rows = [['1', [1, 'ACC1']], ['A', [1, 'ACC1']], ['0', [1, 'ACC2']]];
+  for (const decoded of [decodeLog(...rows), decodeLog(...rows, ['1'], ['A'])]) {
+    expectSelection(applyFilters(decoded, { account: 'ACC1' }), decoded, 0, 1);
+    expectSelection(applyFilters(decoded, { account: 'ACC2' }), decoded, 2);
+  }
+});
+
+test('test_apply_filters_account_and_sender_keep_only_matching_messages', () => {
+  const decoded = decodeLog(
+    ['D', [11, 'C1'], [1, 'ACC1'], [49, 'OTHER']],
+    ['8', [11, 'C1'], [37, 'O1'], [49, 'BRK']],
+    ['0', [1, 'ACC1'], [49, 'BRK']], ['0', [49, 'BRK']],
+  );
+  expectSelection(applyFilters(decoded, { account: 'ACC1', senderCompId: 'BRK' }), decoded, 1, 2);
+  expectSelection(applyFilters(decoded, { senderCompId: 'BRK' }), decoded, 1, 2, 3);
+  expectSelection(applyFilters(decoded, { senderCompId: 'OTHER' }), decoded, 0);
 });
 
 test('test_apply_filters_account_and_sender_returns_intersection', () => {
```

## 4. Files the fix pass touched
```
 test/filters.test.js | 5 ++++-
 1 file changed, 4 insertions(+), 1 deletion(-)
```
Whole ticket:
```
 src/filters.js       |  2 +-
 test/filters.test.js | 31 ++++++++++++++++++++++++++++---
 2 files changed, 29 insertions(+), 4 deletions(-)
```

## 5. Latest gates record (14:26:21, head `bfb67b7`)
`passed: true` · missing ACs: none · 3 new tests, 3 valid · lint passed · `pass_to_pass` passed (exit 0) · `existing_tests_touched: true`.
**Mutation:** `killed 6, survived 0, timeout 0, no tests 0, unrun 0, static (not measured) 0`; no error; complete; left out: `test/static-checks.test.js`. The first gates run's mutation line was the same.
This is the first ticket gated on D22 and D23.

## State
`FXL-17`'s reviewer and scribe wait, and FXL-14 to FXL-16 wait on `accept FXL-17`. Waiting for your decision file (`approve_test_edit` for head `bfb67b789917b5f15fa0cbfdc1b3bffcf76bc1ee`, file `test/filters.test.js`, and `unblock_once` for `t_bb611a50`; or a reset).
