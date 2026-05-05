# Product Design Framework

End-to-end product lifecycle — from business idea inception through multi-team analysis, BRD/PRD creation, and Python implementation.

## Lifecycle Phases

```
01-ideation/          → Business idea capture, market analysis, value proposition
02-analysis/          → Multi-team review (legal, compliance, risk, ops, product, bizdev, finance)
03-brd/               → Business Requirements Documents
04-prd/               → Product Requirements Documents
05-technical-design/  → Architecture, API specs, data models, integrations
06-implementation/    → Python code, APIs, services, tests
```

## How to Use

### Phase 1: Ideation
1. Copy `01-ideation/templates/idea-canvas.md` to `01-ideation/<project-name>.md`
2. Fill in the business idea, target market, value proposition, revenue model
3. Run initial feasibility check

### Phase 2: Multi-Team Analysis
Each team reviews the idea through their lens:
- **Legal** — IP, licensing, regulatory, contracts
- **Compliance** — Industry regulations, data privacy (GDPR/CCPA), audit requirements
- **Risk** — Market risk, technical risk, operational risk, financial risk
- **Operations** — Infrastructure, staffing, SLAs, support model
- **Product** — User research, competitive analysis, feature prioritization
- **Business Development** — Partnerships, go-to-market, channel strategy
- **Finance** — Cost modeling, revenue projections, ROI analysis, funding

### Phase 3: BRD (Business Requirements Document)
Synthesize analysis into formal business requirements with stakeholder sign-off.

### Phase 4: PRD (Product Requirements Document)
Translate BRDs into product specs: user stories, acceptance criteria, wireframes, metrics.

### Phase 5: Technical Design
Architecture decisions, API specifications (OpenAPI), data models, external integrations.

### Phase 6: Implementation
Python codebase with FastAPI, database models, service layer, external API integrations, tests.

## Quick Start

```bash
# Start a new product
cp 01-ideation/templates/idea-canvas.md 01-ideation/my-product.md

# Generate analysis reports
python shared/scripts/generate_analysis.py --idea 01-ideation/my-product.md

# Generate BRD from analysis
python shared/scripts/generate_brd.py --analysis 02-analysis/

# Generate PRD from BRD
python shared/scripts/generate_prd.py --brd 03-brd/approved/<brd>.md

# Scaffold implementation from PRD
python shared/scripts/scaffold_code.py --prd 04-prd/approved/<prd>.md
```

## AI-Assisted Workflow

Each phase includes prompts in `shared/prompts/` for use with Claude Code:

```bash
claude -p "$(cat shared/prompts/ideation.md) $(cat 01-ideation/my-product.md)" --max-turns 10
claude -p "$(cat shared/prompts/legal-review.md) $(cat 01-ideation/my-product.md)" --max-turns 10
claude -p "$(cat shared/prompts/generate-brd.md) $(cat 02-analysis/)" --max-turns 15
```
