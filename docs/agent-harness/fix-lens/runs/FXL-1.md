# FXL-1: BLOCKED for a human

## FXL-1 · reviewer (fix 1) (t_ff6d389a) is blocked
```
  [2026-11-26 01:24] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:25] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:26] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:27] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:28] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:29] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:30] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:31] [run 226] heartbeat {'note': 'review running'}
  [2026-11-26 01:32] commented {'author': 'default', 'len': 102}
  [2026-11-26 01:32] [run 226] blocked {'reason': 'FXL-1: 2 proven, 0 blocking-unproven, 0 notes, 0 skipped for budget; $1.153 (see review.json)', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #226 blocked      @reviewer  607s  2026-11-26 01:22
        → FXL-1: 2 proven, 0 blocking-unproven, 0 notes, 0 skipped for budget; $1.153 (see review.json)
```

Run files: base.txt, find-raw-1.txt, findings.json, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, proofs.json, readiness.json, refutations.json, repo.txt, review.json

## Run summary
Fix pass: pass 1 triggered by gates
- First attempt's gates: {"passed": false, "missing_acs": ["AC8"]}; lint True; pass_to_pass True
- Latest gates: {"passed": true}; lint True; pass_to_pass True

### Latest review: tier standard, cost $1.153, decision {'blocking': ['1', '2'], 'blocking_unproven': [], 'notes': []}
- 1 [high, conf 95] src/framing.js:13 The code finds '8=FIX' by substring search without checking if it is at a field boundary (start of text, or immediately after a delimiter).
  failure: For input '58=resend 8=FIX.4.2\x0135=0\x0110=123\x01' (no real message, only '8=FIX' embedded in tag 58's value), indexOf returns 12 and the parser emits a candidate starting at offset 12 with fields [{tag:35,value:'0'},{tag:10,value:'123'}]. AC3 requires this to return an empty list because the '8=
- 2 [high, conf 92] src/framing.js:24 The field-end calculation only recognises '\n' as a line terminator; '\r' and '\r\n' are not handled, so a trailing '\r' is included in the field value and the checksum regex /^\d{3}$/ fails.
  failure: For input '8=FIX.4.2\x0135=0\x0110=123\r\n' (valid per AC5, which explicitly lists \r\n as a terminator), nextNewline finds the '\n' at position 23, fieldText becomes '10=123\r', value is '123\r', the regex rejects it, the loop breaks on the '\n', foundChecksum stays false, and the function returns 
- proof 1: proven=True (AssertionError: assertion failed); test `test/framing-boundary.test.js > splitMessages field boundary > 8=FIX embedded in another field value returns empty list`
- proof 2: proven=True (AssertionError: assertion failed); test `test/framing-crlf.test.js > splitMessages line terminators > recognises a checksum field terminated by CRLF`

Fix feedback trigger: gates


## Models and cost so far (everything since the hold was released; only FXL-1 has run)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | qwen3.7-plus | alibaba-token-plan | 2 | 69 | 237476 | 39053.0000 |
| planner | qwen3.7-plus | alibaba-token-plan | 1 | 26 | 139050 | 13500.0000 |
| reviewer | qwen3.7-plus | alibaba-token-plan | 1 | 2 | 47350 | 34612.0000 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 30594 | 4278.0000 |

Claude (refuter and prover) on the retry's review: $1.153 (`review.json`).

## What this means
Nothing here is a harness failure: the queue is holding exactly as designed. The first attempt failed the gates (AC8: the `test/helpers/fix.js` BodyLength/CheckSum example had no test), the one automatic fix pass added it and passed the gates, and then the retry's review found **two proven bugs in `src/framing.js`**, each with a failing test the prover wrote (`test/framing-boundary.test.js` for AC3, `test/framing-crlf.test.js` for AC5). A second failure blocks for a human, so the card `FXL-1 · reviewer (fix 1)` is `needs_input`. I have **not** unblocked it, edited the repository, or touched the trusted main (still the operator's initial commit `544c8c5`). FXL-2 to FXL-7 wait behind it.
The patch is not written: nothing from FXL-1 reached the trusted `main`. The branch `harness/FXL-1` (with the unfixed bugs) is in `work/fix-lens` for inspection.
