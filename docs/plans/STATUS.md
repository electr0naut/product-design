# Next-phase planning status

The generic product-design scaffold is the scope; FIX is only a later test run. This file tracks the Step 1 implementation sequence.

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
- Isolated the planning and Step 1a branches in separate worktrees from the in-progress provenance/portal code (subsequently parked below).
- Proposed Step 1's behavioural contract in `docs/specs/015-derived-review-states.md` and an execution sequence in `docs/plans/step1-derived-review-states.md`; no Step 1 code was changed.
- Reviewed the proposal against product-scoped gate discovery: a draft suffix must not change the product slug or bypass another product's manifest. Added multi-lane status aggregation and a regression criterion for this path.
- PR #11 for the Step 1 proposal was merged as `09f18ec` after CI passed.
- Owner decisions were recorded verbatim in `docs/plans/step1-owner-decisions.md` (commit `f25e789`): seven-day visible-only warning; generated outputs start draft; canonical `--out` refused under `--draft`; explicit copy-only promotion; per-artifact status with lane reasons.
- Parked the uncommitted work on `feat/review-provenance-and-portal-hardening` in a named stash (31 tracked/untracked paths: provenance and PRD-generation changes, portal/CSP code, JS/Python tests and CI wiring). The feature worktree was clean at `07083fa`; none of it was merged or brought into Step 1a.
- Moved that parked work off the VM: applied the stash on `wip/review-provenance-and-portal-hardening`, committed it as `f1fe7bb` and pushed the branch; the local stash was then dropped. The branch is WIP only — not reviewed, not merged.
- Implemented Step 1a on `feat/derived-artifact-status`: live, read-only per-artifact projection with underlying lane/gate reasons, seven-day configurable visibility-only assumption warnings, CLI status and exit codes, and 13 focused tests. No manifest, provenance, output-path, draft-routing, promotion or gate-enforcement changes. Independent review identified and we fixed multi-scope artifact-change false approval, historical nonoverlapping approval, and malformed-manifest CLI error handling. Local `make check` passed: 133 Python tests plus 6 subtests, Ruff, Pyright, ESLint, TypeScript and Next.js build. PR #13 squash-merged as `8c6823e` after all five current-head checks (`check`, `CodeQL`, three CodeQL analyses) passed on `bb2c0f7`.
- Implemented Step 1b on `feat/step1b-provenance-snapshot`: provenance sidecars now record a historical review snapshot (`snapshot_version`, `output_review_status` with artifact, status, evaluation date, manifest path/SHA-256, scopes and warnings) and a separate `input_gate_readiness` receipt (gate, lanes evaluated, gate completeness, decision IDs, per-lane policy hash). Readiness is never copied into approval, and the snapshot is explicitly historical. `assume_sha256` projects not-yet-written bytes with unchanged path/symlink/non-regular checks; the manifest is re-read, re-hashed and re-evaluated at snapshot time, and generation fails closed if the manifest, input artifacts or gate readiness changed during the model run. The document is written before its sidecar so a failed write cannot leave provenance describing unwritten bytes, and snapshot fields cannot overwrite the measured document hash. No draft routing, promotion or gate change. 15 focused tests; `make check` passed with 148 Python tests plus 6 subtests. PR #15 squash-merged as `1bbc2c1` after all five current-head checks passed on `641fbdd`.

## Open
- Nothing in progress: Steps 1a and 1b are merged and this status records them. Waiting for the owner before starting 1c.
- Steps 1c–1d remain deferred: draft path routing and promote command, then the `CLAUDE.md` correction.
- Story directories (`06-backlog/<product>/`) are written by the story importer, which creates no provenance sidecars; snapshot coverage there remains a gap for 1c.
- Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this planning pass.
- `CLAUDE.md` still describes approvals as unenforced; its correction is deferred to Step 1d per the owner's ordered PRs.

## Questions
- None blocking: the owner answered the Step 1 policy questions in `step1-owner-decisions.md`. Stop and ask if implementation would require weakening a gate.
