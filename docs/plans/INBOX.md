# Inbox

Queued requests for the scaffold work. Read this file only between tasks, never
in the middle of one. When an item is handled, move it to the "Done" section of
`docs/plans/STATUS.md` with the commit that handled it, and remove it here.

## Queue

- Owner review of PR #35 workflow corrections (smallest change that works, one spec plus small PRs):
  1. Operations IS a BRD input again. PR #35 says it is not, but 02-analysis already has an operations analysis and generate_brd.py requires all seven analyses, so the plan contradicts the code. Keep the operations analysis as a BRD input, focused on operability: manual steps, cut-offs, volumes, staffing, failure modes. Keep the QA-stage runbook review as well. Fix next-phase.md and STATUS.md to match.
  2. Client evidence before the BRD: add a short "design partners / client evidence" section to the idea canvas and executive brief (who was asked, what they said, or "none yet"). A field, not a new gate.
  3. Technology and security feasibility in phase 2: a short brief from CTO/engineering (build options, custody/keys, venue connectivity, security risks, hard blockers) as a BRD input. Reuse the existing brief pattern; do not add a new framework.
  4. Funding in the finance brief: one section on liquidity, capital and funding cost of the product. No new role.
  5. After go-live: add success metrics and kill criteria to the BRD template, and a post-launch review step at 30-90 days in the workflow doc. Documentation only, no new code.
  6. Change control: no code change. State in the workflow doc that a change after BRD approval goes through the existing manifest change/reapproval flow.
  7. Prioritisation across products: out of scope for a clone-per-product template. One line in the workflow doc saying so.
  
  Same working rules: spec in docs/specs/ first, make check green, wait for CodeRabbit, plain-English summary in STATUS.md, Model trailer. Stop and ask if any change would weaken a gate. Handle after current task, before starting Compliance and Risk briefs.
