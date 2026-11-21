
# Next phase: review states, role-shaped review, decision feedback, Atlassian

Status: proposal from a planning session (not approved). Plan before coding.
Scope: the generic scaffolding for any product. The FIX lens is only a test run.

## Problem
1. A draft is indistinguishable from an approved document on disk.
2. Reviewers get walls of AI text; nobody reads them.
3. Later agents ingest that prose (stale or rotten context) and act on
   wrong assumptions.
Constraint: do not over-engineer or reinvent existing formats.

## Step 1: Derived review states (do first)
Compute status from the manifest, never set it by hand:
- draft: generated with --draft or without a manifest
- in_review: some required roles have not decided
- on_hold: request_changes, open change, or unanswered question
- approved: all required roles approved the current artifact hashes
- needs_reapproval: was approved, but artifact changed or a change resolved
Record the status, manifest path and manifest hash in the provenance sidecar.
Give drafts a distinct suffix or folder so they cannot be mistaken for
approved output. Approvals resting on assumptions get flagged before
review_by, not only after expiry.
Also: fix CLAUDE.md, which still says approval is not an enforced check.

## Step 2: Role-shaped outputs (two layers)
Decision layer (short, human): one page per audience.
- Executive: ask, recommendation, 2-3 options, cost, main risk, deadline,
  cost of saying no.
- Finance: few numbers, assumptions beside each, ranges, exact spend asked.
- Legal: claims relied on, with citation and jurisdiction.
- Compliance: obligation -> control mapping, gaps flagged.
- Operations: who does what differently on day one, volumes, failure
  modes, staffing impact.
Evidence layer (underneath): claim cards, one claim each, quoted source,
owning role. Reuse known formats: decision memo, ADR, RACI.
Review is a queue of small cards per role, riskiest first, ~10 per session.
Answers: agree / disagree / unsure / not my area + one line why.
Later rounds show only changed claims.
Extends the existing role review pages and question flow.

## Step 3: Decisions feed the next generation
Recorded answers and confirmed claims become locked constraints in the next
prompt. Agents read recorded human decisions and confirmed claims, never the
long generated prose. A signed-off answer always overrides generated text.

## Step 4: Jira and Confluence (last)
Personal free Atlassian sandbox, official Atlassian MCP server.
Repo stays the system of record; Atlassian is a view and an input channel.
- Approved docs -> Confluence pages stamped with hash and status.
- Epics/stories -> Jira, with traced requirements.
- One issue per gate/lane, one subtask per required role. A sync script
  turns a reviewer's action into a decision packet; record_decision.py
  still re-hashes and verifies.
- Changes and open questions as their own issue types.

## Sync rule
docs/plans/STATUS.md is the handoff to the planning session: done, open,
questions. Update and push after every meaningful step. The repo is
public: nothing confidential in these files.

## Hard rule
Agents may draft and publish through MCP. Agents never record an approval.

## Pushback to keep in mind
- Step 4 is where over-engineering creeps in. Ship steps 1-3 in the repo and
  try them with real reviewers before adding Atlassian.
- Do not add a hand-set status field; derive it, or it will drift.
- Content prompts are thin (BRD prompt ~84 words). Role-shaped outputs will
  only be as good as those prompts; strengthen them in step 2.
