+++
key = "FXL-22"
title = "Order grouping within parties, and finding the order of a message"
rank = 22
blocked_by = []
labels = []
+++
Until now an order id was its value alone, so two clients that both used ClOrdID `1`, or two venues that both
used OrderID `1`, became one order. From v1.4 an id belongs to a party (PRD v1.4 AC-035 and AC-036; technical
design v1.4 section 12): a ClOrdID to the client, an OrderID to the executing party. `findOrder` also learns to
find the order of one message. Only `src/orders.js` changes in the product. Nothing on the page changes in this
ticket: `src/render.js` still calls `findOrder(groups, id)`, which keeps working (FXL-26 passes the number).

The parties of a message. For an ExecutionReport (35=8) or an OrderCancelReject (35=9), the executing party is
its SenderCompID (49) and the client is its TargetCompID (56). For every other message the client is its 49 and
the executing party is its 56. A missing 49 or 56 is the empty string.

The keys of a message. The pair (client, value) for its ClOrdID (11) and for its OrigClOrdID (41), and the pair
(executing party, value) for its OrderID (37). Two keys are the same only when both parts are equal, exactly and
case-sensitively. A ClOrdID key is never the same as an OrderID key, also when party and value are equal.
Everything else is as today: an empty value and `37=NONE` give no key, all keys of one message are joined, the
groups are the connected sets, and a group lists `clOrdIds`, `orderIds` and `numbers` as before.

`src/orders.js`, `test/orders.test.js`, `test/filters.test.js` and `test/render.test.js` are expected to change.
`src/filters.js`, `src/summary.js` and `src/render.js` do not change.

Existing tests. Some fixtures in `test/filters.test.js` and `test/render.test.js` send an execution report in
the same direction as its order, or leave out the 49 or 56 of one of the two, which no real log does. With the
party rule the report no longer joins its order, and the test fails. Give those fixtures the real direction: a
report goes from the executing party to the client, so its 49 is the order's 56 and its 56 is the order's 49.
Where an expected value follows from the 49 or 56 of a message you changed (a SenderCompID filter, a filter
list), the expected value follows the fixture; where the old fixture cannot keep what the test's name says,
rebuild the fixture so that the name still holds. No test is removed, no assertion is dropped, and no test
outside these two files and `test/orders.test.js` changes. Name every test you changed in the handoff. On the
code as it stood before v1.3 these were:

- `test/filters.test.js`: `test_apply_filters_account_and_sender_keep_only_matching_messages`,
  `test_apply_filters_sender_exclusions_preserve_full_log_order_links`,
  `test_filters_frozen_inputs_remain_unchanged`.
- `test/render.test.js`: `test_render_filter_and_selected_order_apply_together`,
  `test_render_filtered_log_passes_shown_to_tradeSummary`,
  `test_render_filtering_preserves_full_log_gaps_and_numbers`,
  `test_render_fxl15_fix44_order_story_matches_example`,
  `test_render_literal_order_and_story_values_leave_attributes_fixed`,
  `test_render_logA_account_ACC2_only_vod_sell_row`,
  `test_render_order_terms_choose_source_and_skip_missing_parts`,
  `test_render_selected_order_keeps_only_original_group_numbers`,
  `test_render_selected_stats_count_visible_messages_gaps_and_orders`,
  `test_render_selected_timeline_preserves_existing_gaps_without_new_gaps`.

Tests added since then that fail for the same reason are handled the same way.

The examples below give each message as its type and the fields that matter, numbered in log order. `ALPHA ->
BRK` means 49=ALPHA and 56=BRK.

Acceptance criteria
- AC0: `orderGroups(decoded)` still returns groups with exactly the keys `clOrdIds`, `orderIds` and `numbers`,
  in order of first appearance, and stays pure. `findOrder(groups, id, number)` takes the message number as an
  optional third argument.
