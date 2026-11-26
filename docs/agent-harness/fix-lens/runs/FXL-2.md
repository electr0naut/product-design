# FXL-2: BLOCKED for a human

## FXL-2 · reviewer (fix 1) (t_4d479ff8) is blocked
```
  [2026-11-26 03:40] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:41] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:42] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:43] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:44] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:45] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:46] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:47] [run 262] heartbeat {'note': 'review running'}
  [2026-11-26 03:47] commented {'author': 'default', 'len': 149}
  [2026-11-26 03:47] [run 262] blocked {'reason': 'reviewer runner failed: reviewer profile call failed (1): session_id: local-d838c8accf7f87709b2d123cf34613070836b84ab036cfa17151ca8ea6a3639f', 'kind': 'transient', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #262 blocked      @reviewer  530s  2026-11-26 03:39
        → reviewer runner failed: reviewer profile call failed (1): session_id: local-d838c8accf7f87709b2d123cf34613070836b84ab036cfa17151ca8ea6a3639f
```

Run files: base.txt, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, readiness.json, repo.txt

## Run summary
Fix pass: pass 1 triggered by gates
- First attempt's gates: {"passed": false, "missing_acs": ["AC1"], "over_budget": [{"ac": "AC2", "valid_tests": 5, "max": 3}]}; lint True; pass_to_pass True
- Latest gates: {"passed": true}; lint True; pass_to_pass True

Fix feedback trigger: gates

## Diagnosis (read-only; nothing unblocked, nothing changed)
**This is an infrastructure failure, not a finding about the ticket.** FXL-2 passed its gates after the one gate-triggered fix pass (first attempt: `missing_acs: [AC1]` and AC2 over the test budget, 5 valid tests against a maximum of 3; retry: `passed: true`, lint and pass-to-pass true). Then the retry's **review never happened**:
- The card `FXL-2 · reviewer (fix 1)` (`t_4d479ff8`) is blocked, `kind: transient`: `reviewer runner failed: reviewer profile call failed (1): session_id: local-d838c8ac...`.
- The reviewer profile's session (`state.db`, read-only): model `qwen3.7-plus`, started 03:39, ended 03:47 (**525 s**), `api_call_count 0`, input and output tokens 0, `end_reason cli_close`. The only reply in it is the stock line **"Your request was not processed. Send it again if you still want me to carry it out."** So the Qwen provider accepted the call and returned nothing for nearly nine minutes, then the session closed with exit 1. No review, no `review.json`, no Claude call (cost $0).
- The runner records the failed attempt and blocks the card; the **one-attempt-per-card rule** (`reviewer-attempts.json`) means unblocking the card would only make the runner refuse it again ("already attempted once"), so a plain unblock does not help. Previous Qwen finder calls in the same hours (FXL-1's reviews, 03:20 and earlier) worked.
- Run files: no `find-raw-*.txt`, no `review.json`; the gates' result (`gates.json`, `passed: true`) and the fix feedback (`fix-1.json`) are intact. The trusted main is still FXL-1's `8057bbf`; FXL-2 has not landed.

## Options (all for the reviewer or the user; I did none)
1. **Retry the review once:** remove the card's entry from `work/reviewer-attempts.json` and unblock the card (one attempt more for the same head, no fix pass spent). I will not edit the attempt record by hand without an instruction.
2. **Reload FXL-2 from scratch** on the current base: archive its cards and reload, which also spends no fix budget (a new attempt on a changed base only if the base moved; FXL-2's base is `8057bbf`, so the same-base rule would give no new passes).
3. **A harness change (D10), which I recommend either way:** a transient failure of the finder call (empty or "not processed" reply, no API call made) should be retried once automatically, with a short pause, before the card blocks; only a second failure blocks. The finder is free (Qwen), the card is not a ticket failure, and today a single provider hiccup holds the whole queue for a human. A bounded retry keeps "never silently approve" intact (the finder still has to return a valid answer).

## Block cause and the one retry (per FXL-2-review.md)

**Cause (read-only):** the provider was not down. The reviewer session (03:39:09, qwen3.7-plus, alibaba-token-plan) made **1 API call**, not 0 as written above, and the stream was cut at 03:47:54 by Hermes: "Stream cut: the reasoning turned into a runaway repetition loop". It returned a 309-char notice after 524.5 s. No quota or rate-limit error is in the profile's logs.
**Provider check:** one tiny `reviewer` call at 09:02 answered `pong` in 13 s (qwen3.7-plus, 1 API call).
**Action at 09:05 (as the review instructs):** removed only `t_4d479ff8` from `work/reviewer-attempts.json` (other entry kept; backup in the scratchpad), then `hermes kanban unblock t_4d479ff8`, once. The fix ledger was not touched.

## Model per stage (FXL-2)

Planner: **qwen3.7-plus** (fallback; Hermes logged "Fallback activated: gpt-6-sol → qwen3.7-plus" at 02:30 and 03:13). Triage, implementer, finder: qwen3.7-plus. A planner check call at 09:03 answered on **gpt-6-sol** (openai-codex), no fallback, state.db session model gpt-6-sol. From now on each FXL-<n>.md lists the model per stage.
