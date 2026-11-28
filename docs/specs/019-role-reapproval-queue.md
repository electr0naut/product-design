# Role reapproval queue (Step 2, review-flow slice)

## Problem
A role that approved a lane disappears into “Blocked on other roles” even after its reviewed artifact changes or a later question answer/change resolution requires that role to decide again. The queue then hides the action from the person who must take it.

## Scope
Derive structured role-specific actions from the existing gate evaluator and use them when sorting lanes into the read-only portal queue. An approval still current for that role remains in “Blocked on other roles” when another role or a dependency blocks the lane. Changed artifact bytes, an answer recorded after that role's decision, or a resolved change after its decision require renewed review. An unanswered question addressed to that role needs an answer; unresolved feedback raised by that role needs resolution, not another automatic approval. These move into the existing `pending_for_role` section, which the UI labels “Needs your attention” rather than implying all actions are approvals. Retain the existing JSON queue sections and owner-operated decision recorder.

## Non-goals
No claim-card parser, risk ranking, answer recording, UI write endpoint, status override, new approval, change to gate readiness, or Atlassian sync. This is the first narrow review-flow correction, not the whole Step 2 queue design.

## Invariants
- The gate evaluator is the single source of truth for per-role action kinds (`review_again`, `answer_question`, `resolve_feedback`); the portal does not reimplement timestamp, feedback-event or hash comparisons.
- A historical `approve` does not count as current after its hash changes or a later answer/resolution; one role's action does not claim another role's decision. Feedback resolution is an owner-operated event, never an inferred approval.
- Another role's question, feedback, stale decision, or an upstream dependency does not turn a current approval into a fresh approval request.
- Projection reads only; never write or synthesize `review/*.json` decisions, feedback, answers, or changes.

## Acceptance criteria
- [ ] A changed artifact after approval puts the affected role's lane in `pending_for_role` rather than `blocked_on_others`, with a `review_again` action.
- [ ] A later answer or resolved change requires only that role's renewed review; an unanswered question for that role has an `answer_question` action, and its own unresolved feedback has `resolve_feedback` (including feedback on an older decision).
- [ ] A current approval waiting solely on another role or dependency stays `blocked_on_others`, even with another role's unanswered question, and gate readiness is unchanged.
- [ ] Portal and CLI projections preserve exact manifest bytes and decision IDs/count.

## Test plan
- Unit tests with real manifest fixtures for stale hashes, later answers, resolved changes, unanswered questions, and feedback on an older decision; combine each with another role's blocker to verify isolation.
- CLI `check_gate.py --role` test for the same read model and unchanged manifest bytes; run `make check`.

## Rollout and rollback
Additive evaluator metadata and a queue classification change. No manifest migration. Revert the projection changes to restore the previous view; existing decisions remain untouched.
