# Technology and Security Decision Brief (Step 2, correction #3)

## Problem
The BRD lacks a technology and security feasibility assessment from CTO/engineering. Without this, the Risk Committee cannot evaluate build options, custody/keys, venue connectivity, security risks, or hard blockers before approving the BRD.

## Scope
- Add `generate_technology_security_brief.py --brd <path>` that reads only the named BRD, applies the existing `brd-to-prd` gate and provenance workflow, and writes `03-brd/technology-security/<product>.draft.md` by default. A supplied output must end in `.draft.md` and name the same product. Preserve common `--force`, `--draft`, `--prompt-only`, `--review-manifest`, and `--claude-bin` behavior.
- A short decision layer contains Build Options, Custody/Keys, Venue Connectivity, Security Risks, Hard Blockers, Main Uncertainty, and Decision Needed. Every non-Unknown/non-"none yet" line cites an evidence card `[C1]`. Exact-line BRD excerpts live in numbered Evidence Cards with Claim, Source and Quote. A technical term, security concept, or explicit blocker in the decision layer must occur exactly in a quoted line of at least one card cited on that line; a citation alone is not evidence of a technical claim. Do not infer security properties or build feasibility from vague statements. No arithmetic or inferred technical assessment is permitted.
- Unknown values are explicitly `Unknown.` and cannot be mixed with an assertion. "none yet" is also accepted without a card reference (for fields where no assessment has been made yet). A source quote match establishes provenance of the words, not semantic support for a claim such as a security property or build option. The prompt instructs the model to use `Unknown.` or `none yet` whenever the BRD does not support an interpretation; human CTO/engineering review remains mandatory. Re-read BRD bytes before writing, including after the generation receipt is computed.

## Non-goals
Security audits, penetration testing, architecture design, a technology review portal, other audiences, Atlassian sync or changing executive, finance, legal, or operations brief behavior.

## Invariants
- A configured input gate is authoritative unless explicitly bypassed with `--draft`; without a manifest the generated output remains draft. A fresh output's live review status is draft, but if the exact output path and bytes were already enrolled and approved, the shared status projection remains authoritative; the command never records an approval or equates input-gate readiness with output approval. This task will not overwrite reviewed product documents.
- Reject missing/extra sections, duplicate/dangling/unused cards, unsupported technical terms or blockers, incorrect sources or quotes, changed BRD, and approval claims before either document or sidecar is written. Preserve existing outputs without `--force`.
- Resolve the BRD and output through the existing `project_path` and `canonical_path` conventions; verify the named BRD's slug equals the output's canonical product identity. Let the common `generate` path perform symlink and collision checks for document, sidecar, prompt-only and fallback writes. Prompt-only writes only a prompt; a similarly named sibling BRD is never bundled. Review decisions remain owner-operated.

## Acceptance criteria
- [ ] A valid technology/security draft using one named BRD produces a `.draft.md` and provenance sidecar marked draft; no review record changes.
- [ ] An unsupported technical term or blocker, invalid card/source/quote, changed BRD or blocked gate fails without document or sidecar.
- [ ] Prompt-only and collision behavior match the executive, finance, and legal briefs; output paths cannot escape the product root or cross product identity.

## Test plan
- Unit/CLI tests with a realistic BRD line and fake model: valid draft, unsupported technical term, Unknown, "none yet", malformed citations, blocked manifest, source mutation, prompt-only isolation, output path/collision.
- Run `make check` and obtain independent review plus CodeRabbit before merge.

## Rollout and rollback
Additive script, prompt and template. No manifest migration or automatic Atlassian publication. Remove the new command/template to roll back without altering existing review state.
