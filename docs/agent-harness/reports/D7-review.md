# D7 review: fix-pass budget per kind (`agent-harness` branch `d7-fix-budget` @ `76ddf7c`)

**Approved, with two small changes.** Verified in the reviewing session: `288 passed, 3 skipped in 72.91s`
(with `-p no:cacheprovider`), and ruff is clean.

- **Budget per `(key, base, kind)`:** a legacy entry counts against every base, and the ledger still fails closed.
- **`current_cards`** picks the newest live `(fix N)` card, so a second pass chains correctly.
- **The card numbering** counts every pass ever recorded, so idempotency keys are never reused.
- **Stored proofs** are rerun within the same attempt only. The base-test rule compares with the attempt's first
  head.

## Changes before the merge

1. **Make `base` a required argument of `request_fix`.** No default `""`: a caller that forgets it would count
   against a base that matches nothing. Both callers already pass it.
2. **Migrate legacy ledger entries: yes, option (a).**
   - Write a small tool, run once by code: for each entry without `base`, set
     `base = merge-base(entry.head, trusted main)`, computed in the host-only trusted repo with `GIT_SAFE`.
   - Write the file atomically, and save a copy as `fix-ledger.json.bak`.
   - If the merge-base can't be computed, leave the entry as it is (it stays fail safe).
   - **Test:** an entry gets the right base, an unresolvable one is left alone, and the backup exists.
   - For FXL-1 this gives `544c8c5`. Once FXL-3 has landed, FXL-1 reruns on a newer base with a full budget, which
     is what we want.

## Morning deploy (the user runs it; you prepare it)

When both changes are in and the tests pass, fast-forward `master` and post the sha. Then write in the report the
exact lines for the user, the same shape as last night:
- the deploy line for the host kit;
- the bundle-and-fetch lines for the container's copy;
- the migration command.

Then: archive FXL-1's cards and reload FXL-1 alone, as `FXL-1-review.md` says.
