# D7: the fix-pass budget per kind and per attempt (branch `d7-fix-budget` @ `76ddf7c`, NOT merged, NOT deployed)

Branch `d7-fix-budget` on `agent-harness`, one commit on kit `master` (`c6451f5`), pushed for review only (`git ls-remote` confirmed; `master` unchanged). From a fresh clone: `288 passed, 3 skipped`, `ruff check` and `ruff format --check` clean. It is built and tested tonight, **not deployed**: the harness is not changed while a ticket is in flight (FXL-1 is blocked, FXL-3 is running now). The user runs the deploy line in the morning, as with D5.

## What changes
1. **One pass per kind.** An attempt gets at most **one gate-triggered pass and one review-triggered pass**, in either order, never two of the same kind and so never more than two. Unchanged: unproven findings never trigger a pass, mixed proven and unproven findings block, stored proofs are rerun on every later retry, a fix pass that touches base tests blocks. `[fixloop] max_retries` becomes `max_per_kind` (the old key is still read; the host config now says `max_per_kind = 1`).
2. **Per attempt.** An attempt is a key on a base: the ledger records `base` in every entry and the budget counts entries for the same `(key, base)`. A rerun from scratch on a new trusted `main` is a new attempt with its own budget; a rerun on the same base gets none. **An entry written before this change has no `base` and counts against every base** (fails safe: it can only cost budget, and only for its own kind). Card and file numbering still counts every pass of the key ever recorded, so a rerun's cards (`(fix 2)`, `implementer-fix2`...) never reuse an old idempotency key.
3. **Order inside one attempt.** The second pass works on the **newest live cards**: the failed card must be the highest-numbered `(fix N)` card of its stage (or the original); the new implementer card chains on the previous implementer card, the scribe moves from the old reviewer card to the newest one, and a gate failure archives the reviewer card that will never run. Stored proofs from a review pass are rerun on every later retry **of the same attempt** (`attempt_entries`), not on a rerun with a new base. The "fix pass edits a base test" rule compares with the attempt's **first** head.

## Tests (all in `tests/test_fixloop.py`, 8 new; 2 older ones adjusted for the explicit base)
- a gate pass, then proven findings: a review pass is granted (cards `(fix 2)` chained on `(fix 1)`, scribe follows the newest reviewer, ledger `[gates, review]`);
- a second review failure blocks; a second gate failure blocks; **never three passes** (four more requests of both kinds after two passes: all refused, ledger stays at two);
- a new base gets a fresh budget (ledger `retry: 2`, cards `(fix 2)`); the same base does not;
- a legacy entry without a base counts against every base (and only for its own kind);
- the attempt filter and the first-head rule; the ledger still fails closed for the budget too (corrupt ledger: refused, file untouched, no cards); the host config names `max_per_kind`.

## A consequence for FXL-1's rerun you should know about
FXL-1's current ledger entry (gate-triggered, written before D7) has **no base**, so under the rule as specified it counts against the rerun too: the rerun would have no **gate-triggered** pass, only a review-triggered one. If you want the rerun to start with a full budget, say so; options: (a) a small one-time migration that adds `base` (derivable as the merge-base of the entry's `head` and the trusted `main`, `544c8c5`) to entries that lack it, run by code, not edited by hand; (b) leave it (fail safe). I did not add (a).

## Not done
No deploy, no merge, no change to FXL-1 or to `work/fix-lens`. Morning plan from the FXL-1 review: after the user's deploy, archive FXL-1's cards and reload FXL-1 alone.
