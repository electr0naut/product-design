+++
key = "FXL-11"
title = "Group messages into orders"
rank = 11
blocked_by = []
labels = []
+++
Add `src/orders.js`, following technical design section 12 (v1.2): `orderGroups(decoded)` groups the decoded
messages of a log into orders, and `findOrder(groups, id)` finds the group for an id. Both are pure and have no
DOM access. `decoded` is the `decoded` list of `analyse()`: each message has `number` and `fields`, and each
field has `tag` and `value`. Nothing on the page changes in this ticket.

No existing test file is expected to change. Add `test/orders.test.js`.

The source rules of technical design section 8.4 apply to every file under `src/`: no assignment to `.id`,
`.name`, `.title`, `.src`, `.value`, `.style` or `.cssText`, no `setAttribute`, no `import(`. Build objects
with literals. `test/static-checks.test.js` enforces this since FXL-9.

Acceptance criteria
- AC0: A test imports `orderGroups` and `findOrder` from `src/orders.js` and calls `orderGroups(analyse(text).decoded)`.
  Each group has exactly the keys `clOrdIds`, `orderIds` and `numbers`.
- AC1: Messages that share a ClOrdID 11 are one group, and so are messages that share an OrderID 37.
- AC2: OrigClOrdID 41 links a message to the order whose ClOrdID it names. For this log, in this order:
  NewOrder 11=C1; ReplaceRequest 11=C2, 41=C1; ExecutionReport 11=C2, 37=O1; CancelRequest 11=C3, 41=C2;
  the result is one group with `clOrdIds` `["C1", "C2", "C3"]`, `orderIds` `["O1"]` and `numbers` `[1, 2, 3, 4]`.
- AC3: Linking works through a later message. NewOrder 11=A; NewOrder 11=B; ExecutionReport 11=A, 37=X;
  ExecutionReport 11=B, 37=X gives one group with `clOrdIds` `["A", "B"]`, `orderIds` `["X"]` and `numbers`
  `[1, 2, 3, 4]`.
- AC4: `37=NONE` is not an identifier. Two CancelRejects, 11=K1 with 37=NONE and 11=K2 with 37=NONE, give two
  groups, each with an empty `orderIds`. The comparison is exact: `37=None` is an identifier.
- AC5: A message with none of 11, 41 and 37, or with only empty values for them, is in no group.
- AC6: Groups come in order of first appearance. In a group, `clOrdIds` (from 11 and 41) and `orderIds` are in
  order of first appearance without repeats, and `numbers` is in log order.
- AC7: `findOrder(groups, id)` returns the group whose `clOrdIds` or `orderIds` contains `id`, and `null` when
  there is none. `findOrder(groups, "NONE")` is `null` for the log of AC4.
- AC8: When a tag repeats in a message, its first value counts.
- AC9: `orderGroups` does not change its argument, and gives the same result when called twice.
- AC10: For 1,000 valid order messages, `orderGroups` finishes in under 1 second.
