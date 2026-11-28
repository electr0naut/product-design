# D10 review (`agent-harness` branch `d10-spec-review` @ `2057626`)

**Approved, with one change and a timing correction.** Verified in the reviewing session: `335 passed, 3 skipped
in 94.11s` (with `-p no:cacheprovider`), and ruff is clean.

- **The inputs:** host-only ticket text with a key check, spec documents that must sit outside the kit folder,
  and a block before any paid call when an input is missing.
- **The quote check:** a whitespace-normalised, word-for-word `spec_ref` of at least 12 characters. Dropped
  findings are listed in `review.json`.
- **Spec findings go through the refuter and the prover,** and the refuter is told to judge them against the
  quote. That's the design I asked for.
- **The acceptance runner:** host-only history that never shrinks on a regression, exit 4, and the driver holds
  the queue.

The ledger slip is well handled: it's reported, removed exactly, and the redirect is fixed, with a check that
live state is untouched.

The hidden suite now exists in `docs/agent-harness/fix-lens/acceptance/`, with the reviewer's baseline in its
README.

## Change before the merge

**A budget for the spec call itself.** With the whole diff plus the design, the call will often cost more than
the refuter's $0.75 per-call cap, and then every review blocks as `transient`. Add
`[review] spec_budget_usd` (default 2.0) and use it for the spec call only, with a test. The card's overall
budget still applies, as you built it. Then fast-forward `master` to the new sha.

## Timing: never change the harness under a running ticket

FXL-1b is in flight. Deploying D10 while its review is pending would change its review halfway through, which
breaks our rule. So:
1. **Move the hold now.** Link `HOLD: D10 deployed` (`t_01fb15de`) to **FXL-2b's** `triage` as well, if FXL-2b
   hasn't started. FXL-1b finishes on the current harness.
2. **When FXL-1b completes,** post it on PR #47. The user deploys then, so FXL-2b, FXL-3b and FXL-4 to FXL-7 all
   run with the spec pass and the hidden suite.
3. **Then complete the hold.**

## The user's lines

The reviewer gives them to the user directly, adapted for a plain shell (no `!`, which a shell reads as
"negate"). Don't paste the `!` versions to the user.

## Note for later

The loader records ticket text from the copies in `work/fix-lens-tickets/`, which the container can write. For
the next product, record the text from the host-side source (the product-design clone) instead. Not needed now:
step 4 already records from `~/product-design`.
