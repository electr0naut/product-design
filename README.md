# Product Design Template

Clone this repository once for each new product. The repo is a structured
workspace for moving from an initial idea to team analysis, BRD, PRD, technical
design, a traceable user-story backlog, and an implementation plan.

Each phase builds on the reviewed documents from earlier phases. The scripts
support iterative draft-to-draft exploration; approval is a human workflow gate,
not a status check enforced by the CLI.

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

Generated documents are meant to be reviewed and edited, so the scripts never
overwrite an existing document. Pass `--force` to regenerate one.

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

# 3. Generate BRD from idea plus this product's analyses
python shared/scripts/generate_brd.py \
  --idea 01-ideation/my-product.md \
  --analysis 02-analysis/

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

# 7. Generate implementation scaffold from approved technical design
python shared/scripts/scaffold_code.py \
  --technical-design 05-technical-design/architecture/my-product-technical-design.md
```

Use `--prompt-only` on any generation command to write the assembled prompt
without calling Claude:

```bash
python shared/scripts/generate_prd.py \
  --brd 03-brd/my-product-brd.md \
  --prompt-only
```

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

## Engineering Checks

The repository includes a reproducible local quality gate for the Python pipeline and the Next.js overview:

```bash
uv sync
npm ci
make check
```

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
