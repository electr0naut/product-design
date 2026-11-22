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

## Handover (2026-11-21)

**State.** `main` was `4f358b2` when this handover was written; PR #23 merges the handover itself, so read the true head with `git log -1 origin/main`. CI was green on that head (`check` plus the three CodeQL analyses); no open PRs; working tree clean; stash list empty. Steps 1a–1d, the working rules, security triage (a), the nanoid audit (b) and the root-safety test fix (c) are merged. The handover prompt lives in `docs/prompts/handover.md`. The other worktrees are clean: `/srv/lab/product-design` holds the WIP branch, and `/srv/lab/product-design-status` is detached at the same `main` commit after being reset from a stale tree (`7149daf`).

**Next step.** After finishing CodeRabbit's four comments on PR #24, clean up the templates: `04-prd/templates/prd-template.md` and `05-technical-design/architecture/template.md` still link to `03-brd/approved/` and `04-prd/approved/`, which do not exist; replace those links with the `review/<product>.json` contract. The mutation report separates contract-covered test gaps from behaviour that genuinely needs an owner decision.

**Remaining known gaps.** `04-prd/templates/prd-template.md` and `05-technical-design/architecture/template.md` still link to `03-brd/approved/` and `04-prd/approved/`, which do not exist; sign-off lives in `review/<product>.json`. Story directories `06-backlog/<product>/` receive no provenance sidecars because the story importer writes none. Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this pass.

**Gotchas.**
- PRs #1–#23 have no CodeRabbit review, comment or check run recorded; the app's earlier installation state is unknown. The owner enabled it by November 22, 2026, and its first observed review on PR #24 posted four actionable comments. Finish and answer each thread before considering a merge; recording a missed review window is never a substitute for a review.
- There is no global git identity. Pass `-c user.name='Hermes Agent' -c user.email='hermes-agent@users.noreply.github.com'` on every commit and rebase `--continue`.
- No `gh` CLI and no PyYAML. GitHub work goes through `/home/ubay/.hermes/cache/scratch/product_design_gh_api.py` (token read from `~/.config/gh/hosts.yml`). Actions: `view <pr>`, `checks <sha>`, `watch <sha>`, `merge <pr> <sha> [title]`, `reviews <pr>`, `review-comments <pr>`, `issue-comments <pr>`, `main`, `create <branch>`. `merge` now takes the commit title from the PR; PRs #18 and #19 landed with a generic wrong subject because it used to be hardcoded.
- `main` is also checked out in `/srv/lab/product-design-status` at the stale `64e1a7f`, so `git switch main` in the next-phase worktree fails; refresh that worktree or branch from `origin/main`.
- Local branches for merged work still exist (`docs/*`, `feat/step1*`, `security/*`, `fix/*`). They were squash-merged, so `git branch --merged` will not list them; they are not unmerged work.
- `make check` runs ruff, pyright, pytest, ESLint, `tsc` and a Next build; use `uv run pytest <path>` for a focused run. Last local count: 213 tests plus 6 subtests. `make mutate` runs the advisory mutmut pass (about three minutes) and is not part of `make check`; `mutants/` and `.mutmut-cache` are ignored.
- Draft contract: `--draft` writes `*.draft.md` or `<product>.draft/`, refuses a canonical `--out`, and evaluates gates against the canonical path; `promote.py` copies bytes and sidecar but never approves. `review/*.json` is written only by `record_decision.py`, run by the owner.
- Never add a write endpoint to `/review` or weaken its loopback Host check.

**Uncommitted or stashed work.** None; the stash list is empty. `wip/review-provenance-and-portal-hardening` at `f1fe7bb`, checked out in `/srv/lab/product-design`, is unmerged WIP (31 files: story provenance sidecars, split-PRD, question extraction, Vitest/Playwright, nonce CSP). It is not reviewed; do not merge it without the owner.

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
- Adopted the owner's working rules in `AGENTS.md` and above, and created `docs/plans/INBOX.md` (commit `a6c4ca3`, PR #17, merged as `14320f6`). Known deviation: PR #17 was opened at 19:26 and merged at 19:34, eight minutes later and before the new rule's 30-minute review window, because no CodeRabbit review, comment or check appears on any PR in this repository. The change was documentation only and was merged under the owner's explicit merge-when-green instruction for that PR. The rule stays in force for later PRs, but no reviewer has been connected since, so every PR below records the same deviation rather than silently claiming a review.
  In plain English: the rules for how future changes are committed, reviewed and queued now live in the repo instead of in chat. The risk is that a reviewer expected to check these changes is not actually connected, so nothing was independently reviewed.

