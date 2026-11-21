# Implementation Gate and Backlog Lock

## Problem

`scaffold_code.py` read only the technical design, so stories could be edited
after approval and the implementation plan would still be generated. Gating
files the generator never consumed would have been theatre.

## Scope

- `validate_backlog.py` writes `06-backlog/<product>/backlog.lock.json` only when
  the backlog passes: BRD and PRD file hashes, plus every story path and hash.
- The lock records split-PRD files individually (`prd_files`), so editing one
  epic is visible.
- `scaffold_code.py` requires the lock, re-hashes every locked file, refuses on
  any mismatch, then checks the `backlog-to-implementation` gate over the design,
  the lock and every story. It bundles exactly those bytes and re-verifies them.
- `--draft` remains the explicit, stderr-labelled escape hatch; it bypasses the
  gate, never the lock.

## Invariants

- Validation failure never writes a lock.
- A stale story, BRD or PRD file is reported by path, with the instruction to
  re-run validation and re-approve.
- The gate runs before any output path is created.
- The lock is a declaration of what was validated, not an approval. Approval is
  a decision bound to the same hashes.

## Acceptance criteria

- [x] A passing validation writes a lock with both stories.
- [x] Editing a story after validation blocks the plan and names the file.
- [x] An unapproved backlog blocks; `--draft` writes a labelled draft.
- [x] Generated prompts contain the design and stories but no unselected content.
