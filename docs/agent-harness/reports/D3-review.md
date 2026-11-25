# D3 review: mutation testing (`agent-harness@c92fadc`)

**Approved, report-only. Switch it on.** Verified in the reviewing session: `239 passed, 3 skipped in 68.38s`
(the 3 need the real engines in the container), and ruff is clean.

- **The design is right:** the mutation field never changes `passed`, its errors become `ran: false`, and only
  changed lines count.
- **`unrun` is the right call.** Catching the Stryker/Vitest `describe` problem and refusing to report those
  mutants as "survived" is exactly the honesty the gates need.
- **The real fixture result is useful.** The `ROUND_HALF_UP -> None` survivor points at the same weak test the
  review found by a different route.
- **The D3.0 risk-key fold is correct,** and the config test caught the second duplicate table before the
  commit.

## Missing from D3: the fix-pass test rule (do it first, as D3.1)

`D2.1-review.md` gained a section after you'd pulled it: **"Answer: a fix pass that deletes or edits an existing
test"**. It isn't in D3. Do it now, before anything else, with its three tests:
- on a fix pass, an edit to or deletion of a test that exists on the first attempt's head blocks for a human;
- a test added in the first attempt can still be fixed;
- on a first pass, touching a base test makes the ticket high-risk.

## Answers

1. **Switch-on: approved.** Set `[mutation] enabled = true` in the container's `harness.toml`, then run:
   - one Python fixture ticket;
   - one JS ticket whose tests are top-level `test()` calls.

   Check that `passed` is unchanged and the added time is within about 60 s. Undo is `false`.
2. **The `describe` problem:**
   - Spend at most 30 minutes finding out whether a Stryker or Vitest setting, or a version pin of
     `@stryker-mutator/vitest-runner`, fixes it. Search the Stryker issue tracker for the symptom first.
   - If something does, use it and add a real-engine test.
   - If not, keep `unrun` plus the warning, and add one line to the JS card text: "prefer top-level `test()`
     calls; mutation testing can't see tests inside `describe`."
   - Don't rewrite the JS fixture's existing tests.
3. **Attribution by coverage is enough.** The signal "this changed line survives the whole suite" is what a
   reviewer needs. Don't add one mutmut run per acceptance criterion.

## The ownership probe

Don't loosen permissions to test them. Your probe left both folders at mode 777 for a few seconds. To show that
`hermes` *could* `chmod`, check the owner with `stat`: a uid that matches `hermes` already proves it. I'm asking
the user to check the `sudo chown`.

## D4: the last overnight item, a live JavaScript run

After D3.1 and the switch-on check, run the JS fixture (JSN-1, then JSN-2) through the **live** pipeline: real
triage, planner, implementer, gates, the Qwen finder and the Claude refuter and prover. You don't play any stage
by hand this time.
- **Why:** the model-written JS proof and the JS card text have never run. The FIX Lens pilot depends on both.
- **Also run the J1 seeded bug** as a variant: expect it to be caught, proven, sent through one fix pass, then
  completed.
- **Report as `D4-js-live.md`:** per-ticket models, cost, the tier, the mutation field, and the hidden-test
  score (expected 9/9).

After D4, stop and wait. FIX Lens needs the user's Gate 3 approval first.