- AC1: Two clients that use the same ClOrdID are two orders. For (1) `D`, ALPHA -> BRK, 11=7; (2) `D`, BETA ->
  BRK, 11=7; (3) `8`, BRK -> ALPHA, 37=X1, 11=7; (4) `8`, BRK -> BETA, 37=X2, 11=7; (5) `F`, ALPHA -> BRK,
  11=8, 41=7, 37=X1; (6) `9`, BRK -> ALPHA, 37=X1, 11=8, 41=7: the groups are `{ clOrdIds: ["7", "8"],
  orderIds: ["X1"], numbers: [1, 3, 5, 6] }` and `{ clOrdIds: ["7"], orderIds: ["X2"], numbers: [2, 4] }`. The
  same holds on FIX 4.2.
- AC2: Two executing parties that use the same OrderID are two orders. For (1) `D`, FUND -> NORTH, 11=N1; (2)
  `D`, FUND -> SOUTH, 11=S1; (3) `8`, NORTH -> FUND, 37=5, 11=N1; (4) `8`, SOUTH -> FUND, 37=5, 11=S1: the
  groups have the numbers `[1, 3]` and `[2, 4]`, each with `orderIds: ["5"]`.
- AC3: A copy of a report sent to a third CompID joins its order through the OrderID. Adding (5) `8`, NORTH ->
  DESK, 37=5, 11=N1 to the log of AC2 gives the numbers `[1, 3, 5]` and `[2, 4]`.
- AC4: A request names the executing party in its 56: a cancel request `F`, FUND -> NORTH, 11=N2, 37=5 with no
  41 joins the NORTH order of AC2 and not the SOUTH one.
- AC5: A missing 49 or 56 is the empty party, the same for every message that lacks it, and it is no CompID
  that a message could carry. For (1) `D` without 49 and 56, 11=K1; (2) `8` without 49 and 56, 11=K1, 37=Z1;
  (3) `D` with 49=ALPHA, 11=K1: the groups have the numbers `[1, 2]` and `[3]`.
- AC6: The two parts of a key never run together and are compared exactly. `D`, 49=`A/B`, 11=`C` and `D`,
  49=`A`, 11=`B/C` (both to BRK) are two orders, and so they are with any other character in place of `/`.
  `D` from `CLI` and `D` from `cli` with the same ClOrdID are two orders.
- AC7: ClOrdIDs and OrderIDs are separate. For (1) `D`, SELF -> SELF, 11=1 and (2) `8`, SELF -> SELF, 37=1,
  there are two groups: `[1]` with `clOrdIds: ["1"]` and `[2]` with `orderIds: ["1"]`.
- AC8: `findOrder(groups, id, number)` returns the group whose `numbers` include `number`. When `number` is
  `null` or left out, or no group holds that message, it returns the first group whose `clOrdIds` or `orderIds`
  contains `id`, or `null`. For (1) `D`, ALPHA -> BRK, 11=500; (2) `D`, BETA -> BRK, 11=Q9; (3) `8`, BRK ->
  ALPHA, 37=12, 11=500; (4) `8`, BRK -> BETA, 37=500, 11=Q9; (5) a heartbeat: `findOrder(groups, "500", 4)` is
  the group `[2, 4]`; with `3`, with `null`, with no third argument, with `5` and with `99` it is the group
  `[1, 3]`; `findOrder(groups, "nope", 99)` is `null`.
- AC9: What used the groups still works. `applyFilters` with the Account filter keeps to the orders of that
  account when two clients share a ClOrdID: in the log of AC1 with 1=A1 on message 1 and 1=B1 on message 2, the
  filter `A1` passes the messages 1, 3, 5 and 6, and `B1` passes 2 and 4.
- AC10: `orderGroups` on 10,000 decoded messages (orders and their reports from 50 clients that all number
  their ClOrdIDs from 0) finishes in under 1 second, and the test checks the number of groups it expects from
  how it built the log.
