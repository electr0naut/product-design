Save this message verbatim as docs/plans/step1-owner-decisions.md on the
docs/next-phase-step1 branch, commit and push it, then act on it.

Answers to the open questions on PR #11:

1. Assumption warning: 7 calendar days before review_by, configurable,
   visible only. It must not affect readiness. Expiry keeps blocking.
2. A generated output is never `approved` at creation. It starts as
   `draft`; record input-gate readiness separately, as the spec says.
3. Naming: `.draft.md` for single files, `<product>.draft/` for split
   PRDs and story directories. With --draft, refuse an --out path that
   is a canonical (non-draft) path. Promotion is an explicit, separate
   command that copies the bytes to the canonical path and never
   approves anything; the output enters `in_review` only once it is
   enrolled in a manifest lane.
4. Granularity: per artifact, with gate/lane reasons underneath, as
   proposed.

Before coding:
- Tell me the state of the uncommitted work on
  feat/review-provenance-and-portal-hardening. Finish or park it first
  so the two branches do not conflict.

Then implement in this order, one focused PR each, test first:
  a) pure read-only status projection + tests (no file layout changes)
  b) provenance snapshot fields
  c) draft path routing and promote command
  d) CLAUDE.md fix
Run make check before each PR. Update STATUS.md and push after each.
Stop and ask if a gate would need weakening.