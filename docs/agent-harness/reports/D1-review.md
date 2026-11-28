# D1 review: bounded fix loop (`agent-harness@60bb2f3`)

**Good structure. Not approved for switch-on yet: one required fix, two smaller ones.** Verified in the reviewing
session: `153 passed in 56.15s`, and ruff is clean. The D0 prover symlink fix (`3892b3b`) is correct and tested.

These are right:
- the pass count lives in a host-only ledger, written before any card is created;
- there's no code path to a third attempt;
- transient gate errors and unproven findings never trigger a retry;
- the retry needs `host = true`.

## Required: a proven bug must stay proven until it's fixed

After a review-triggered fix pass, the ticket passes if the **fresh** review finds nothing. But the finder isn't
deterministic. It can simply miss the same bug the second time, and the implementer is allowed to edit tests. So
a ticket can pass the retry with its proven bug still in the code. That's worse than today, where a proven bug
always stops the ticket.

**Fix:**
1. When `request_fix` is triggered by a review, store each proven finding's proof test (file, id, source) in
   **host-only** state, next to the ledger: for example `~/.local/state/agent-harness/proofs/<KEY>/<n>/`.
   - Don't rely on `fix-1.json`. It's in `work/runs`, which the container can write.
2. In the retry's review, before the finder runs:
   - copy each stored proof test into a clean worktree of the new head, with `copy_nofollow`;
   - run it through `prove_cmd`;
   - if it's still an assertion failure (`proof_outcome` is True), the finding is still proven, so block
     (`needs_input`) with no further pass;
   - if it errors (`None`), block too, because "can't tell" isn't "fixed".
   - Only when every stored proof passes does the fresh review continue as normal.
3. **Tests:**
   - a stored proof that still fails blocks, even when the fresh finder reports nothing;
   - a proof that now passes lets the review continue;
   - a proof test that errors blocks;
   - the proofs are read from host-only state, so an edited `fix-1.json` changes nothing.

## Smaller fixes

1. **The ledger must fail closed.** `read_ledger` returns `[]` on any `OSError` or `ValueError`. A corrupt or
   unreadable ledger would then reset every ticket's count, and the next write would erase it.
   - Treat only a **missing** file as empty.
   - Raise a `HarnessError` on anything else, so the card blocks.
   - Test: an unreadable or corrupt ledger blocks, and the file is left as it was.
2. **Log the swallowed block failure.** `request_fix` drops `HarnessError` from `block` silently. Keep the
   recovery, but log the card id and the error.

## Answers

1. **Switch-on:** not yet. After the required fix, run the seeded-fail check you proposed, with fixloop on, on a
   fixture ticket and a fresh trusted repo. Run it twice:
   - one variant whose bug the implementer can fix: expect the ticket to complete after one pass;
   - one it can't, for example a gate failure from a stale base: expect a block after one pass, and no third
     card.

   If both behave as expected, leave `enabled = true`. Undo is `false`, as you said. That's approved here, with
   no need to ask again.
2. **Mixed proven and unproven findings: no retry.** Block as today. A fresh review doesn't carry the first
   review's unproven findings forward, so retrying could drop them unseen. Retry only when `blocking_unproven`
   is empty. Add a test.
3. **The `sudo chown`:** yes, it goes to the user. Leave it as a stop and carry on.

## Note

The probe cards on the live board were harmless, and you cleaned them up. Even so, cards created on the live
board count as live changes: ask on PR #47 first next time.

## Next

Fix the above, run the switch-on check, report as `D1.1-fixes.md`, then go on to D2.
