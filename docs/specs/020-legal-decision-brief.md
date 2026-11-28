# Legal Decision Brief (Step 2, third slice)

## Problem
A legal reviewer cannot see which claims the draft relies on, which BRD lines support them, or what jurisdiction each claim invokes, without re-reading the whole BRD. A generated memo must not turn a quoted claim into a legal conclusion.

## Scope
Add `generate_legal_brief.py --brd <path>` that reads only the named BRD, applies the existing `brd-to-prd` gate and provenance workflow, and writes `03-brd/legal/<product>.draft.md` by default. A supplied output must end in `.draft.md` and name the same product. Preserve common `--force`, `--draft`, `--prompt-only`, `--review-manifest`, and `--claude-bin` behavior.

A short decision layer contains Claim Relied On, Citation, Jurisdiction, Main Legal Risk, and Decision Needed. Every non-Unknown line cites an evidence card `[C1]`. Exact-line BRD excerpts live in numbered Evidence Cards with Claim, Source and Quote. A jurisdiction or citation in the decision layer must occur exactly in a quoted line of at least one card cited on that line; a citation alone is not evidence of a legal conclusion. No jurisdiction inference, no legal conclusion, no approval. Unknown values are explicitly `Unknown.` and cannot be mixed with an assertion. The prompt instructs the model to use `Unknown.` whenever the BRD does not support an interpretation; human legal review remains mandatory. Re-read BRD bytes before writing, including after the generation receipt is computed.

## Non-goals
Legal advice, jurisdiction inference, citation conversion, budget approval, a legal review portal, other audiences, Atlassian sync or changing executive or finance brief behavior.

## Invariants
- A configured input gate is authoritative unless explicitly bypassed with `--draft`; without a manifest the generated output remains draft. A fresh output's live review status is draft, but if the exact output path and bytes were already enrolled and approved, the shared status projection remains authoritative; the command never records an approval or equates input-gate readiness with output approval. This task will not overwrite reviewed product documents.
- Reject missing/extra sections, duplicate/dangling/unused cards, unsupported citations or jurisdictions, incorrect sources or quotes, changed BRD, and approval claims before either document or sidecar is written. Preserve existing outputs without `--force`.
- Resolve the BRD and output through the existing `project_path` and `canonical_path` conventions; verify the named BRD's slug equals the output's canonical product identity. Let the common `generate` path perform symlink and collision checks for document, sidecar, prompt-only and fallback writes. Prompt-only writes only a prompt; a similarly named sibling BRD is never bundled. Review decisions remain owner-operated.

## Acceptance criteria
- [ ] A valid legal draft using one named BRD produces a `.draft.md` and provenance sidecar marked draft; no review record changes.
- [ ] An unsupported citation or jurisdiction, invalid card/source/quote, changed BRD or blocked gate fails without document or sidecar.
- [ ] Prompt-only and collision behavior match the executive and finance briefs; output paths cannot escape the product root or cross product identity.

## Test plan
- Unit/CLI tests with a realistic BRD line and fake model: valid draft, unsupported citation, unsupported jurisdiction, Unknown, malformed citations, blocked manifest, source mutation, prompt-only isolation, output path/collision.
- Run `make check` and obtain independent review plus CodeRabbit before merge.

## Rollout and rollback
Additive script, prompt and template. No manifest migration or automatic Atlassian publication. Remove the new command/template to roll back without altering existing review state.
