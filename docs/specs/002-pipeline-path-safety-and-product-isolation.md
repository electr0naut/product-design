# Pipeline Path Safety and Product Isolation Specification

## Problem

The pipeline discovers product inputs with loose prefix matching and follows filesystem symlinks when reading or writing managed artefacts. This can contaminate one product's prompt with another product's content or redirect a trusted run outside the intended workspace.

## Scope

- Select only the seven exact phase-02 analysis artefact names for a product when generating a BRD.
- Reject symlinked discovered Markdown inputs.
- Reject symlinked managed output files and parent directories.
- Preserve explicit external input/output paths only when they are not symlinked.

## Non-goals

- Build a sandbox for arbitrary third-party filesystems.
- Change the phase directory layout.
- Add approval-state enforcement.

## Invariants

- A BRD for slug `my-product` never includes an artefact for `my-product-v2`.
- A discovered input must be a regular, non-symlink Markdown file.
- A write through a symlink is rejected before any content changes.
- Existing valid local paths retain their current CLI behaviour.

## Acceptance criteria

- [ ] A prefix-neighbour artefact is excluded from the BRD prompt.
- [ ] A symlinked analysis document is rejected.
- [ ] A symlinked output target is rejected and its external target remains unchanged.
- [ ] Existing generation tests remain green.

## Test plan

- Unit/integration tests in `shared/scripts/tests/test_backlog.py`.
- Full `make check` verification.

## Rollout and rollback

No migration. Users with symlink-based inputs or outputs must use a real file instead.
