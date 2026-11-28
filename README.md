# Product Design Template

Clone this repository once for each new product. The repo is a structured
workspace for moving from an initial idea to team analysis, BRD, PRD, technical
design, a traceable user-story backlog, and an implementation plan.

Each phase builds on the reviewed documents from earlier phases. The scripts
support iterative draft-to-draft exploration. A phase gate is only released by
recorded decisions from the required stakeholders for the exact document bytes
they reviewed (see [Stakeholder Review Gates](#stakeholder-review-gates));
passing CI or a generated document is never approval.

```text
01-ideation/          -> idea canvas
02-analysis/          -> legal, compliance, risk, ops, product, bizdev, finance
03-brd/               -> business requirements (BR-xxx, NFR-xxx)
04-prd/               -> product requirements and the epic/story map
05-technical-design/  -> architecture, APIs, data models, integrations
06-backlog/           -> one file per user story, plus a traceability report
07-implementation/    -> implementation plan
```

## Workflow

1. Copy `01-ideation/templates/idea-canvas.md` into `01-ideation/<product>.md`.
2. Edit the idea canvas until it reflects the product you want to explore.
3. Generate phase-02 analyses from the idea canvas.
4. Review and edit the generated analysis documents.
5. Generate the BRD from the idea canvas plus reviewed analyses.
6. Review and edit the BRD.
7. Generate the PRD, including its epic and story map, from the reviewed BRD.
8. Review and edit the PRD.
9. Generate the technical design from the reviewed PRD.
10. Review and edit the technical design.
11. Generate user stories, one epic at a time, from the reviewed PRD and
    technical design.
12. Review and edit the stories, then check traceability and fix any errors.
13. Generate the implementation plan from the reviewed technical design.

The scripts use the files in `shared/prompts/` and the templates in each phase
folder. By default they call `claude -p`. If the Claude CLI is not installed,
they write a `.prompt.md` file that can be pasted into another model.

Generated documents and `.prompt.md` prompts are meant to be reviewed and edited,
so the scripts never overwrite an existing file without `--force`. If Claude is
unavailable, a fallback prompt is written and the command exits 1; if that
prompt already exists, it is preserved (use `--force` to replace it). A
`--prompt-only` collision is skipped with exit 0 unless forced. An invalid
story response never overwrites an existing saved `.response.md` without
`--force` either.

Output paths (including explicit `--out`, `--out-dir`, and `--report` paths) reject
symlinked files or directory components and parent traversal (`..`). The
system-level `/tmp` and `/var` aliases are accepted for Linux/macOS, but
symlinks below them are not. Use real directories for external outputs; no
write or story deletion is permitted through a symlinked product path. This is
not a sandbox against concurrent filesystem mutation by another process.

## Commands

```bash
# 1. Start a new product
cp 01-ideation/templates/idea-canvas.md 01-ideation/my-product.md

# 2. Generate all team analyses
python shared/scripts/generate_analysis.py \
  --idea 01-ideation/my-product.md

# Generate one analysis only
python shared/scripts/generate_analysis.py \
  --idea 01-ideation/my-product.md \
  --role legal

# 3. Generate BRD from idea plus all seven exact analyses for this product
python shared/scripts/generate_brd.py \
  --idea 01-ideation/my-product.md \
  --analysis 02-analysis/
# For exploratory work with at least one exact analysis, add --allow-partial-analysis
# Duplicate exact analysis filenames under different directories are rejected.

# 4. Generate PRD from approved BRD
python shared/scripts/generate_prd.py \
  --brd 03-brd/my-product-brd.md

# 5. Generate technical design from approved PRD
python shared/scripts/generate_technical_design.py \
  --prd 04-prd/my-product-prd.md

# 6. Generate user stories for every epic (or one: --epic E02)
python shared/scripts/generate_stories.py \
  --prd 04-prd/my-product-prd.md \
  --technical-design 05-technical-design/architecture/my-product-technical-design.md

# Check the backlog against the BRD and PRD
python shared/scripts/validate_backlog.py \
  --brd 03-brd/my-product-brd.md \
  --prd 04-prd/my-product-prd.md

# 7. Generate an implementation plan from approved technical design
python shared/scripts/scaffold_code.py \
  --technical-design 05-technical-design/architecture/my-product-technical-design.md
```

For an executive-facing decision brief, use the named BRD as the only content
source. This is a separate, optional draft—not an approval or a replacement for
the BRD/PRD. The output lands in `03-brd/executive/my-product.draft.md` with a
provenance sidecar; `--out` must also end in `.draft.md`. The existing
`brd-to-prd` input gate applies when a review manifest exists, unless `--draft`
explicitly bypasses it. Source quotes in the evidence cards are checked before
writing, but the executive must still review the interpretation and decision.

```bash
python shared/scripts/generate_executive_brief.py \
  --brd 03-brd/my-product-brd.md
# To inspect the assembled prompt without generating, add --prompt-only.
```

A valid generated brief exits 0; an existing output is skipped with exit 0
unless `--force` is supplied. A blocked gate, invalid model output or unsafe
path exits nonzero without writing the brief or sidecar. A missing Claude CLI
writes a fallback `.prompt.md` and exits 1. Copy promotion never approves the
brief; a human review decision remains necessary.

Split the PRD once epics exist, so an approval or edit of E02 does not stale
E01:

```bash
python shared/scripts/split_prd.py --prd 04-prd/my-product-prd.md
# 04-prd/my-product/{core.md,epics/E01.md,epics/E02.md}
python shared/scripts/generate_stories.py \
  --prd 04-prd/my-product --epic E01 \
  --technical-design 05-technical-design/architecture/my-product-technical-design.md
```

The split files become the reviewed artifacts; the monolithic file is a draft
kept for regeneration.

Use `--prompt-only` on any generation command to write the assembled prompt
without calling Claude:

```bash
python shared/scripts/generate_prd.py \
  --brd 03-brd/my-product-brd.md \
  --prompt-only
```

## Stakeholder Review Gates

Reviews are configured per product in `review/<product>.json`, where
`<product>` is the slug used by the phase documents. The manifest is plain JSON:
it is the contract a future role-based portal can read and write through an
audited service, and the checker refuses ambiguous or partial records.
The current schema is v2; a v1 manifest is refused with a pointer to
`shared/scripts/migrate_manifest.py`.

- `gates[].id` names a transition such as `design-to-backlog`.
- `gates[].lanes` splits a gate into swimlanes (usually epics, or an analysis
  domain). Each lane has its own `roles`, `artifacts`, `depends_on` and
  `assumptions`. A blocked lane blocks only its descendants; unrelated lanes
  keep advancing.
- `lanes[].epic: true` marks a swimlane as epic-scoped. Lanes without it are
  cross-cutting (for example `security`) and are always checked, including
  runs that use `--epic`.
- `decisions` record `approve`, `request_changes`, `not_applicable` or
  `cannot_determine`, plus reviewer, role, time, evidence reference, the
  SHA-256 of every reviewed artifact and, optionally, the `source_commit` the
  reviewer saw. Only `approve` with matching hashes and no unresolved feedback
  releases a lane. The latest decision wins; an older approval cannot hide a
  later objection. Decisions must be in time order per role.
- `feedback` entries on a decision are immutable. `feedback_events` record
  `resolve` or `reopen` with a written reason, author, time and evidence; the
  latest event decides the status. Changes follow the same event model through
  `change_events`.
- `questions` record open questions with `Q-001` IDs, a gate/lane, the role that
  must answer, the source artifact and heading, and a raise time.
  `question_answers` are append-only. An unanswered question blocks its lane;
  an answer still requires a newer decision from that role, because an answer
  is evidence, not approval.
- `assumptions` carry a source and `review_by` date; expired ones block the
  lanes that reference them.
- `changes` record a source (for example a regulation, vendor decision or
  priority shift) and affected gate/lane scopes; `change_events` resolve or
  reopen them. An open change blocks its scopes; a resolved change requires a
  newer approval from every required role in those scopes. Only declared scopes
  are invalidated. Split a shared PRD with `split_prd.py` for true per-epic
  invalidation; the technical design is still shared, so editing it stales every
  lane that reviews it.

Check readiness before generating the next phase:

```bash
python shared/scripts/check_gate.py \
  --manifest review/my-product.json \
  --gate design-to-backlog
# One swimlane only:
python shared/scripts/check_gate.py \
  --manifest review/my-product.json \
  --gate design-to-backlog --lane E02
# Machine-readable output, including pending roles and feedback, for a portal:
python shared/scripts/check_gate.py \
  --manifest review/my-product.json \
  --gate design-to-backlog --json
# Live status for one existing artifact, with underlying gate/lane reasons:
python shared/scripts/check_gate.py \
  --manifest review/my-product.json \
  --artifact 04-prd/my-product/epics/E01.md --json
```

`--artifact` is read-only. It reports `draft` for an unenrolled artifact,
`in_review` for outstanding decisions, `on_hold` for active blockers,
`needs_reapproval` after a previously complete approval goes stale, and
`approved` only when every applicable lane is ready for the current bytes.
Assumptions due within seven calendar days appear under `warnings` without
changing readiness; use `--warning-days N` to change the lead time and
`--today YYYY-MM-DD` for reproducible reports. An artifact check exits 0 only
for `approved`, 1 for any other state, and 2 for invalid input. This is the
status of the artifact itself, not a claim that an output was approved when
its generating command's *input* gate passed. No decisions are written.

Exit status is `0` when every selected lane is ready, `1` when blocked and `2`
for an invalid manifest. The generation scripts enforce the gate for their
transition when `review/<product>.json` exists for the output product (falling
back to the input product), or when `--review-manifest` is given (it must name
the product being generated). An output product with its own manifest must pass
that manifest, even if the input product is approved. Whole-document generation
requires every lane, including cross-cutting lanes such as `security`;
`generate_stories.py --epic E01` checks that swimlane plus cross-cutting lanes.
They refuse to proceed if an input is not covered by the
reviewed artifacts, including when a reviewed input is copied or renamed, and a
partial BRD input cannot claim gate release. Use `--draft` for exploratory
output; it is labelled only on stderr and is never reported as approved. With
no manifest at all, generation stays draft-only and says so.

`--draft` also routes the write to a visibly draft path: a single document goes
to `name.draft.md` and a multi-file product (split PRD, story backlog) goes to
`<product>.draft/`. A canonical `--out` is refused, because exploring must never
overwrite reviewed words; the canonical default path is suffixed instead. Draft
output needs no manifest, and its provenance sidecar records `draft`.

Promotion is a separate, explicit copy:

```bash
python shared/scripts/promote.py 04-prd/my-product.draft.md
python shared/scripts/promote.py 06-backlog/my-product.draft --force
```

It refuses to overwrite an existing canonical file unless `--force` is given,
copies the bytes and the sidecar unchanged apart from the recorded path, and
never writes a review record or an approval. The promoted file still needs a
recorded decision before any gate counting it is released.

Record a decision from a review packet — the packet is untrusted, so the
recorder re-hashes the artifacts and assigns IDs:

```bash
python shared/scripts/record_decision.py \
  --manifest review/my-product.json \
  --packet review-inbox/acme-E02-legal.json \
  --evidence slack:C123/456
```

The recorder refuses a stale approval outright; a stale change request needs
`--accept-stale`. `--verify` performs every check without writing.

### Role review pages

`npm run build && npm run review` serves local pages under `/review`, one queue
per product and role. A decision page shows the artifacts and their hashes, what
blocks the lane, the other required roles, open questions for that role, and a
form that builds a decision packet. The packet is downloaded or copied; it is not
submitted. The maintainer records it with `record_decision.py`.

The pages are deliberately unauthenticated, so they bind to loopback and reject
any other `Host` header. They are a convenience for people already trusted with
the material; they are not access control. Do not expose them through a public
URL. The AI help button answers one open question from that question's cited
section, marks unverified quotes, and never submits or records anything; it is
disabled unless `REVIEW_ASSIST_ENABLED=1` and the `claude` CLI is available.

Approvals bind document hashes, not identity. Recording and validating a
decision is a local, auditable trail; it is not SSO, access control or a formal
legal signature. Before a portal is built, export only the material each role
needs, decide where confidential analyses may be processed, and authenticate
reviewers. `review/EXAMPLE.json` is an inert template, not a configured review.

Generated documents also get a `<document>.provenance.json` sidecar with the
repository-relative input paths and their hashes, the prompt and template
hashes, the assembled prompt hash, the document hash and generation time. The
CLI cannot confirm which model answered,
so it records `model: null` rather than guessing. Provenance proves what was
consumed, not that a claim is true or approved. Legal and compliance prompts
require verifiable citations, applicability assumptions and explicit
uncertainty.

The sidecar also carries a historical review snapshot: `output_review_status`
holds the projected status for the written bytes, the `evaluated_at` date, the
review manifest's path and SHA-256 when one was used, and any non-blocking
assumption warnings; `input_gate_readiness` separately records the input gate,
its lanes, the decision IDs and each lane's policy hash. A ready input gate is
not output approval: a freshly generated document starts as `draft`, or as
`in_review` once its lane is enrolled, and is reported `approved` only when the
identical bytes already carry a complete approval. The snapshot is never
re-read as a live certificate — use `check_gate.py --artifact` (or the portal)
to recompute status from the manifest. A manifest or document changed after
generation does not refresh its own sidecar.

## User Story Backlog

The PRD defines the work split: epics (`### E01: Name`) and a story map table
with one row per story (`US-001`), its persona, priority, and the BRD
requirements it traces to. Acceptance criteria are not written in the PRD.

After the technical design is approved, `generate_stories.py` expands each epic
in its own Claude call, with the PRD and technical design as context. Each
story gets its own file, so it can be reviewed, assigned and implemented on its
own:

```text
06-backlog/my-product/
  E01-account-setup/
    US-001-sign-up-with-email.md
    US-002-verify-email-address.md
  E02-billing/
    US-003-pay-an-invoice-by-card.md
  traceability.md
```

Each story file starts with frontmatter that scripts read, followed by the
story, Given/When/Then acceptance criteria, technical notes, tasks and open
questions (see `06-backlog/templates/story-template.md`):

```yaml
---
id: US-003
title: Pay an invoice by card
epic: E02
traces_to: [BR-004, NFR-002]
depends_on: [US-001]
components: [billing-service, invoices-table]
priority: Must
estimate: M
status: Draft
---
```

Without the Claude CLI, run `generate_stories.py --prompt-only --epic E01`,
paste the prompt into another model, save its answer, and split it into story
files with `--epic E01 --response <saved answer>`.

The response marker and each story file's frontmatter `id` must use the exact
canonical form `US-001` (three digits), and the filename must be `US-001.md`
or `US-001-<title>.md` with the same ID. Frontmatter `epic` must be exact
`E01` (two digits). The importer rejects noncanonical identities before any
story files change; the validator also treats noncanonical frontmatter as an
error. PRD story-map parsing still accepts alternate ID spelling but produces
canonical IDs for imports. `--force` is required to replace an existing
`.prompt.md`, including saved epic prompts.

`validate_backlog.py` checks the backlog and writes
`06-backlog/<product>/traceability.md` with a requirement coverage matrix and a
build order that puts dependencies first, then priority. It exits with an error
when:

- a story traces to a requirement that is not in the BRD, or traces to nothing
- a BRD requirement (BR-xxx) has no story and is not a PRD non-goal
- a story depends on an unknown story, or dependencies form a cycle
- two stories share an ID

It warns about stories without acceptance criteria or tasks, XL or missing
estimates, Must stories that depend on lower-priority ones, and stories that are
out of sync with the PRD story map. Add `--strict` to fail on warnings too.

On success it writes `backlog.lock.json` with the BRD, PRD (or each split PRD
file) and story hashes. `scaffold_code.py` refuses to build an implementation
plan unless the lock matches the working tree and the
`backlog-to-implementation` review gate is ready; `--draft` bypasses the gate but
never the lock. A failed validation never writes a lock.

For reviewers, `review_pack.py --manifest review/<product>.json --role legal`
writes a Markdown pack listing the pending decision, artifact hashes, stale
roles, open questions, changes and assumptions. `check_gate.py --all --json
--today YYYY-MM-DD` reports every product, gate and lane, including stale
approvals in gates you were not checking.

## Repository Roles

- `01-ideation/templates/` contains the first editable seed document.
- `02-analysis/templates/` contains role-specific review structures.
- `03-brd/templates/` and `04-prd/templates/` define the document formats used
  by the generation scripts.
- `05-technical-design/architecture/template.md` defines the architecture output.
- `06-backlog/templates/story-template.md` defines the user story format.
- `shared/prompts/` contains the model instructions for each generation step.
- `shared/scripts/` contains orchestration scripts that assemble context and
  write the next phase. `backlog.py` holds the story map, story file and
  traceability logic; its tests run with
  `python -m unittest discover shared/scripts/tests`.

## Linux and macOS Setup

The committed CI gate runs on Ubuntu. A Linux/macOS checkout requires Git, GNU
Make, Node.js 22+, npm, and `uv`; Python 3.11 is managed from `uv.lock`.

```bash
bash scripts/bootstrap.sh
```

The bootstrap script installs the locked Python environment, performs a clean npm
install, and runs `make check`. It does not require `sudo` and never installs
system packages.

## Engineering Checks

The repository includes a reproducible local quality gate for the Python pipeline and the Next.js overview:

```bash
uv sync
npm ci
make check
```

Mutation testing is advisory and scoped to the review-gate and backlog parsers;
it is not part of `make check`:

```bash
make mutate
```

See `docs/plans/mutation-testing-2026-11-21.md` for the last scores and the
survivor triage.

See `AGENTS.md` for portable coding-agent instructions and `ENGINEERING.md` for the
full change, testing, specification and AI-review rules. Use
`docs/specs/TEMPLATE.md` for behaviour-changing work.

## App Shell

The included Next.js app is a static workflow overview. It is not required for
document generation and does not browse or execute repository artefacts.

```bash
npm run dev
npm run lint
npm run build
```
