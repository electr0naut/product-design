# Next-phase planning status

This branch contains a proposal, not an approved implementation. The generic product-design scaffold is the scope; FIX is only a later test run.

## Working rules
- Scaffolding phase: you may merge your own PRs once make check and CI
  are green. The owner reviews afterwards and reverts if needed.
- Never write, edit or synthesise decisions, feedback events, answers or
  change events in any review/*.json manifest. Only record_decision.py,
  run by the owner, records decisions.
- When the scaffolding skeleton is declared complete, autonomous merging
  ends: open PRs and wait for the owner to merge.

## Done
- Saved the planning-session document verbatim in `docs/plans/next-phase.md` (commit `d3271b2`).
- Inspected the current review manifest evaluator, provenance writer, existing gate/provenance specs, repo instructions, and spec template on the `main` baseline.
- Isolated this documentation branch in a separate worktree; the in-progress provenance/portal code on `feat/review-provenance-and-portal-hardening` is untouched and uncommitted.
- Proposed Step 1's behavioural contract in `docs/specs/015-derived-review-states.md` and an execution sequence in `docs/plans/step1-derived-review-states.md`; no Step 1 code was changed.
- Reviewed the proposal against product-scoped gate discovery: a draft suffix must not change the product slug or bypass another product's manifest. Added multi-lane status aggregation and a regression criterion for this path.
- Opened draft PR #11 for the Step 1 proposal: https://github.com/electr0naut/product-design/pull/11. It is not approved or merged.
- Owner decisions were recorded verbatim in `docs/plans/step1-owner-decisions.md` (commit `f25e789`): seven-day visible-only warning; generated outputs start draft; canonical `--out` refused under `--draft`; explicit copy-only promotion; per-artifact status with lane reasons.
- Parked all 31 tracked/untracked paths on `feat/review-provenance-and-portal-hardening` in `stash@{0}` (`park review-provenance-and-portal-hardening before Step 1 series`); that worktree is clean. No parked code was brought into this branch.

## Open
- Implement Step 1 as four focused, test-first PRs in owner-specified order: read-only projection, provenance snapshots, draft routing/promotion, then `CLAUDE.md` correction. Run `make check` before each PR.
- Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this planning pass.
- `CLAUDE.md` still describes approvals as unenforced; update it when step 1 is implemented, not as an unrelated edit to this proposal.

## Questions
- None blocking: the owner answered the Step 1 policy questions in `step1-owner-decisions.md`. Stop and ask if implementation would require weakening a gate.
