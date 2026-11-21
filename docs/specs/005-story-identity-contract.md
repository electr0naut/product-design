# Story Identity Contract Specification

## Problem
The importer compares normalized response markers against exact frontmatter while the validator normalizes frontmatter identities, making the two disagree.

## Scope
Use exact canonical `US-xxx` story-file names, frontmatter IDs and response-marker IDs and `Exx` epic frontmatter IDs. The filename ID must match frontmatter. PRD story-map syntax retains existing tolerant parsing; its resulting canonical IDs are the expected values for import. Remove unreachable importer warnings.

## Non-goals
Rewriting historic story files, tightening requirement references or changing PRD table syntax.

## Invariants
No importer or validator silently changes a story-file identity. Noncanonical or malformed marker-like lines and frontmatter fail import without modifying files; noncanonical frontmatter or a filename/frontmatter mismatch fails validation even if a normalized form matches a PRD row.

## Acceptance criteria
- [x] Lowercase, short-width or embellished story IDs are rejected consistently.
- [x] Canonical response import and backlog validation remain successful.

## Test plan
CLI import and validator regression tests, full `make check`.

## Rollout and rollback
Older noncanonical story frontmatter must be edited to canonical IDs before validation; no automatic migration.
