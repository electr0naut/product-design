# Executive Decision Brief (Step 2, first slice)

## Problem
A full BRD makes an executive hunt for the decision, alternatives, cost and evidence. A shorter generated brief must not masquerade as an approved decision or repeat unsupported claims.

## Scope
- Add a single-product `generate_executive_brief.py --brd <path>` CLI. It reads only the named BRD, reuses the existing `brd-to-prd` input gate and generation/provenance path, and defaults to `03-brd/executive/<product>.draft.md` (a visibly draft document). `--out` must also name a `.draft.md` file; `--force`, `--prompt-only`, `--review-manifest`, `--draft` and `--claude-bin` retain their existing meanings. A bypass is explicit; a configured, blocked gate cannot be silently skipped.
- The brief has a short decision layer: ask, recommendation, two or three options, cost/range, client evidence (who was asked, what they said, or "none yet"), main risk, deadline and cost of saying no. An evidence layer beneath it consists of numbered claim cards (`C1`, etc.), each with one claim, the BRD source path and a one-line verbatim quote. Decision-layer factual assertions reference cards using `[C1]`; unknown facts must be marked `Unknown`, not invented.
- Reject model output before writing either document or provenance unless required sections and card references are present, card IDs are unique, every referenced card exists, and every quoted excerpt occurs verbatim in the exact BRD bytes used for the prompt. A quote match establishes provenance of the excerpt, not the truth of an interpretation. Re-read and compare the BRD bytes before writing, even without a review manifest.
- The result is a draft for human review. It may later be copy-promoted and enrolled in a separate manifest lane through the existing workflow; this slice does not add a portal, alter the manifest, or record decisions.

## Non-goals
Other roles, a new approval gate, automatic approval, verified reviewer identity, cost calculations, parsing arbitrary prose citations, Atlassian, and story-provenance sidecars.

## Invariants
- A configured gate is authoritative for source approval; no manifest remains draft-only. `--draft` bypasses gate enforcement visibly but cannot write a canonical output.
- No generated output is approved by the input gate. Existing documents and sidecars are never overwritten without `--force`, and invalid model output cannot leave partial files.
- Source paths remain inside the product root, and a changed BRD or manifest fails closed. A prompt-only run writes only a prompt, not a decision brief or sidecar.

## Acceptance criteria
- [ ] A valid generated executive brief has the named sections, two or three options and cited cards with exact quotes from the selected BRD; its draft output and provenance sidecar are written, with no approval claim.
- [ ] A blocked manifest, invalid quote, missing/duplicate card, dangling card reference, missing required section, or changed BRD rejects the run without writing the document or sidecar.
- [ ] Existing files are preserved without `--force`; prompt-only and missing-model fallback retain their existing exit and file semantics. Inputs from a similarly named product are never bundled or cited.

## Test plan
- Unit tests: validate a realistic brief and reject bad sections, option count, cards, quotes and references; assert source bytes are rechecked.
- CLI integration: prompt-only and model-stub generation; blocked gate; path/collision handling; draft provenance and no sidecar on failure.
- Golden fixture: one concise realistic executive memo with verbatim BRD quote and card reference. Run `make check` and require independent PR review.

## Rollout and rollback
Additive CLI and prompt/template only; existing generators and manifests remain unchanged. Removing the new CLI/template leaves existing review state untouched. Generated drafts are ordinary files and can be retained for audit or removed by the owner.
