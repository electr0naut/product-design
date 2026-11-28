# FXL-5: BLOCKED for a human

## FXL-5 · reviewer (fix 1) (t_f8d0133b) is blocked
```
Events (9):
  [2026-11-26 21:28] created {'assignee': 'reviewer', 'status': 'todo', 'parents': ['t_b1553c6a'], 'creator_task_id': None, 'tenant': None, 'workspace_kind': 'dir', 'workspace_path': '/srv/lab/agent-harness/work/fix-lens', 'branch_name': None, 'project_id': None, 'skills': None, 'goal_mode': None, 'model_override': None, 'provider_override': None}
  [2026-11-26 21:28] dependency_wait {'reason': 'parent_not_done', 'parent': 't_b1553c6a'}
  [2026-11-26 21:32] promoted
  [2026-11-26 21:32] [run 359] claimed {'lock': 'ailab:433487', 'expires': 1795726940, 'run_id': 359}
  [2026-11-26 21:33] [run 359] heartbeat {'note': 'review running'}
  [2026-11-26 21:34] [run 359] heartbeat {'note': 'review running'}
  [2026-11-26 21:35] [run 359] heartbeat {'note': 'review running'}
  [2026-11-26 21:35] commented {'author': 'default', 'len': 102}
  [2026-11-26 21:35] [run 359] blocked {'reason': 'FXL-5: 1 proven, 0 blocking-unproven, 3 notes, 0 skipped for budget; $1.984 (see review.json)', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #359 blocked      @reviewer  186s  2026-11-26 21:32
        → FXL-5: 1 proven, 0 blocking-unproven, 3 notes, 0 skipped for budget; $1.984 (see review.json)
```

Run files: base.txt, find-raw-1.txt, findings.json, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, proofs.json, readiness.json, refutations.json, repo.txt, review-1.json, review.json

## Run summary
Fix pass: pass 1 triggered by review
- First attempt's gates: {"passed": true}; lint True; pass_to_pass True
- Latest gates: {"passed": true}; lint True; pass_to_pass True

### First review: tier standard, cost $3.0968, decision {'blocking': ['F2', 'F3'], 'blocking_unproven': [], 'notes': ['F1', 'F4', 'F5', 'F6', 'F7']}
- F1 [medium, conf 70] src/timeline.js:44 The Logon 141=Y reset mutates the direction's expected sequence number even when the message's MsgSeqNum (34) is missing or non-numeric, so a 34-less Logon changes expected to 1. AC7 says a message with 34 missing/not a number is not checked and does not change the expected number.
  failure: For one direction the log has Heartbeat 34=1, 34=2, 34=3 (expected becomes 4), then a Logon with 141=Y and no 34 (or 34=NaN). The condition on line 44 only requires previous!==undefined, so line 45 sets expected to 1 even though seq is null. A following Heartbeat with 34=4 then fails 'seq > expected
- F2 [high, conf 99] src/timeline.js:71 Events get kind "message", and gap events get kind "gap" (line 62). The only values the design allows are "session" and "order". NewOrder and ExecutionReport events are never marked "order", and session events are never marked "session".
  failure: A FIX.4.2 35=D message with 34=1 gives {name:"NewOrder", kind:"message"} instead of kind "order". A Heartbeat gives kind "message" instead of "session". With 34=1 then 34=5, the SequenceGap event has kind "gap", which is not an allowed value.
- F3 [high, conf 99] src/timeline.js:48 The `type === "4"` branch only updates the expected number and never runs the gap check. The check should be skipped only for Reset mode (no 123=Y), so a GapFill with a higher-than-expected MsgSeqNum loses its SequenceGap.
  failure: In one direction, send Heartbeat 34=1, then 35=4 with 123=Y, 34=5 and 36=10. The output is [Heartbeat, GapFill]. It should be [Heartbeat, SequenceGap 'expected 2, received 5', GapFill], with expected then set to 10.
- F4 [medium, conf 98] src/timeline.js:44 The Logon 141=Y reset runs even when 34 is missing or not a number. Such a message must skip the reset, the gap check and the update, and must leave the expected number unchanged.
  failure: Send Heartbeat 34=7, then a Logon with 141=Y and no 34, then Heartbeat 34=10. The code gives the gap 'expected 1, received 10'. It should give 'expected 8, received 10'. If the last message is 34=8, the code reports a false gap 'expected 1, received 8'.
