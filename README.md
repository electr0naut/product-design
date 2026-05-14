# Product Design Template

Clone this repository once for each new product. The repo is a structured
workspace for moving from an initial idea to team analysis, BRD, PRD, technical
design, and implementation scaffolding.

Each phase builds on the approved documents from earlier phases:

```text
01-ideation/          -> idea canvas
02-analysis/          -> legal, compliance, risk, ops, product, bizdev, finance
03-brd/               -> business requirements
04-prd/               -> product requirements
05-technical-design/  -> architecture, APIs, data models, integrations
06-implementation/    -> implementation scaffold and generated code
```

## Workflow

1. Copy `01-ideation/templates/idea-canvas.md` into `01-ideation/<product>.md`.
2. Edit the idea canvas until it reflects the product you want to explore.
3. Generate phase-02 analyses from the idea canvas.
4. Review and edit the generated analysis documents.
5. Generate the BRD from the idea canvas plus approved analyses.
6. Review and edit the BRD.
7. Generate the PRD from the approved BRD.
8. Review and edit the PRD.
9. Generate the technical design from the approved PRD.
10. Review and edit the technical design.
11. Generate the implementation scaffold from the approved technical design.

The scripts use the files in `shared/prompts/` and the templates in each phase
folder. By default they call `claude -p`. If the Claude CLI is not installed,
they write a `.prompt.md` file that can be pasted into another model.

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

# 3. Generate BRD from idea plus analyses
python shared/scripts/generate_brd.py \
  --idea 01-ideation/my-product.md \
  --analysis 02-analysis/

# 4. Generate PRD from approved BRD
python shared/scripts/generate_prd.py \
  --brd 03-brd/my-product-brd.md

# 5. Generate technical design from approved PRD
python shared/scripts/generate_technical_design.py \
  --prd 04-prd/my-product-prd.md

# 6. Generate implementation scaffold from approved technical design
python shared/scripts/scaffold_code.py \
  --technical-design 05-technical-design/architecture/my-product-technical-design.md
```

Use `--prompt-only` on any command to write the assembled prompt without calling
Claude:

```bash
python shared/scripts/generate_prd.py \
  --brd 03-brd/my-product-brd.md \
  --prompt-only
```

## Repository Roles

- `01-ideation/templates/` contains the first editable seed document.
- `02-analysis/templates/` contains role-specific review structures.
- `03-brd/templates/` and `04-prd/templates/` define the document formats used
  by the generation scripts.
- `05-technical-design/architecture/template.md` defines the architecture output.
- `shared/prompts/` contains the model instructions for each generation step.
- `shared/scripts/` contains orchestration scripts that assemble context and
  write the next phase.

## App Shell

The included Next.js app is a lightweight dashboard for browsing the template
workflow. It is not required for document generation.

```bash
npm run dev
npm run lint
npm run build
```
