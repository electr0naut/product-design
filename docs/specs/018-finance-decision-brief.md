# Finance Decision Brief (Step 2, revised)

## Problem
The finance decision brief must describe how to keep the books in line for a product: the ledger model, billing, how to reflect activity, report producing, and the proofs needed to show collateralisation to a regulator. The previous finance brief (#29) covered spending, which is not the finance team's role in this workflow. A generated memo must not turn guessed figures into approved accounting policy.

## Scope
- Replace `generate_finance_brief.py --brd <path>` to read only the named BRD, apply the existing `brd-to-prd` gate and provenance workflow, and write `03-brd/finance/<product>.draft.md` by default. A supplied output must end in `.draft.md` and name the same product. Preserve common `--force`, `--draft`, `--prompt-only`, `--review-manifest`, and `--claude-bin` behavior.
- A short decision layer contains Ledger Model, Billing, Activity Reflection, Report Producing, Collateralisation Proofs, Funding (liquidity, capital, funding cost), Main Uncertainty and Decision Needed. Every non-Unknown line cites an evidence card `[C1]`. Exact-line BRD excerpts live in numbered Evidence Cards with Claim, Source and Quote. A monetary amount, account name, or explicit numeric quantity (including its adjacent unit/currency) in the decision layer must occur exactly in a quoted line of at least one card cited on that line; a citation alone is not evidence of a number. Do not infer accounting treatment from a source estimate, or convert a source figure into a different accounting period. No arithmetic or inferred treatment is permitted.
- Unknown values are explicitly `Unknown.` and cannot be mixed with an assertion. A source quote match and lexical number check establish provenance of the words, not semantic support for a claim such as a ledger structure, billing cycle, or regulatory proof. The prompt instructs the model to use `Unknown.` whenever the BRD does not support an interpretation; human finance review remains mandatory. Re-read BRD bytes before writing, including after the generation receipt is computed.

## Non-goals
Estimating costs, deriving spend ranges, currency conversion, budget approval, spending requests, a finance review portal, other audiences, Atlassian sync or changing executive or legal brief behavior.

## Invariants
- A configured input gate is authoritative unless explicitly bypassed with `--draft`; without a manifest the generated output remains draft. A fresh output's live review status is draft, but if the exact output path and bytes were already enrolled and approved, the shared status projection remains authoritative; the command never records an approval or equates input-gate readiness with output approval. This task will not overwrite reviewed product documents.
- Reject missing/extra sections, duplicate/dangling/unused cards, unsupported numeric literals, incorrect sources or quotes, changed BRD, and approval claims before either document or sidecar is written. Preserve existing outputs without `--force`.
- Resolve the BRD and output through the existing `project_path` and `canonical_path` conventions; verify the named BRD's slug equals the output's canonical product identity. Let the common `generate` path perform symlink and collision checks for document, sidecar, prompt-only and fallback writes. Prompt-only writes only a prompt; a similarly named sibling BRD is never bundled. Review decisions remain owner-operated.

## Acceptance criteria
- [ ] A valid finance draft using one named BRD produces a `.draft.md` and provenance sidecar marked draft; no review record changes.
- [ ] An unsupported number, invalid card/source/quote, changed BRD or blocked gate fails without document or sidecar.
- [ ] Prompt-only and collision behavior match the executive and legal briefs; output paths cannot escape the product root or cross product identity.

## Test plan
- Unit/CLI tests with a realistic BRD line and fake model: valid draft, unsupported amount, Unknown, malformed citations, blocked manifest, source mutation, prompt-only isolation, output path/collision.
- Run `make check` and obtain independent review plus CodeRabbit before merge.

## Rollout and rollback
Replacement script, prompt and template. No manifest migration or automatic Atlassian publication. Remove the new command/template to roll back without altering existing review state.
