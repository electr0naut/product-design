# CLAUDE.md

## Project

Clone-per-product template for generating product lifecycle documents in order:
idea canvas, team analysis, BRD, PRD, technical design, and implementation
scaffold.

## Stack

- Markdown templates and prompts
- Python standard-library scripts in `shared/scripts/`
- Optional Claude CLI for document generation
- Lightweight Next.js dashboard in `src/app/`

## Commands

- Generate analyses: `python shared/scripts/generate_analysis.py --idea 01-ideation/<product>.md`
- Generate BRD: `python shared/scripts/generate_brd.py --idea 01-ideation/<product>.md --analysis 02-analysis/`
- Generate PRD: `python shared/scripts/generate_prd.py --brd 03-brd/<product>-brd.md`
- Generate technical design: `python shared/scripts/generate_technical_design.py --prd 04-prd/<product>-prd.md`
- Generate implementation scaffold: `python shared/scripts/scaffold_code.py --technical-design 05-technical-design/architecture/<product>-technical-design.md`
- Prompt only: add `--prompt-only` to any generation command
- Dev app: `npm run dev`
- Lint app: `npm run lint`
- Build app: `npm run build`

## Workflow Rules

- Treat earlier approved documents as the source of truth for later phases.
- Keep generated documents traceable to their inputs.
- Edit phase documents in order: `01` before `02`, `02` before `03`, and so on.
- Do not overwrite approved product documents without confirming intent.
- Keep reusable instructions in `shared/prompts/`, not in generated output files.
- Keep templates generic enough to clone for unrelated products.

## Directory Contract

- `01-ideation/` stores one or more product idea canvases.
- `02-analysis/<role>/` stores generated and reviewed analysis docs.
- `03-brd/` stores BRDs; `03-brd/approved/` may hold signed-off versions.
- `04-prd/` stores PRDs; `04-prd/approved/` may hold signed-off versions.
- `05-technical-design/` stores architecture, API, data model, and integration specs.
- `06-implementation/` stores generated implementation plans or scaffolded code.
