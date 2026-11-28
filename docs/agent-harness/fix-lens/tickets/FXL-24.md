+++
key = "FXL-24"
title = "A Logon numbered 1 restarts the expected sequence number"
rank = 24
blocked_by = []
labels = []
+++
A session that starts again at MsgSeqNum 1 without ResetSeqNumFlag (a daily reset, or an engine set to reset on
logout or disconnect) was not followed: every message after the restart had a lower number than expected and
was ignored, so a real gap after the restart was not shown. From v1.4 a Logon numbered 1 restarts the count
(PRD v1.4 TR-003; technical design v1.4 section 7, step 1).

MsgSeqNum is read as a number, as today, so `34=01` is numbered 1. Step 1 becomes: a Logon (35=A) with 141=Y,
or with MsgSeqNum 1, when 43 is not `Y`, sets the expected number
of its direction to 1. The other steps do not change, so the Logon itself then advances the expected number to
2. Only its own direction restarts; the other direction restarts with its own Logon. The restart adds no
timeline event of its own.

`src/timeline.js` and `test/timeline.test.js` are expected to change. No existing test is expected to change;
if one fails, stop and say which in the handoff.

In the examples `A -> B` means 49=A and 56=B, `H` is a heartbeat (35=0), and each message is written with its
MsgSeqNum.

Acceptance criteria
- AC0: `timeline(messages)` keeps its signature and the shape of its events.
- AC1: (1) Logon A -> B 1; (2) H A -> B 2; (3) H A -> B 3; (4) Logon A -> B 1; (5) H A -> B 2; (6) H A -> B 4:
  there is exactly one SequenceGap event, before the event of message 6, with `detail` `expected 3, received
  4`. Messages 4 and 5 have no gap, and message 4 has only its own event. The same holds on FIX 4.2.
- AC2: A log that runs on after the restart without a gap (… (4) Logon 1; (5) H 2; (6) H 3) has no SequenceGap
  event at all.
- AC3: Only that direction restarts. (1) Logon A -> B 1; (2) Logon B -> A 1; (3) H A -> B 2; (4) H B -> A 2;
  (5) Logon A -> B 1; (6) H B -> A 3; (7) H A -> B 3; (8) H B -> A 5: message 6 has no gap, message 7 has the
  gap `expected 2, received 3`, and message 8 has the gap `expected 4, received 5`.
- AC4: A PossDup Logon restarts nothing. (1) Logon A -> B 1; (2) H 2; (3) Logon 1 with 43=Y; (4) H 2; (5) H 4:
  one gap, at message 5, `expected 3, received 4`.
- AC5: Only a Logon restarts. The log of AC4 with a heartbeat numbered 1 as message 3 gives the same one gap.
- AC6: A Logon with a lower number other than 1 and without 141=Y restarts nothing. (1) Logon 1; (2) H 2; (3)
  H 3; (4) Logon 2; (5) H 3; (6) H 5 (all A -> B): one gap, at message 6, `expected 4, received 5`.
- AC7: A Logon with 141=Y behaves as today, whatever its number, and a Logon numbered 1 that is the first
  message of its direction behaves as today.
- AC8: Two restarts in one direction are both followed: after the second Logon numbered 1 the next expected
  number is 2 again.
