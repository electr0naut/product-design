# FXL-1B, attempt 2: the spec pass worked, and the card budget cut off the proofs

**This is the result D10 was built for.** The spec pass found three deviations, and I had independently found the
same kind of thing by reading patches:
- **F4** is the prefix bug FXL-1B exists to fix. A prefix with `=` still hides the message.
- **F2** is a critical regression of FXL-2's rule: `||` is no longer reported.
- **F3** drops messages with other BeginStrings, where the PRD says to report them as an unsupported version.

The refuter let all three stand. The finder's F1 is proven. Gates passed on the full test list (D11 works).

**Answer to the budget question:** the proofs were skipped by the **card** budget. `Runner._claude` caps a review
at `[review] max_usd_per_card`, default $3.00. The spec pass plus four refutations plus one proof reached $2.38, so
the next proof wouldn't fit. That's a real sizing issue: with the spec pass on, a review with several findings
needs more than $3. The per-ticket ceiling, `[budget] ticket_max_usd`, stays at $8.

## Decision (as the user's delegate)

1. **Raise the review card budget for `fix-lens` to $5.00** (`[review] max_usd_per_card = 5.0` in
   `eval/fix-lens/harness.fixlens.toml`), with a config test. Leave the per-call limits and the spec budget as
   they are.
   - Commit it **on top of `d12-deploy`**, so the user installs D12 and this together, in one line.
   - Don't fast-forward `master` until I've seen the commit.
2. **After that deploy:** remove FXL-1B's reviewer card from the reviewer attempts file and unblock it **once**.
   The review reruns in full under the new budget.
   - If all four findings are proven, the decision has no unproven blocking findings, so the one review-triggered
     fix pass starts, with four failing tests behind it.
   - If something is still unproven, the card blocks again, and I decide.
3. **Restart the evidence driver** with your `KeyError` fix (operator tooling, fine), after the deploy.

## Why not reset and rerun from scratch

The implementation is close. The gates pass, and the findings are specific. A full rerun would throw that away,
and a new attempt could introduce different bugs. Rerunning the review with room for proofs, then the one fix
pass with failing tests, is the cheaper and more reliable path.

**Expected cost of the rerun:** about $2.40 for the review again, plus about $1.50 for the proofs, plus the fix
pass's review. Roughly $5 in total for FXL-1B, within the $8 ticket ceiling.
