# Story Response Import Integrity Specification

## Problem

A model response can contain unknown, missing, duplicate or contradictory story identifiers. The current importer can write partial or misleading backlog files while returning success.

## Scope

Validate every story response for one selected epic before any existing story file is deleted or a new file is written.

## Non-goals

- Change the PRD story-map format.
- Add a full YAML parser.
- Redesign the backlog validator.

## Invariants

- Response marker IDs equal the selected epic's expected story-ID set exactly.
- Each marker occurs once.
- Every story has frontmatter.
- Frontmatter `id` equals its marker ID.
- Frontmatter `epic` equals the selected epic.
- A rejected response leaves all existing story files unchanged.

## Acceptance criteria

- [ ] Unknown, duplicate, missing or mismatched IDs return a nonzero result.
- [ ] Invalid responses write no new story file and delete no existing story file.
- [ ] A valid complete response retains current `--force` overwrite semantics.
- [ ] Existing generation and validation tests remain green.

## Test plan

- Unit/integration tests for invalid saved responses passed through `generate_stories.py`.
- A regression test verifies an existing story remains byte-identical after rejected import.

## Rollout and rollback

No migration. Existing malformed responses must be corrected and re-imported.
