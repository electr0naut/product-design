# Phase Gate Checklist

This checklist is the human conversation guide. When a product has a
`review/<product>.json` manifest, the machine-checkable release condition is
`shared/scripts/check_gate.py` with recorded stakeholder decisions bound to the
reviewed revision. A ticked box, a generated document or green CI is not a
recorded approval; silence is not approval either.

## Gate 1: Ideation → Analysis
- [ ] Idea canvas completed with all sections
- [ ] Executive sponsor identified
- [ ] Budget for analysis phase approved

Discovery note (not a Gate 1 blocker): record the target audience and the demand
hypothesis in the canvas. Initial market sizing or verified counterparty demand
can be investigated during analysis; do not invent it to pass this gate. A future
product-scoped policy switch may require demand evidence before analysis, but no
such switch exists yet. This note does not waive the sponsor, budget or recorded
review-decision requirements.

## Gate 2: Analysis → BRD
- [ ] All 7 team analyses completed
- [ ] No critical blocking issues (or mitigations approved)
- [ ] Financial viability confirmed (or exception granted)
- [ ] Compliance path identified
- [ ] Risk matrix reviewed by leadership

## Gate 3: BRD → PRD
- [ ] BRD approved by all stakeholders
- [ ] Budget approved
- [ ] Timeline agreed
- [ ] Team allocation confirmed

## Gate 4: PRD → Technical Design
- [ ] PRD approved by product and engineering leads
- [ ] Every story in the story map traces to at least one BR
- [ ] Every BR is covered by a story or listed as a non-goal
- [ ] API requirements defined
- [ ] External integration requirements confirmed
- [ ] Non-functional requirements have specific targets

## Gate 5: Technical Design → Backlog
- [ ] Architecture reviewed and approved
- [ ] API spec reviewed
- [ ] Data models validated
- [ ] Security design approved
- [ ] Infrastructure costs estimated

## Gate 6: Backlog → Implementation
- [ ] `validate_backlog.py` reports no errors
- [ ] Every story reviewed by product and engineering (acceptance criteria, tasks, estimate)
- [ ] No XL stories left; oversized stories split in the PRD story map
- [ ] Open questions in Must stories resolved
- [ ] Development environment ready

## Gate 7: Implementation → Launch
- [ ] All must-have features implemented
- [ ] Unit test coverage > 80%
- [ ] Integration tests passing
- [ ] Security audit completed
- [ ] Performance benchmarks met
- [ ] Documentation complete
- [ ] Runbook created
- [ ] Monitoring and alerting configured
