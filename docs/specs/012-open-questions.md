# Open Questions

## Problem

Review questions lived as free text inside documents, with no stable ID, owner
or blocking rule. The role portal cannot ask a stakeholder to answer a question
it cannot identify.

## Scope

- Manifest `questions`: `id` (`Q-001`), `gate`, `lane`, `role`, `text`,
  `source` (`artifact`, `heading`), `raised_at`.
- `question_answers` are append-only: `text`, `answered_by`, `answered_at`,
  `ai_assisted`, `evidence`, optional `model` and `excerpt_sha256`.
- The question's source artifact must be one of the lane's artifacts and the
  role must be required by that lane.
- An unanswered question blocks its lane. An answer alone does not unblock: the
  role's latest decision must be newer than the answer, because the answer is
  evidence and the document edit invalidates prior approval.

## Non-goals

- Automatic question extraction into the manifest. Proposed extraction must be
  accepted by a human.
- Treating an AI-drafted answer as a decision.

## Acceptance criteria

- [ ] A lane with an unanswered question is blocked and names the question.
- [ ] After an answer without reapproval, the lane is blocked with
      `question needs reapproval`.
- [ ] A newer decision from the question's role unblocks it.
- [ ] Unknown question ids, roles, artifacts and out-of-order answers fail
      validation.

## Test plan

`test_review_records.py::test_questions_block_until_answered_and_reapproved`.
