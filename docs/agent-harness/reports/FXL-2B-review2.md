# FXL-2B: the edit to `test/helpers.test.js` is approved

The fix pass only **adds** a `checkMessage(...) === null` assertion to a test that FXL-2B's own first pass added.
No expected value changes, and nothing is weakened. The pipe-byte CheckSum correction is in the first pass, which
a first pass may do (it made the ticket high-risk, as designed). On the fix head:
- the container suite is 65 of 65;
- the hidden `acc-check` is **9 of 9** and `acc-framing` 9 of 9, so the CheckSum bug is fixed, by the independent
  reference values.

**Approve this edit once.** Run `tools/approve_test_edit.py FXL-2B --head <fix head 356ab44, full sha> --files
test/helpers.test.js --reason "FXL-2B-review2: fix pass only adds an assertion to a test this ticket added; hidden
acc-check 9/9"`. Then clear the gatekeeper (fix 1) card's attempt if it's there, unblock it once, and comment on
PR #47.
