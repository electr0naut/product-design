# FXL-1B, attempt 2 ends blocked: rerun on the Codex implementer

**What happened:**
1. With the $5 budget, the review proved its findings.
2. The one review-triggered fix pass ran, on Qwen.
3. The retry's review then proved **two more** bugs:
   - **F1:** the prefix rule still rejects `digits=` prefixes and `=` directly before `8=FIX`. That's the
     ticket's own AC1, missed for the third time.
   - **F3:** `checkMessage` ignores `candidate.end`, so the next message's faults are blamed on the earlier
     candidate.
4. That was the second review failure in this attempt, so the ticket blocked, as designed.

The harness behaved correctly throughout: real bugs, proven with failing tests, and nothing landed. The
weakness is the implementer: Qwen keeps getting the boundary rules wrong.

## Decision (as the user's delegate)

1. **Apply `CODEX-implementer-review.md` now.** No implementer card is running: FXL-1B is blocked and the rest
   are waiting. Set the implementer profile to `gpt-6-sol`, falling back to Qwen and then DeepSeek, verify it
   answers, and do the restart only if Hermes needs one.
2. **Reset FXL-1B's attempt** with `tools/reset_attempt.py FXL-1B --reason "two review failures on the Qwen
   implementer; rerun on the Codex implementer (user approved)"`.
3. **Archive the FXL-1B cards, and the unstarted cards of FXL-2B, FXL-3B and FXL-4 to FXL-7.** Move FXL-1B's run
   folder to `work/old/runs-FXL-1B.attempt2`. Keep `FXL-1B.md` as `FXL-1B-attempt2.md`.
4. **Reload all seven in one call,** and restart the evidence driver.
5. **The new `FXL-1B.md` states the implementer model.** Comparing attempt 3 (Codex) with attempts 1 and 2 (Qwen)
   on the same ticket is the cleanest A/B we'll get.

Expected cost: one more full review, about $2 to $5 of Claude, plus Codex quota.
