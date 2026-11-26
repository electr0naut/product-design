# D9 review: the whole diff is reviewed (`agent-harness` branch `d9-review-diff` @ `4b16baa`)

**Approved. Fast-forward `master` to `4b16baa`.** That's the one sha the user deploys in the morning, instead of
`feae6b2`. Verified in the reviewing session: `310 passed, 3 skipped in 79.82s`, and ruff is clean.

- **Per-file diffs are packed into chunks, and split by hunk when they need to be.** Every character lands in
  exactly one chunk, and a hunk that can't fit blocks with a reason. That's the fail-closed rule we wanted.
- **Excluded files are listed with their sizes in every finder prompt,** and `review.json` records
  `diff_chars`, `excluded` and `chunks`.
- **Finding ids are renumbered after merging, before the refuter and the prover run.**

## Known limits (accepted for the pilot)

- **A chunk is reviewed without the other chunks.** A bug that only shows when a test and its code are read
  together can be missed if they land in different chunks. That's still far better than never seeing the second
  file. Track it: if FIX Lens tickets regularly need more than one chunk, raise `max_diff_chars`, or pass each
  chunk the list of files in the other chunks.
- **Excluded files are never reviewed.** For `fix-lens`, `vendor/**` should never change after the operator's
  initial commit. Add `vendor/*` to `fix-lens`'s `high_risk_globs` in a later change, so any ticket touching it
  gets the full review, and its report says so. Not needed tonight.
