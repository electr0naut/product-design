# BRD Analysis Completeness Specification

## Problem
A single analysis currently allows a BRD to be generated as if all seven role reviews were present.

## Scope
Require the exact seven product analysis filenames by default. `--allow-partial-analysis` opts into exploratory prompts or BRDs from at least one exact match.

## Non-goals
Changing naming conventions, accepting prefix neighbours, or checking human approval.

## Invariants
Only exact filenames for the idea slug are selected. Duplicate exact role filenames in different directories fail closed. Missing names are reported deterministically before a prompt, document or fallback is written. No matches still fail even with opt-in.

## Acceptance criteria
- [x] Default missing roles fail with exit 1 and list missing names without writing output.
- [x] Seven exact files pass; prefix neighbours are excluded.
- [x] Opt-in partial run succeeds with at least one match; none still fail.

## Test plan
CLI tests for partial/default/opt-in, complete inputs and prefix neighbours; `make check`.

## Rollout and rollback
Intentional tighter default; pass `--allow-partial-analysis` for exploratory work.
