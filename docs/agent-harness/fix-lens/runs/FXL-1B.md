# FXL-1B: BLOCKED for a human

## FXL-1B · reviewer (fix 2) (t_2d6d9207) is blocked
```
  [2026-11-26 18:17] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:18] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:19] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:20] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:21] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:22] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:23] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:24] [run 305] heartbeat {'note': 'review running'}
  [2026-11-26 18:25] commented {'author': 'default', 'len': 104}
  [2026-11-26 18:25] [run 305] blocked {'reason': 'FXL-1B: 2 proven, 0 blocking-unproven, 1 notes, 0 skipped for budget; $2.0408 (see review.json)', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #305 blocked      @reviewer  726s  2026-11-26 18:13
        → FXL-1B: 2 proven, 0 blocking-unproven, 1 notes, 0 skipped for budget; $2.0408 (see review.json)
```

Run files: base.txt, find-raw-1.txt, find-raw-2.txt, findings.json, fix-2.json, gates-2.json, gates.json, implement.json, plan.json, proofs.json, readiness.json, refutations.json, repo.txt, review-2.json, review.json

## Run summary
Fix pass: pass 2 triggered by review
- Latest gates: {"passed": true, "unmapped": ["test/framing.test.js > AC6: field structure > records tag as number, value as string, and position of tag start"]}; lint True; pass_to_pass True

### Latest review: tier high, cost $2.0408, decision {'blocking': ['F1', 'F3'], 'blocking_unproven': [], 'notes': ['F2']}
- F1 [high, conf 90] src/framing.js:412 findMessageStart has two extra rejections in the delimiter-free prefix branch. It rejects any prefix that begins with digits and '=' (/^\d+=/), and any '8=FIX' directly preceded by '=' (line 407). The spec requires only that the preceding character is not a digit and that the line before has no deli
  failure: splitMessages("1=yes 8=FIX.4.4|9=5|35=0|10=123|") returns [], but one candidate should start at offset 6. The text before it has no delimiter and the preceding character is a space. splitMessages("msg=8=FIX.4.4|9=5|35=0|10=123|") also returns [], but one candidate should start at offset 4, because '
- F2 [medium, conf 80] src/framing.js:380 The change adds a start condition that is not in the spec: '8=FIX' must be followed by '|', SOH, a line end, end of text, '.' or 'T'. Any other following character means no candidate starts, so the malformed message is never reported.
  failure: splitMessages("8=FIX4.4|9=5|35=0|10=123|") returns [], but it should return one candidate at offset 0. In "8=FIX.4.4|9=5|35=0|8=FIX 4.4|9=5|35=0|10=123|", the loop at line 52 ends candidate 1 at the second '8=FIX'. findMessageStart then rejects that start, so the second message disappears.
- F3 [high, conf 88] src/framing.js:203 splitMessages now ends a candidate with no CheckSum where the next one starts on the same line. checkMessage ignores candidate.end and re-reads the raw text up to the line end, including the new empty-piece handling. Faults in the next message are therefore reported against the earlier candidate.
  failure: For text "8=FIX.4.4|9=5|35=0|8=FIX.4.4|9=5||35=0|10=123|", candidate 1 covers offsets 0 to 19 and has no empty piece or CheckSum, so it should report missing_checksum. checkMessage(candidate1, text) instead returns field_without_equals at position 34, which is the '||' inside message 2.
- proof F1: proven=True (AssertionError: assertion failed); test `test/prove-f1.test.js > F1: delimiter-free prefix > accepts 8=FIX after a prefix starting with digits= or directly after =`
- proof F3: proven=True (AssertionError: assertion failed); test `test/f3-candidate-end.test.js > F3: checkMessage respects candidate.end > does not report the next message's faults against the earlier candidate`
