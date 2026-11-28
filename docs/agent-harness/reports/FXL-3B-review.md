# FXL-3B: the fix pass edited `test/dictionary.test.js`, which this ticket requires

FXL-3B **exists to rewrite that file**:
- AC1: the new argument order, tested;
- AC2: the reproducibility test builds into a temporary folder;
- AC4: top-level `test()` calls.

So an edit is expected. That's exactly the D14 case: the ticket should have declared
`may_edit_tests = ["test/dictionary.test.js"]`.

## Decision (as the user's delegate): approve, on an objective condition

Run the hidden acceptance suite (`acc-dictionary`, plus all the others for regressions) against the **fix head**,
with a scratch trusted root, as you did for FXL-2B. Also run the fix head's full `vitest run` in the container.

- **If `acc-dictionary` is 4 of 4, nothing that passed before regresses, and the suite is green:** record the
  approval:

  ```
  tools/approve_test_edit.py FXL-3B --head <fix head, full sha> --files test/dictionary.test.js --reason "FXL-3B-review: ticket requires rewriting this file; hidden acc-dictionary 4/4 on the fix head"
  ```

  Then clear the gatekeeper card's attempt if it's there, unblock it once, and post the numbers in `FXL-3B.md`.
- **Otherwise:** don't approve. Put the full diff of `test/dictionary.test.js` (first head to fix head) in
  `FXL-3B.md`, and wait for me.

The hidden suite is the independent check that the edit didn't weaken anything that matters. That's why this
approval can depend on its result rather than on a person reading the diff.
