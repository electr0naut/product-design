
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

## Step 2: Collaborative decision workflow (role-shaped inputs to the BRD)

The workflow is collaborative with feedback loops, not a linear sequence of standalone outputs. Decision briefs are inputs to the BRD, and the BRD is the gate document for the Risk Committee.

**Workflow.** Business Development pitches ideas to the executive commission (which includes the CTO, who estimates infrastructure needs and evaluates options and costs), which decides whether to assess. Legal and Compliance review whether we can do it — legally and regulatory-wise. Finance details what's needed to keep the books in line: the ledger model, billing, how to reflect activity, report producing, and the proofs needed to show collateralisation to a regulator (which may require collaboration with Legal and Compliance — the whole project requires syncing up and teams reviewing what the others produced and what they missed). Risk looks at how and whether we can model it. Product picks up all the moving parts: chasing open questions across teams, interfacing to get everyone in line, and producing the BRD. Operations is separate: they surface the tooling needed to operate the product on a day-to-day basis, with proper visibility over the health of the platform/product.

The BRD is the gate document that goes to the Risk Committee — at least one designated person from each team — who reads it, raises questions, pushes back or approves. From there: PRD (where the Head of Product coordinates with the CTO/Development team), then phased buildout. During the QA phase, Operations is brought in to be shown the runbooks that show the tooling, the decisions that need to be taken, the escalation paths, etc. Then the first trade is executed by Risk, reviewed by all teams, and if all sign off on their side of the window, the product is considered live and can get its first pilot clients.

**Decision briefs as BRD inputs.** Each team produces a short decision brief as their input to the BRD:
- Executive (including CTO): whether to proceed with assessment, infrastructure needs, options and costs (already done as #27, still valid)
- Legal: claims relied on, with citation and jurisdiction (already done as #32, still valid)
- Compliance: obligation → control mapping, gaps flagged (not yet specified)
- Finance: ledger model, billing, activity reflection, report producing, collateralisation proofs (redone as #34)
- Risk: how and whether we can model it (not yet specified)

Operations is not a BRD input; they come in during QA to review runbooks, tooling, decisions, and escalation paths.

**Production order.** The briefs follow the workflow dependencies:
1. Executive assessment (whether to proceed) — already done
2. Legal and Compliance (can we do it?) — can run in parallel
3. Finance (what's needed to keep the books in line) — may need input from Legal/Compliance
4. Risk (how and whether we can model it) — may need input from Finance, Legal, Compliance
5. Product: chase open questions, interface across teams, produce the BRD
6. BRD → Risk Committee review → PRD → phased buildout

The Risk Committee review is the gate, not individual brief approvals. The briefs are inputs to the BRD; the BRD is what the Risk Committee reads and approves or pushes back on.

**Evidence layer (underneath).** Claim cards, one claim each, quoted source, owning role. Reuse known formats: decision memo, ADR, RACI. Review is a queue of small cards per role, riskiest first, ~10 per session. Answers: agree / disagree / unsure / not my area + one line why. Later rounds show only changed claims. Extends the existing role review pages and question flow.

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
