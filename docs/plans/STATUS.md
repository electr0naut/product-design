# Next-phase planning status

The generic product-design scaffold is the scope; FIX is only a later test run. This file tracks the Step 1 implementation sequence.

## Working rules
- CodeRabbit reviews every PR: wait for it, then fix or answer every comment in
  the PR thread. Never merge with an unanswered comment, never dismiss a review,
  never edit branch protection. If no review arrives within 30 minutes, do not
  merge: note it here and move on.
- End every commit message with `Model: <model name>`. If the model changes
  mid-task, discard the partial work, restart from the last green commit, and
  name the new model in the next commit.
- Read `docs/plans/INBOX.md` only between tasks, never mid-task; move handled
  items here under "Done" with the commit that handled them.
- Record every merged PR here with two plain-English sentences: what changed and
  what could break.
- Scaffolding phase: you may merge your own PRs once make check and CI
  are green and no review comment is left unanswered. The owner reviews
  afterwards and reverts if needed.
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
  In plain English: the scripts can now report how far any document has got in review — draft, waiting for reviewers, blocked, needing fresh sign-off, or approved — without changing a single file. It could mislead if the report were wrong, so a document only counts as approved when every required reviewer signed off on exactly those words.
- Implemented Step 1b on `feat/step1b-provenance-snapshot`: provenance sidecars now record a historical review snapshot (`snapshot_version`, `output_review_status` with artifact, status, evaluation date, manifest path/SHA-256, scopes and warnings) and a separate `input_gate_readiness` receipt (gate, lanes evaluated, gate completeness, decision IDs, per-lane policy hash). Readiness is never copied into approval, and the snapshot is explicitly historical. `assume_sha256` projects not-yet-written bytes with unchanged path/symlink/non-regular checks; the manifest is re-read, re-hashed and re-evaluated at snapshot time, and generation fails closed if the manifest, input artifacts or gate readiness changed during the model run. The document is written before its sidecar so a failed write cannot leave provenance describing unwritten bytes, and snapshot fields cannot overwrite the measured document hash. No draft routing, promotion or gate change. 15 focused tests; `make check` passed with 148 Python tests plus 6 subtests. PR #15 squash-merged as `1bbc2c1` after all five current-head checks passed on `641fbdd`.
  In plain English: each generated document now carries a small receipt saying which reviews unlocked the step and what review state the new file was in. The receipt can only be wrong if the review records change while the model is writing, and in that case generation stops instead of writing a misleading receipt.
- Adopted the owner's working rules in `AGENTS.md` and above, and created `docs/plans/INBOX.md` (commit `a6c4ca3`, PR #17, merged as `14320f6`). Known deviation: PR #17 was opened at 19:26 and merged at 19:34, eight minutes later and before the new rule's 30-minute review window, because no CodeRabbit review, comment or check appears on any PR in this repository. The change was documentation only and was merged under the owner's explicit merge-when-green instruction for that PR. The rule stays in force for later PRs; if no independent reviewer is connected, later PRs must wait the full window and be left unmerged.
  In plain English: the rules for how future changes are committed, reviewed and queued now live in the repo instead of in chat. The risk is that a reviewer expected to check these changes is not actually connected, so nothing was independently reviewed.

## Open
- Ordered next work (one small PR each): (a) security triage — PR #18 makes `actions/checkout` set `persist-credentials: false`; there are no CodeRabbit findings to triage because it never reviewed; Dependabot's only alert (Next.js image-optimization RCE) is already fixed and CodeQL reports zero alerts. (b) nanoid "DoS via infinite loop" — PR #19 records in `docs/security/dependency-audit.md` that the lock resolves 3.3.20, outside both affected ranges, with `npm audit` reporting zero vulnerabilities, so no dependency change is needed. Both PRs are CI-green. Review gate: PR #18 was opened at 19:36 and PR #19 at 19:37; both waited the full 30-minute window with no CodeRabbit review, comment or check, so per the working rule they are left open and unmerged for the owner either to connect CodeRabbit or to merge explicitly.
- Then Step 1c (draft path routing and copy-only promote) and Step 1d (`CLAUDE.md` correction).
- Story directories (`06-backlog/<product>/`) are written by the story importer, which creates no provenance sidecars; snapshot coverage there remains a gap for 1c.
- Queued, not started: mutation testing with mutmut on changed lines only in `gate_reviews.py` and `backlog.py`, advisory, tests only, with before/after scores and an explanation of surviving mutants. It waits until Step 1 (1b–1d) is merged.
- Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this planning pass.
- `CLAUDE.md` still describes approvals as unenforced; its correction is deferred to Step 1d per the owner's ordered PRs.

## Questions
- None blocking: the owner answered the Step 1 policy questions in `step1-owner-decisions.md`. Stop and ask if implementation would require weakening a gate.
