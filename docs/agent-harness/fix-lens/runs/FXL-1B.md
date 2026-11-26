# FXL-1B: BLOCKED for a human

## FXL-1B · reviewer (t_a012b041) is blocked
```
  [2026-11-26 15:27] [run 301] claimed {'lock': 'ailab:361504', 'expires': 1795705045, 'run_id': 301}
  [2026-11-26 15:28] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:29] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:30] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:31] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:32] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:33] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:34] [run 301] heartbeat {'note': 'review running'}
  [2026-11-26 15:34] commented {'author': 'default', 'len': 104}
  [2026-11-26 15:34] [run 301] blocked {'reason': 'FXL-1B: 1 proven, 3 blocking-unproven, 0 notes, 0 skipped for budget; $2.3768 (see review.json)', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #301 blocked      @reviewer  444s  2026-11-26 15:27
        → FXL-1B: 1 proven, 3 blocking-unproven, 0 notes, 0 skipped for budget; $2.3768 (see review.json)
```

Run files: base.txt, find-raw-1.txt, findings.json, gates.json, implement.json, plan.json, proofs.json, readiness.json, refutations.json, repo.txt, review.json

## Run summary
Fix pass: none
- Latest gates: {"passed": true, "unmapped": ["test/framing.test.js > AC6: field structure > records tag as number, value as string, and position of tag start"]}; lint True; pass_to_pass True

### Latest review: tier high, cost $2.3768, decision {'blocking': ['F1'], 'blocking_unproven': ['F2', 'F3', 'F4'], 'notes': []}
- F1 [high, conf 92] src/framing.js:51 The delimiter-adjacent 8=FIX check does not verify that the '8=FIX' is followed by a valid message-start character (delimiter, '.', line end, or text end).
  failure: Input '8=FIX.4.4|9=5|35=0|8=FIXCLIENT|10=123|' ends the first candidate at the '8=FIXCLIENT' position (because text.substring matches '8=FIX' and prev is '|'), then findMessageStart rejects '8=FIXCLIENT' (next char 'C' is invalid). Result: one candidate with fields [8,9,35] and the trailing '10=123'
- F2 [critical, conf 99] src/framing.js:203 The change makes checkMessage stop at any empty piece (`if (fieldText === "") break;`) and removes FXL-2's handling of an empty piece between delimiters. `||` is no longer reported as field_without_equals, and the pieces after it are no longer checked by rules 1 and 2. The ticket required keeping wh
  failure: Take `8=FIX.4.4|9=5||35=0|10=NNN|`, where BodyLength matches the bytes after `9=5|` (here `|35=0|` is 6, so use `9=6`) and NNN is the correct checksum. splitMessages skips the empty piece, so fields are 8, 9, 35, 10. rawFields stops at the `||`, and checkMessage returns null, so the message is accep
- F3 [high, conf 97] src/framing.js:371 The new filter in findMessageStart starts a candidate only if `8=FIX` is followed by `.`, a delimiter, a line end or the end of the text. The design has no such condition, so BeginStrings such as FIXT.1.1 are silently dropped.
  failure: splitMessages("8=FIXT.1.1|9=5|35=0|10=123|") returns [] because the character after `8=FIX` is `T`. It should return one candidate, which is later labelled unsupported version FIXT.1.1. The message vanishes with no decode and no error, and it is also left out of the message count.
- F4 [high, conf 92] src/framing.js:394 A prefix containing `=` still hides the message when it matches `\b\d+=`, even though the line before `8=FIX` has no delimiter and the preceding character is not a digit. AC1 allows no such exception.
  failure: For `thread 1=main 8=FIX.4.4|9=5|35=0|10=123|`, the character before `8=FIX` is a space and the prefix has no `|` or SOH. The regex matches `1=`, so splitMessages returns []. It should return one candidate starting at offset 14. A prefix such as `10.0.0.1=gw 8=FIX.4.4|...` is hidden in the same way.
- proof F1: proven=True (AssertionError: assertion failed); test `test/f1-invalid-start.test.js > F1: delimiter-adjacent 8=FIX that is not a message start > does not end the current candidate at 8=FIXCLIENT`
- proof F2: proven=None (budget); test `None`
- proof F3: proven=None (budget); test `None`
- proof F4: proven=None (budget); test `None`
