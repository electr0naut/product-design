+++
key = "FXL-13"
title = "Filters by account and by sender and target ids"
rank = 13
blocked_by = ["FXL-11"]
labels = []
+++
Add `src/filters.js`, following technical design section 14 (v1.2): `FILTERS`, `filterOptions(decoded)` and
`applyFilters(decoded, chosen)`. All are pure and have no DOM access. `decoded` is the `decoded` list of
`analyse()`. `chosen` is an object with a string or `null` per filter key. The Account filter uses `orderGroups`
from `src/orders.js`. Nothing on the page changes in this ticket.

No existing test file is expected to change. Add `test/filters.test.js`.

The source rules of technical design section 8.4 apply to every file under `src/`: no assignment to `.id`,
`.name`, `.title`, `.src`, `.value`, `.style` or `.cssText`, no `setAttribute`, no `import(`. Build objects
with literals. `test/static-checks.test.js` enforces this since FXL-9.

Acceptance criteria
- AC0: A test imports `FILTERS`, `filterOptions` and `applyFilters` from `src/filters.js`. `FILTERS` is, in this
  order, `{ key: "account", tag: 1, label: "Account" }`, `{ key: "senderCompId", tag: 49, label: "SenderCompID" }`,
  `{ key: "senderSubId", tag: 50, label: "SenderSubID" }`, `{ key: "targetCompId", tag: 56, label: "TargetCompID" }`
  and `{ key: "targetSubId", tag: 57, label: "TargetSubID" }`.
- AC1: `filterOptions(decoded)` returns an object with the five keys. Each value is the list of distinct,
  non-empty values of that tag in the log, sorted with plain string comparison (`Zeta` before `alpha`). A tag
  that no message carries gives an empty list.
- AC2: With every chosen value `null`, or with `chosen` an empty object, `applyFilters` returns all the messages,
  in order.
- AC3: `senderCompId`, `senderSubId`, `targetCompId` and `targetSubId` keep the messages whose own field has
  exactly the chosen value. A message without the tag does not pass.
- AC4: `account` keeps every message of every order that has at least one message with that Account. For this
  log: NewOrder 11=C1, 1=ACC1; ExecutionReport 11=C1, 37=O1 (no Account); NewOrder 11=C2, 1=ACC2;
  ExecutionReport 11=C2, 37=O2 (no Account); choosing `ACC1` keeps messages 1 and 2 only.
- AC5: A message that is in no order and carries the Account itself also passes the `account` filter. A Heartbeat
  never passes it.
- AC6: Filters combine: with two chosen values, a message passes only if it passes both. Choosing an Account and
  a SenderCompID keeps, from the Account's orders, only the messages sent by that sender.
- AC7: Order grouping for the Account filter runs on the whole log, whatever the other filters are: in AC6 the
  order's Account may be on a message that the SenderCompID filter removes.
- AC8: The result is always a subset of `decoded` in log order, and `applyFilters` and `filterOptions` do not
  change their arguments.
- AC9: When a tag repeats in a message, its first value counts.
- AC10: For 1,000 valid order messages, `applyFilters` with an Account chosen finishes in under 1 second.
