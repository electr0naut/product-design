# Append-Only Feedback and Changes

## Problem

Resolving a review comment edited the decision that raised it, so the record
could not show who objected or when it cleared. `changes[].status` had the same
defect. Schema v1 also stored resolution only as prose.

## Scope

- Decisions keep immutable `feedback` entries (`id`, `text`).
- `feedback_events` record `resolve` or `reopen`, with text, time, author and
  evidence. Status is the latest event per feedback id; no event means open.
- Changes are immutable declarations; `change_events` record resolution the same
  way. A resolved change still requires a decision newer than the resolve event.
- `migrate_manifest.py` converts v1: resolved feedback becomes a resolve event
  stamped with the decision time and `by: migrated-v1`; resolved changes become
  change events. It is idempotent, refuses unknown versions, and writes
  atomically.
- Schema v1 is refused by the evaluator with a migration hint; there is no dual
  reader.

## Invariants

- Event ids are unique across feedback events, change events and answers.
- Events for one subject must be in non-decreasing time order.
- Reopening a resolved objection blocks the lane again.
- A resolution is evidence, not approval.

## Acceptance criteria

- [ ] An unresolved comment blocks a lane even after a later approval.
- [ ] Resolving it unblocks without editing the decision record.
- [ ] Reopening blocks again.
- [ ] Migration preserves outcomes and is idempotent.
- [ ] A v1 manifest fails validation with a migration instruction.

## Test plan

`test_review_records.py` migration and question tests, plus
`test_gate_reviews.py` feedback and change cases.