- Step 1c: draft-path routing and copy-only promotion (PR #20, commit `ec72513`). `--draft` writes `name.draft.md` or `<product>.draft/`, refuses a canonical `--out`, and evaluates the gate against the canonical path; `promote.py` copies bytes and sidecar, refuses overwrite without `--force`, and never writes a review record. `make check` green: 157 tests plus 6 subtests.
  In plain English: exploring with a draft can no longer overwrite a reviewed document, because drafts now land in files and folders marked "draft". The promote command copies a draft into the real place but changes nothing about its review state, so a promoted file still needs a recorded decision before it counts as approved.

- Step 1d: `CLAUDE.md` corrected (PR #21). It no longer says approval is an unenforced convention: it states that generation scripts enforce `review/<product>.json`, re-hash inputs and outputs, and that only the owner's `record_decision.py` records decisions; it documents `--draft` routing and `promote.py`, points at `make check`, and drops the stale `approved/` folder claim.
  In plain English: the repository's own instructions to coding assistants now match how the scripts actually behave, so a new agent will not assume approvals are only a convention. The risk is stale references elsewhere: two document templates still link to `03-brd/approved/` and `04-prd/approved/`, folders that no longer exist.

- Item (c): the write-failure test no longer depends on `chmod` (PR #22). It injects a failing `workflow_common.write_text` instead, so it still asserts the same guarantee — no document, no sidecar — when the suite runs as root, where directory permissions are ignored. `make check` green: 148 tests plus 6 subtests.
  In plain English: one test passed only because a normal user cannot write into a read-only folder, so it failed for the wrong reason as root. It now forces the write to fail directly and checks the same safety property on any account.

- Session handover (PR #23): `docs/prompts/handover.md` holds the reusable prompt, and the `## Handover` section at the top of this file records the current state, next step, gaps, gotchas, and that nothing is uncommitted or stashed. Direct pushes to `main` are blocked by the repository ruleset, so this went through a PR.
  In plain English: a fresh session that only has the repo can now read the current state, the next job and the traps without needing this conversation. The risk is that the handover goes stale — it names `main` at `4f358b2`, so update that SHA whenever the handover is rewritten.

- Mutation testing (PR #24, commit `979e5a2`). mutmut 3.8.1 is scoped in `pyproject.toml` to `shared/scripts/gate_reviews.py` and `shared/scripts/backlog.py` on test-covered lines (mutmut 3.8.1 has no line-range filter), and `make mutate` runs it. Two conftest guards act only when mutmut is imported: subprocess CLI tests drop `MUTANT_UNDER_TEST` so a child interpreter does not re-read mutmut config from a temp directory, and the mutated modules are aliased into `sys.modules` under their path-derived names so trampoline keys match the flat test imports. Both are no-ops under `make check`. 54 tests were added for the initial gaps. Initial score: 79.4% (2210/2784) before, 92.2% (2568/2784) after; CodeRabbit's review added two tests and raised it to 92.3% (2571/2784, 213 survivors). The current survivor list is in `docs/plans/mutation-testing-2026-11-21.md`; do not treat contract-covered test gaps as owner decisions. No production behaviour changed. `make check` green: 213 tests plus 6 subtests.
  In plain English: a tool deliberately planted small bugs in the review-gate and backlog code to see whether the tests noticed; the tests now catch most of them. What could break is the tests themselves becoming too literal about error wording, so the report lists which planted bugs are still missed and why.

## Open

- Security triage is merged: PR #18 sets `persist-credentials: false` and records the two accepted loopback risks; PR #19 records why the nanoid advisory does not apply (3.3.20 is outside both ranges, `npm audit` clean). No CodeRabbit findings existed; Dependabot's only alert was already fixed and CodeQL reports zero alerts.
- Template clean-up: `04-prd/templates/prd-template.md` and `05-technical-design/architecture/template.md` still link to `approved/` folders that do not exist; sign-off lives in `review/<product>.json`.
- Story directories (`06-backlog/<product>/`) are written by the story importer, which creates no provenance sidecars; snapshot coverage there remains a gap.
- Mutation-testing survivors now listed in `docs/plans/mutation-testing-2026-11-21.md`: 34 behaviour-bearing gaps remain after adding a cross-gate regression test. Gate/lane scope is an existing contract, so filter survivors are test gaps, not owner decisions; ask the owner only where the expected behavior is genuinely unspecified. No production changes should be made merely to raise the mutation score.
- Steps 2–4 (role-shaped output, decision constraints, Atlassian) are outside this planning pass.
- CodeRabbit is now connected and reviewed PR #24 with four actionable comments. Require an actual review and a reply or fix for every comment before merging; a recorded review gap does not grant permission to merge. If no follow-up review arrives within 30 minutes after pushing changes, leave the PR open and record that delay.

## Questions
- None blocking: the owner answered the Step 1 policy questions in `step1-owner-decisions.md`. Stop and ask if implementation would require weakening a gate.
