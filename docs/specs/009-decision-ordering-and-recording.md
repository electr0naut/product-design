# Decision Ordering and Recording

## Problem

Gate status used array order, so a packet written earlier but recorded later
could silently win. Typed reviewer names also had no recorded provenance, and
artifact hashes could be stale by the time a decision was committed.

## Scope

- Manifest schema v2 validates decisions per gate/lane/role in non-decreasing
  `recorded_at` order and rejects the whole manifest otherwise.
- Decisions may carry `source_commit` (the revision reviewed), `recorded_by` and
  an `attestation` of `typed-name, unverified` or `verified`.
- `record_decision.py` records an untrusted packet: it assigns decision and
  feedback IDs, re-hashes lane artifacts, refuses a stale approval, refuses a
  packet older than that role's latest decision, requires evidence, warns on
  free-text evidence, writes atomically, and supports `--verify`.

## Non-goals

- Identity verification or SSO. A typed name remains unverified.
- Automatic approval. Silence and unparsable packets never advance a gate.

## Invariants

- A packet's `artifact_sha256` must name exactly the lane's artifacts.
- A non-approval packet may be stale only with `--accept-stale`; an approval may
  never be accepted stale.
- IDs are assigned by the recorder, never chosen by the client.
- The manifest is replaced atomically; a failed write leaves the previous bytes.

## Acceptance criteria

- [ ] An approved packet appends one decision with `D-###`, server feedback IDs,
  the current hashes, the evidence and the unverified attestation.
- [ ] A stale approval exits 1 with the changed paths and does not modify the
  manifest.
- [ ] A stale change request exits 1 without `--accept-stale` and is recorded
  with it.
- [ ] A packet older than the role's latest decision is refused.
- [ ] Out-of-order decisions in a manifest fail validation.

## Test plan

`shared/scripts/tests/test_review_records.py`: recording, stale approval, stale
non-approval, ordering, unknown role, questions, portal view and migration.
