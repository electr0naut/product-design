+++
key = "FXL-10"
title = "Cancel and replace requests, trade cancels, trade corrections and order status in the timeline"
rank = 10
blocked_by = []
labels = []
+++
The timeline ignores cancel and replace requests, and it shows a FIX 4.2 trade cancel or correction as a Fill.
Add `src/execution.js` and change `src/timeline.js` to follow technical design section 7 (v1.2), steps 4 to 6,
and the TimelineEvent shape of section 2. Sequence-number handling (steps 1 to 3) does not change.

`test/timeline.test.js` is expected to change in this ticket: the event keys gain `origClOrdId` and `execRefId`,
and the names of some ExecutionReports change (design section 15).

Acceptance criteria
- AC0: A test imports `executionKind` from `src/execution.js` and `timeline` from `src/timeline.js`. Every event
  has exactly the keys `number`, `kind`, `name`, `sendingTime`, `sender`, `target`, `seqNum`, `clOrdId`,
  `orderId`, `origClOrdId`, `execRefId`, `detail`.
- AC1: `35=F` gives `CancelRequest`, `35=G` gives `ReplaceRequest` and `35=9` gives `CancelReject`, each with
  `kind` `order`, and with ClOrdID 11, OrderID 37 and OrigClOrdID 41 when present, else `null`.
- AC2: On `FIX.4.4`, `executionKind` returns `TradeCancel` for 150=H, `TradeCorrect` for 150=G and `OrderStatus`
  for 150=I. 150=F is still `Fill`, 0 `Acknowledgement`, 4 `Cancelled`, 5 `Replaced`; any other value is
  `ExecutionReport (ExecType X)`, and no 150 is `ExecutionReport (no ExecType)`.
- AC3: On `FIX.4.2`, ExecTransType 20 is checked first: 20=1 is `TradeCancel`, 20=2 is `TradeCorrect` and 20=3 is
  `OrderStatus`, whatever 150 says. With 20=0 or no tag 20, 150=1 and 150=2 are `Fill`.
- AC4: The versions do not borrow each other's rules. A `FIX.4.4` report with 20=1 and 150=F is a `Fill`. A
  `FIX.4.2` report with 150=H and no tag 20 is `ExecutionReport (ExecType H)`.
- AC5: For an unsupported version only 150=0, 4 and 5 are mapped: a `FIX.4.1` report with 20=1 and 150=2 is
  `ExecutionReport (ExecType 2)`.
- AC6: `executionKind` reads tags 8, 20 and 150 from `message.fields` (the first value of each), so it gives the
  same answer for a candidate from `splitMessages` and for the decoded message of the same text from `analyse`.
- AC7: The timeline names every ExecutionReport with `executionKind`: for one report of each kind above, the
  event's `name` equals `executionKind(message)`.
- AC8: `execRefId` is tag 19 on `TradeCancel` and `TradeCorrect` events, and `null` on every other event.
  `origClOrdId` is tag 41 when the message has one, on any order event, else `null`. Session events have `null`
  for both.
- AC9: Sequence gaps, PossDup, SequenceReset and Logon handling are unchanged: the existing tests for them pass
  without changes to their expectations.
