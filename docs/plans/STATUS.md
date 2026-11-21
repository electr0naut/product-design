# Next-phase planning status

This branch contains a proposal, not an approved implementation. The generic product-design scaffold is the scope; FIX is only a later test run.

## Done
- Saved the planning-session document verbatim in `docs/plans/next-phase.md` (commit `d3271b2`).
- Inspected the current review manifest evaluator, provenance writer, existing gate/provenance specs, repo instructions, and spec template on the `main` baseline.
- Isolated this documentation branch in a separate worktree; the in-progress provenance/portal code on `feat/review-provenance-and-portal-hardening` is untouched and uncommitted.
- Proposed Step 1's behavioural contract in `docs/specs/015-derived-review-states.md` and an execution sequence in `docs/plans/step1-derived-review-states.md`; no Step 1 code was changed.
- Reviewed the proposal against product-scoped gate discovery: a draft suffix must not change the product slug or bypass another product's manifest. Added multi-lane status aggregation and a regression criterion for this path.

## Open
- Review step-1 policy choices with the owner before coding.
- Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this planning pass.
- `CLAUDE.md` still describes approvals as unenforced; update it when step 1 is implemented, not as an unrelated edit to this proposal.

## Questions
- How many days before an assumption’s `review_by` should the warning appear, and should warning affect readiness or just visibility?
- Should a generated artifact ever carry `approved`, or only show that its *input gate* was ready at generation time? The proposed spec distinguishes these.
- What is the canonical draft output convention across single files, split PRDs, and story directories, including backwards compatibility for existing `--out` paths?
