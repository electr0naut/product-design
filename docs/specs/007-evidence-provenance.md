# Evidence and Generation Provenance Specification

## Problem
Legal/compliance drafts can sound authoritative without attributable sources or disclosed uncertainty. Generated documents do not record which input files and prompt/template bytes produced them.

## Scope
Legal and compliance instructions/templates request claim-level sources, jurisdiction, applicability assumptions, uncertainty, and human specialist review. Common single-document generation writes `<document stem>.provenance.json` beside a successfully generated document, containing source input paths and SHA-256 digests, instruction/template paths and digests, assembled-prompt and generated-document digests, UTC generation time, and model identifier (`null` when not reported by the CLI).

## Non-goals
No validation of source truth, legal conclusions, expert approval, reviewer identity, or model output quality. No sidecars for manually imported story responses, prompt-only files, or CLI-unavailable fallback prompts. No network calls or changes to gate/review workflows.

## Invariants
- A sidecar is an audit aid, not proof of accuracy or approval. Do not record reviewers, secrets, or assumed model names.
- Neither a generated document nor its sidecar is overwritten without `--force`; if either exists, skip both. With `--force`, both may be replaced after symlink checks. A symlinked sidecar, document, or ancestor is rejected before generation, including skip and force branches.
- A missing CLI may write a fallback prompt under existing rules, but never a provenance sidecar or document.
- Source digests reflect bytes loaded into the assembled prompt; the document digest reflects the written document bytes.

## Acceptance criteria
- [ ] Role instructions and templates demand verifiable sources, explicit unknowns and applicability assumptions, and human review.
- [ ] A generated document gets parseable provenance with inputs, prompt/template hashes, UTC timestamp, document hash and honest unknown model.
- [ ] Existing or symlinked sidecar/output is handled without unintended writes on normal, force, and fallback paths.

## Test plan
- Unit tests: `shared/scripts/tests/test_evidence_provenance.py` covers digest accuracy, prompt copy, unknown model, collision, symlink, fallback and prompt-only paths.
- Integration/CLI tests: fake executable analysis generation; no external service.
- Regression: targeted pytest and `make check`.

## Rollout and rollback
No migration. Existing documents are untouched unless explicitly forced. Removing sidecar generation leaves documents readable; sidecars may be retained for auditing.
