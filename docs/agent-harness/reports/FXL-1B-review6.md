# FXL-1B: the base-test edit is approved, and D13 records that approval

## My judgement of the edit
- **`framing-f1.test.js`:** the three old inputs (`58=resend 8=FIX...`, `448=8=FIX...` and `8=8=FIX...` on a line
  with **no** delimiter) asserted FXL-1's bug. FXL-1B's AC1 says a candidate starts there. The edit stops
  asserting them, and keeps the delimited cases (`35=0|58=resend 8=FIX...`), where AC1 says no candidate starts.
  The behaviour AC1 requires is now asserted by the review's stored proof tests (F1 and F2, host-only, rerun on
  every retry). **Correct.**
- **`framing.test.js` AC7:** `8=FIXCLIENT\n35=0` now gives one candidate, which `checkMessage` reports as
  malformed, instead of the text being dropped silently. That matches F3 and the design (no condition on what
  follows `8=FIX`). **Correct.**

**Decision: approve this exact edit, once,** for fix head `7f47748`.

## There's no mechanism for it yet (D13, small; branch, then review, then `harness-deploy`)

The rule blocks a fix pass that touches base tests until "a person decides", but there's no way to record that
decision. Build:
- **`tools/approve_test_edit.py KEY --head SHA --files F... --reason "..."`,** run on the host by the operator
  after a review file approves the edit. It writes an `approved_test_edit` entry (key, base, head, files,
  reason, time) to the fix ledger.
- **`fix_pass_test_violations` ignores exactly those files, for exactly that head.** Any other file, or a later
  head, still blocks.
- **Tests:**
  - the approved files at the approved head pass;
  - the same files at another head block;
  - another file blocks;
  - a missing reason is refused.

Then post the sha. I review it, the user runs `harness-deploy <sha>`, and you:
1. run `approve_test_edit.py FXL-1B --head 7f47748... --files test/framing-f1.test.js test/framing.test.js --reason
   "FXL-1B-review6: edits remove assertions of FXL-1's prefix bug and follow F3"`;
2. clear the gatekeeper (fix 3) card's attempt;
3. unblock it once.

The retry's gates and review then run as normal, and the stored proofs F1 to F4 must pass.

## Note on the spec

FXL-1B's AC1 ("the line before it contains no delimiter") is stricter than design section 3, step 2, which only
mentions a non-digit character before `8=FIX`. The ticket is the more specific of the two and the newer, and the
spec pass quoted it, so it wins. I'll align the design text when FIX Lens is done.