- F5 [medium, conf 90] src/timeline.js:49 A NewSeqNo of 36=0 is accepted and stored as the expected number, because sequence() allows any string of digits. A 36 that is not a positive integer should fall back to seq + 1.
  failure: Send Heartbeat 34=1, then Reset 34=50 with 36=0, then Heartbeat 34=51. The code sets expected to 0 and emits 'expected 0, received 51'. Expected should be 51, with no gap.
- F6 [medium, conf 65] src/timeline.js:43 The whole sequence block, including the Logon 141=Y reset, is skipped when 43=Y. In the design, step 1 has no PossDupFlag condition: 43=Y only blocks the gap check (step 2) and the update in step 3.
  failure: Send Heartbeat 34=7, then a Logon with 141=Y, 43=Y and 34=1, then Heartbeat 34=3. By the design's steps, step 1 sets expected to 1, so the last message gives 'expected 1, received 3'. The code keeps expected at 8 and emits no gap. AC8's wording about 43=Y not changing the expected number could be re
- F7 [medium, conf 85] src/timeline.js:39 The direction key is built from null for a missing 49 or 56, not from the empty string. A message missing the tag and a message with an empty value are therefore tracked as different directions.
  failure: Message 1 has no 49, with 56=SELL and 34=1. Message 2 has 49= (empty), 56=SELL and 34=5. Both should use the key ('', 'SELL') and give 'expected 2, received 5'. The code uses [null,"SELL"] and ["","SELL"], so no gap is emitted.
- proof F2: proven=True (AssertionError: assertion failed); test `test/timeline-kind.test.js > test_timeline_kind_is_session_or_order`
- proof F3: proven=True (AssertionError: assertion failed); test `test/timeline-gapfill-gap.test.js > test_timeline_gapfill_above_expected_emits_gap_before_event`

### Latest review: tier standard, cost $1.984, decision {'blocking': ['F2'], 'blocking_unproven': [], 'notes': ['F1', 'F3', 'F4']}
- F1 [medium, conf 70] src/timeline.js:44 The Logon 141=Y reset on lines 44-45 rewrites the direction's expected sequence number even when the message has no usable MsgSeqNum (34), contradicting AC7 ('a message with 34 missing or not a number ... doesn't change the expected number'). The reset is gated only on `previous !== undefined`, not 
  failure: For one direction, a log of Heartbeat 34=1, 34=2, 34=3 (expected becomes 4), then a Logon with 141=Y but no 34 tag, then Heartbeat 34=4: line 45 sets expected to 1 for that direction even though seq is null, so the following Heartbeat 34=4 satisfies `seq > expected` and emits a spurious SequenceGap 
- F2 [high, conf 97] src/timeline.js:44 The Logon 141=Y reset runs even when MsgSeqNum 34 is missing or not a number. The guard checks only 43, 35, 141 and whether the direction already has an expected number, not `seq !== null`. So an unchecked message changes the expected number.
  failure: All in one direction: (1) 35=0, 34=7; (2) 35=A, 141=Y, no 34 (or 34=abc); (3) 35=0, 34=10. The spec skips the reset for message 2, so expected stays 8 and the gap reads `expected 8, received 10`. The code sets expected to 1 and outputs `expected 1, received 10`. If message 3 has 34=8, the spec gives
- F3 [medium, conf 92] src/timeline.js:53 A SequenceReset with 36=0 sets the expected number to 0. `sequence()` accepts any string of digits, including zero, but NewSeqNo applies only when it is a positive integer. Otherwise the expected number should be 34 + 1.
  failure: All in one direction: (1) 35=0, 34=1; (2) 35=4 without 123=Y, 34=5, 36=0; (3) 35=0, 34=6. The spec sets expected to 6 after message 2, so there is no gap. The code sets it to 0 and emits SequenceGap `expected 0, received 6` before message 3.
- F4 [medium, conf 85] src/timeline.js:39 The direction key uses null for a missing 49 or 56 instead of the empty string. `value()` returns null and that goes straight into `JSON.stringify([sender, target])`. A missing tag and an empty tag are therefore tracked as separate directions.
  failure: (1) 35=0 with no 49, 56=SELL, 34=1; (2) 35=0 with `49=` (empty), 56=SELL, 34=5. The spec gives both the key ("", "SELL"), so SequenceGap `expected 2, received 5` comes before message 2. The code uses the keys [null,"SELL"] and ["","SELL"] and emits no gap.
- proof F2: proven=True (AssertionError: assertion failed); test `test/logon-reset-missing-seq.test.js > test_timeline_logon_reset_without_numeric_seq_keeps_expected_number`

Fix feedback trigger: review
