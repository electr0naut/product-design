+++
key = "FXL-23"
title = "Trading summary: executions belong to their sender, and a cancel or correction finds its fill wherever it stands"
rank = 23
blocked_by = []
labels = []
+++
Two changes to step 1 of `tradeSummary` in `src/summary.js` (PRD v1.4 AC-041 to AC-043; technical design v1.4
section 13). Nothing else in the module changes: `executionKind`, the rules for a Fill, a TradeCorrect and a
TradeCancel, the `shown` set, step 2 and the shape of the answer stay as they are.

The key of a report. It was OrderID and ExecID, so two venues that both used OrderID `1` and ExecID `1` were
one execution and the second fill was dropped as a resend. The key is now the triple (SenderCompID 49, OrderID
37, ExecID 17); a missing 49 or 37 is the empty string; a report with no 17 has no key, as before. A lookup by
ExecRefID uses the looking report's own 49 and 37 with its 19. The three parts never run together: build the
key so that no choice of values makes two different triples equal.

Two passes. The reports were taken once, in log order, so a trade cancel that stood before its fill was
unmatched and the fill stayed in the totals. Logs merged from two sources hold them in either order. The
reports are now taken in two passes over the whole list, each in log order: first every Fill, then every
TradeCorrect and TradeCancel. The list of executions stays in log order of `number`. One limit stays, and is
wanted: a TradeCancel or TradeCorrect that names a TradeCorrect standing after it in the log does not find it
and is unmatched.

`src/summary.js` and `test/summary.test.js` are expected to change. No existing test is expected to change; if
one fails, stop and say which in the handoff.

In the examples every message is an ExecutionReport on FIX 4.4 with 55=ABC and 54=1, numbered in log order. A
side of a row is written as its `fills`, `filledQty` and `notional`.

Acceptance criteria
- AC0: `tradeSummary(decoded, shown)` still returns `{ rows, unmatched }` with the same row shape, and stays
  pure.
- AC1: Reports of two senders with the same OrderID and ExecID are two executions. (1) 49=NORTH, 37=1, 17=1,
  150=F, 32=100, 31=10; (2) 49=SOUTH, 37=1, 17=1, 150=F, 32=200, 31=11: the buy side of ABC has 2 fills, 300
  and 3200. The same holds on FIX 4.2.
- AC2: A report sent again by the same sender is still counted once, whatever its TargetCompID. Adding (3), a
  copy of (1) with another 56, changes nothing.
- AC3: A trade cancel before its fill removes it. (1) 49=BRK, 37=O1, 17=E2, 19=E1, 150=H; (2) 49=BRK, 37=O1,
  17=E1, 150=F, 32=100, 31=10: `rows` is empty and `unmatched` is 0. The same holds on FIX 4.2 with
  ExecTransType (20). When the fill (2) is sent once more after that, it stays cancelled.
- AC4: A trade correction before its fill corrects it, and the execution keeps the number of the fill. (1)
  49=BRK, 37=O1, 17=E2, 19=E1, 150=G, 32=80, 31=9; (2) the fill of AC3: the buy side has 1 fill, 80 and 720,
  and `unmatched` is 0. With `shown` holding only message 1 `rows` is empty; with only message 2 the fill of 80
  is counted.
- AC5: The limit. (1) a cancel 17=E3 that names 19=E2; (2) the correction of AC4, 17=E2 naming E1; (3) the
  fill E1 (all 49=BRK, 37=O1): the cancel is unmatched and changes nothing, the correction applies: 1 fill, 80
  and 720, `unmatched` 1.
- AC6: A cancel or a correction only finds an execution of its own sender and OrderID. After the fill of AC3,
  a cancel from 49=OTHER with 37=O1 that names E1, and a cancel from 49=BRK with 37=O2 that names E1, are both
  unmatched: 1 fill, 100 and 1000, `unmatched` 2.
- AC7: Reports without 49 share the empty sender: two fills without 49 and with the same 37 and 17 are one
  execution, and a cancel without 49 finds a fill without 49.
- AC8: The parts of the key do not run together: fills from 49=`A|B` with 37=`C` and from 49=`A` with
  37=`B|C`, same 17, are two executions, and so they are with any other character in place of `|`; the same
  for 37 and 17.
- AC9: The usual order still works as today: a fill, then its correction, then a cancel of the correction
  leaves nothing; an ExecRefID that is nowhere in the log is unmatched, and `unmatched` counts only the
  messages in `shown`.
- AC10: `tradeSummary` on 10,000 reports in which every cancel stands before its fill finishes in under 1
  second, and the test checks the totals it expects from how it built the log.
