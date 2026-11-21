# Step 1 plan: derived review states (proposal only)

Scope: generic product-design scaffold; no FIX product changes. This plans only Step 1 of `docs/plans/next-phase.md`. The behavioural contract is `docs/specs/015-derived-review-states.md` and remains unapproved until the owner resolves its open policy choices.

## Baseline and design
1. Keep `gate_reviews.py` as the sole authority. Today `evaluate_gate()` emits `ready`, `reasons`, decisions and hashes; `maybe_enforce_gate()` returns `None` for explicit draft or missing manifest. Do not derive status from the existing provenance sidecar or from `ready` alone: readiness refers to inputs of the next generator, not approval of its output.
2. Add a pure projection over validated manifest history, current artifact hashes and an explicit evaluation date. Return status plus all reasons for each gate/lane/artifact. Treat invalid manifests/unsafe or missing artifacts as errors. Preserve the current JSON contract's `ready` field and add fields rather than breaking portal consumers.
3. Specify precedence and prior-approval evidence in tests before implementation. An open hold wins over stale approvals; previously fully approved scopes whose hashes change require reapproval. Missing roles before any full approval remain in review. Dependency blocks are explicit and scoped, not silently converted into approvals.
4. Extend provenance with an explicitly historical snapshot: output hash, `output_review_status`, manifest relative path/hash when present, evaluation date, and separate input-gate receipt (gate, lanes, decision IDs, policy hashes). Do not retrofit `review_status: gated` into `approved`; a successful generator run only says its input gate was ready then.
5. Route new draft outputs to visibly draft paths only after agreeing on naming and promotion. Check `--out` collisions and symlinked ancestors before writes. Keep existing unsuffixed outputs readable; do not move them or rewrite historical sidecars. The acceptance test must cover both one-file and multi-file/story outputs.
6. Expose impending assumption `review_by` as a non-blocking warning ahead of expiry; retain the current expiry blocker. Update `CLAUDE.md`'s obsolete statement during the eventual implementation.

## Test-first sequence (not started)
- Add failing evaluator tests for every state, precedence, changed bytes, resolved changes/answers, dependency isolation, invalid manifests, and warning date boundary.
- Add failing CLI/provenance tests for draft/no-manifest, gated generation without output approval, manifest hash snapshot drift, explicit output paths, old sidecars, split PRD/story roots and no-overwrite/symlink safety.
- Implement the pure evaluator, then sidecar snapshot and draft-path routing in separate focused commits. Run targeted tests, `make check`, independent spec review, and CI; stop rather than weakening gates on failure.

## Decision points before code
- Confirm warning lead time (proposed 7 calendar days) and whether warning should be non-blocking.
- Confirm `.draft.md`/`<product>.draft/` naming and how a human promotes draft bytes into a canonical review path *before* approval; include backwards compatibility for explicit `--out`.
- Confirm whether the desired five-state vocabulary applies per artifact, per lane, or both; proposed read model is per-artifact with underlying gate/lane reasons, while input-gate readiness remains separate.

No steps 2–4, portal redesign, decision-constraint prompts, or Atlassian integration are included here.
