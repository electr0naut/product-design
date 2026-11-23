# Gate 1 demand discovery policy specification

## Problem
A real product can enter analysis with only a demand hypothesis. Requiring initial market sizing before analysis forces invented numbers or prevents the research meant to test the hypothesis. For internal infrastructure, counterparty-demand evidence may be more relevant than commercial TAM, but it too may not exist at ideation.

## Scope
Change the human Gate 1 checklist so market sizing and verified counterparty demand are not default preconditions for ideation-to-analysis. Ask for a target audience and demand hypothesis in the canvas; direct analysts to investigate demand and document evidence or remaining unknowns, without adding a Gate 2 approval condition. Keep sponsor, analysis budget and the review-decision contract unchanged. Record the future option to make demand evidence a product-scoped policy switch, without implementing it now.

## Non-goals
- No automatic waiver or approval of any product gate.
- No change to review manifests, `check_gate.py`, generation scripts or later gates.
- No invented market figures, counterparty commitments or stakeholder decisions.
- No configuration switch in this slice; future design must define its owner, default, evidence contract and migration path before code changes.

## Invariants
- A checklist item is guidance, not a substitute for an authenticated, revision-bound stakeholder decision where a manifest exists.
- A completed idea canvas and an approved analysis budget are distinct facts.
- Missing market evidence must be marked unknown, not represented as validated demand.
- Existing reviewed product documents and review records are untouched.

## Acceptance criteria
- [ ] Gate 1's human checklist does not require initial market sizing or verified counterparty demand to enter analysis by default.
- [ ] The checklist still asks for a complete canvas, a named sponsor and an approved analysis budget; no approval is inferred from the policy change.
- [ ] The optional future switch is described as deferred, not advertised as an implemented configuration.
- [ ] `make check` passes, with no changed pipeline behavior.

## Test plan
- Unit tests: None; documentation-only policy wording.
- Integration/CLI tests: `make check` to catch unrelated regressions; inspect the Gate 1 checklist and existing review contract by hand.
- Fixtures or property tests: None.

## Rollout and rollback
Update the template checklist through a reviewed PR. Existing product clones keep their own checklist unless updated separately. Roll back the wording if a decision is made to require evidence at the ideation-to-analysis gate; do not silently retrofit a strict policy into existing manifests.
