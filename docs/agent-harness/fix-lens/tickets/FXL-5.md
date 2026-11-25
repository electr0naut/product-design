+++
key = "FXL-5"
title = "Session timeline and sequence-gap detection"
rank = 5
blocked_by = ["FXL-1"]
labels = []
+++
Add `src/timeline.js`, following technical design section 7: `timeline(messages)` takes valid messages in log
order (each with its `number` and fields) and returns the events.

Acceptance criteria
- AC1: Events are in log order, never re-sorted by SendingTime.
- AC2: MsgTypes A, 5, 0, 1, 2, 3, j give Logon, Logout, Heartbeat, TestRequest, ResendRequest, SessionReject,
  BusinessReject; 35=4 gives GapFill when 123=Y and Reset otherwise; 35=D gives NewOrder; other MsgTypes give no
  event.
- AC3: ExecutionReport names by ExecType: 0 Acknowledgement; 1 or 2 on FIX.4.2 Fill; F on FIX.4.4 Fill; 4
  Cancelled; 5 Replaced; anything else (including 2 on FIX.4.4) `ExecutionReport (ExecType X)`.
- AC4: Every event has the message number, name, SendingTime when present (else `null`), sender 49, target 56 and
  MsgSeqNum 34; order events also ClOrdID 11 and OrderID 37 when present (else `null`).
- AC5: Sequence numbers are tracked per (49, 56) direction: 1, 2, 5 in one direction gives one SequenceGap event,
  placed just before message 5's own event, with detail `expected 3, received 5`; interleaved messages of the
  other direction don't affect it.
- AC6: The first message of a direction never gives a gap; a lower-than-expected number gives no event.
- AC7: A message with 43=Y gives no gap and doesn't change the expected number.
- AC8: A SequenceReset sets the expected number to its 36 (NewSeqNo): after `4` with 36=10, a message with 34=10
  gives no gap.
- AC9: A Logon with 141=Y resets the direction's expected number to 1 before its own check: a Logon with 141=Y and
  34=1 after message 34=7 gives no gap.
