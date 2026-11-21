# Derived Review States Specification (proposal)

## Problem
A generated draft and a reviewed document can have indistinguishable paths. The gate evaluator reports `ready` and reasons, while provenance records inputs but not a live review state. A sidecar can also become stale after a decision or edit. Reviewers need a status for the exact current bytes without trusting a hand-edited label.

## Scope
- Extend the existing schema-v2 gate evaluator with a read-only, per-artifact status projection. The manifest, current artifact hashes, decision/event history and evaluation date are inputs; status is never stored in the manifest. A sidecar records a timestamped snapshot of that projection, the manifest's repository-relative path and SHA-256, plus the output document SHA-256. The CLI/portal always recompute current status; a sidecar is not a live approval certificate.
- States: `draft` when explicitly generated with `--draft`, no manifest exists, or an output is not yet enrolled in any manifest lane; `in_review` when enrolled but required roles have not all approved; `on_hold` for a latest `request_changes`, unresolved feedback, an open change, an unanswered question or an expired assumption; `approved` only when all applicable required roles have current-hash approvals and all other existing gate rules pass; `needs_reapproval` when prior full approval is no longer current because artifact bytes changed, an answer or resolved change requires another decision. Invalid manifests and missing/unsafe artifacts fail closed as errors, not as any of the five states.
- Precedence when reasons coexist within one scope or across scopes reviewing the same artifact: invalid input (error), `on_hold`, `needs_reapproval`, `in_review`, `approved`. A never-approved scope with stale or missing decisions stays `in_review`; do not manufacture a historical `approved` state from a single role's decision. Show every underlying reason and affected gate/lane rather than concealing them behind one label. An artifact is `approved` only if every applicable scope is ready. A dependency's blocked state remains visible and prevents `approved` without relabelling unrelated lanes.
- A generated output is not approved simply because its *input* gate was ready. Provenance distinguishes `input_gate_ready_at_generation` and its gate/lane/decision IDs from `output_review_status`. At creation, a new output is `draft` until that output is enrolled and reviewed. The existing `review_status: gated` sidecar value on the in-progress branch is a generation-path receipt, not an artifact approval; migration must not map it to `approved`.
- Separate draft outputs from canonical reviewable paths: propose `.draft.md` for a single document and a `<product>.draft/` root for multi-file PRDs/backlogs, preserving story IDs/filenames inside that root. Resolve the canonical product identity *before* applying a draft suffix so manifest discovery and later artifact matching do not silently change products. Explicit `--out` paths must not silently overwrite the canonical file; display the actual draft path and require a deliberate migration/promotion step before review. Existing unsuffixed files and their sidecars remain untouched; detect their review state dynamically without renaming them in place.
- Warn before a linked assumption's `review_by` date (proposed default: 7 calendar days, configurable); the warning is visible in JSON/CLI and does not itself revoke readiness. Expiry retains the existing blocking semantics. The warning window is a policy choice to confirm before implementation.
- Update `CLAUDE.md` to match the already enforced approval gate when implementing step 1; it must not claim approval is merely a human convention.

## Non-goals
- No automatic approval, reviewer identity proof, changes to manifest decision records, role-shaped content, claim cards, decision-constraint prompts, Jira/Confluence, or implementation of steps 2–4.
- No status inferred from filenames, provenance sidecars, CI, or the existence of a generated document alone. No automatic rename/promotion of existing reviewed outputs.

## Invariants
- Python gate evaluation remains authoritative; the portal renders its read model and never reimplements status logic.
- Decisions bind current artifact bytes; latest decision per required role wins. Silence, stale hashes, unresolved feedback, open changes, unanswered questions, expired assumptions and blocked dependencies cannot yield `approved`.
- A draft override never bypasses source validation or permits sidecars to assert approval. A ready input gate does not approve the generated output.
- Manifest path/hash and output hash in a snapshot must describe the exact bytes read and written; missing or malformed manifests fail closed. A changed manifest invalidates the snapshot, never silently refreshes it.
- Existing canonical outputs and sidecars are not overwritten without the existing `--force` safeguard; draft-path migration may not silently alter existing source lists or story IDs.

## Acceptance criteria
- [ ] For the same enrolled artifact, adding current-hash approvals advances `in_review` to `approved`; a changed byte yields `needs_reapproval` after prior full approval, without changing the manifest or a hand-set status field.
- [ ] A latest change request, unresolved feedback, open change or unanswered question yields `on_hold`; a resolved change or answer still requires a newer approval, while unrelated lanes keep their prior state.
- [ ] No manifest, explicit `--draft`, or unenrolled output yields `draft` in the generated sidecar and is written only to a visibly draft path. A gated generation of a new output records input-gate readiness, not `approved` output status; suffixing a draft path does not change product identity or bypass another product's manifest.
- [ ] Sidecars contain the manifest path/hash when one was used, output hash, evaluation date and snapshot semantics; the live CLI detects a changed manifest or artifact and never treats a stale snapshot as authoritative.
- [ ] Invalid manifest, unsafe/missing artifact, or symlinked draft/output paths fail without producing a misleading status or overwriting existing files.
- [ ] An assumption within the agreed warning window is flagged before `review_by` and remains ready; after expiry it blocks the lane.
- [ ] `CLAUDE.md` accurately says configured gates are enforced before generation and no manifest is draft-only.

## Test plan
- Unit tests: status precedence and history across all five states; latest negative decision; per-lane independence; answer/change reapproval; assumption warning versus expiry; manifest hash and changed snapshot.
- Integration/CLI tests: no-manifest and `--draft` output path/sidecar, gated input versus unapproved new output, explicit `--out`, split PRD/story directories, collision/symlink/malformed manifest failures, old unsuffixed artifact compatibility.
- Fixtures or property tests: schema-v2 manifest with two independent lanes plus a cross-cutting lane; vary approval order, artifact bytes and dates; assert no blocked combination returns `approved`. Run `make check` and independent review before merge.

## Rollout and rollback
Start with read-only projection and tests, then add sidecar snapshot fields and draft-path routing. Keep accepting old sidecars and old unsuffixed files as historical inputs, but compute live status from the manifest. Do not rewrite them in bulk. If draft routing proves incompatible, roll back path changes without discarding manifest decisions; the evaluator remains authoritative. Exact draft naming and warning lead time require owner confirmation before coding.
