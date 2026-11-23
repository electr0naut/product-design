# Finance Decision Brief (Step 2, second slice)

## Problem
The executive memo cannot show a finance reviewer the spend being requested, the sourced assumptions behind a range, and what remains unknown without a full BRD read. A generated memo must not turn guessed amounts into approved budgets.

## Scope
- Add `generate_finance_brief.py --brd <path>` that reads only the named BRD, applies the existing `brd-to-prd` gate and provenance workflow, and writes `03-brd/finance/<product>.draft.md` by default. A supplied output must end in `.draft.md` and name the same product. Preserve common `--force`, `--draft`, `--prompt-only`, `--review-manifest`, and `--claude-bin` behavior.
- A short decision layer contains Ask, Spend Range, Assumptions, Funding Source, Main Uncertainty and Decision Needed. Every non-Unknown line cites an evidence card `[C1]`. Exact-line BRD excerpts live in numbered Evidence Cards with Claim, Source and Quote. A monetary amount or explicit numeric quantity (including its adjacent unit/currency) in the decision layer must occur exactly in a quoted line of at least one card cited on that line; a citation alone is not evidence of a number. Do not convert a source estimate into approved spend, or an annual figure into a monthly figure. No arithmetic or inferred range is permitted.
- Unknown values are explicitly `Unknown.` and cannot be mixed with an assertion. A source quote match and lexical number check establish provenance of the words, not semantic support for a claim such as a funding source, timeframe, or approval. The prompt instructs the model to use `Unknown.` whenever the BRD does not support an interpretation; human review remains mandatory. Re-read BRD bytes before writing, including after the generation receipt is computed.

## Non-goals
Estimating costs, deriving a range from multiple figures, currency conversion, budget approval, a finance review portal, other audiences, Atlassian sync or changing executive brief behavior.

## Invariants
- A configured input gate is authoritative unless explicitly bypassed with `--draft`; without a manifest the generated output remains draft. A fresh output's live review status is draft, but if the exact output path and bytes were already enrolled and approved, the shared status projection remains authoritative; the command never records an approval or equates input-gate readiness with output approval. This task will not overwrite reviewed product documents.
- Reject missing/extra sections, duplicate/dangling/unused cards, unsupported numeric literals, incorrect sources or quotes, changed BRD, and approval claims before either document or sidecar is written. Preserve existing outputs without `--force`.
- Resolve the BRD and output through the existing `project_path` and `canonical_path` conventions; verify the named BRD's slug equals the output's canonical product identity. Let the common `generate` path perform symlink and collision checks for document, sidecar, prompt-only and fallback writes. Prompt-only writes only a prompt; a similarly named sibling BRD is never bundled. Review decisions remain owner-operated.

## Acceptance criteria
- [ ] A valid finance draft using one named BRD produces a `.draft.md` and provenance sidecar marked draft; no review record changes.
- [ ] An unsupported number, invalid card/source/quote, changed BRD or blocked gate fails without document or sidecar.
- [ ] Prompt-only and collision behavior match the executive brief; output paths cannot escape the product root or cross product identity.

## Test plan
- Unit/CLI tests with a realistic BRD line and fake model: valid draft, unsupported amount, Unknown, malformed citations, blocked manifest, source mutation, prompt-only isolation, output path/collision.
- Run `make check` and obtain independent review plus CodeRabbit before merge.

## Rollout and rollback
Additive script, prompt and template. No manifest migration or automatic Atlassian publication. Remove the new command/template to roll back without altering existing review state.
