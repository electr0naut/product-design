# Output Safety and Prompt Preservation Specification

## Problem
Existing output directories can hide symlinked ancestors, and prompt-only generation can overwrite a reviewed prompt without `--force`. Story imports can delete existing files before discovering an unsafe target.

## Scope
All generated outputs, fallback prompts, story files, and traceability reports reject symlinked paths before writes or deletes. Prompt-only generation preserves existing prompts unless forced. Explicit external outputs use the same path policy.

## Non-goals
A sandbox against concurrent filesystem mutation or privileged attackers; atomic multi-file imports.

## Invariants
- No output follows a symlink at any component below a trusted filesystem root. The top-level system aliases `/tmp` and `/var` are allowed (macOS `/var` commonly aliases `/private/var`), but symlinks below them are not.
- Output paths containing `..` are rejected rather than normalized past a symlink.
- Repository-managed paths are checked from the repository root down; explicit external paths follow the same checks, not a weaker policy.
- No force-import deletes story files until all affected existing and destination paths have passed safety checks.
- Existing `.prompt.md` content remains unchanged without `--force`; skip succeeds (exit 0). Fallback prompt collisions fail (exit 1) without `--force` because generation could not complete. Invalid story responses cannot replace an existing saved `.response.md` without `--force`.

## Acceptance criteria
- [x] An existing descendant below a symlinked directory cannot receive a write, including prompt-only, story-import, and report paths.
- [x] Unsafe story force-import leaves existing story content unchanged.
- [x] Prompt-only collision skips without changing bytes; `--force` overwrites.
- [x] External non-symlinked paths under normal `/tmp` remain usable.

## Test plan
- CLI tests for existing descendant, story import and report safety.
- CLI prompt-only collision and forced regeneration tests.
- Full `make check` and `git diff --check`.

## Rollout and rollback
Previously accepted symlink-based external paths must be replaced by real directories. No migration.
