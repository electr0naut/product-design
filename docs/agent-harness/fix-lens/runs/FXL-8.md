# FXL-8: evidence

Patch: `FXL-8.patch` (`git format-patch 8db74fc..main` of the trusted repo; commits below).
```
e721f31 test: cover reproducible JS dictionary build as new AC2 test
7768c0f Render full FIX timeline and use CSP-compatible dictionary modules
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 3 | 44 | 85052 | 11297 | 0.0000 |
| implementer | gpt-6.2-sol | openai-codex | 1 | 1 | 10183 | 5 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 12 | 30109 | 4906 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 1 | 10183 | 5 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 5 | 14317 | 68760 | 0.0437 |
| scribe | deepseek-flash | deepseek | 1 | 59 | 63030 | 33659 | 0.0413 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 6 | 29207 | 3776 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.6450**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/dictionary.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 9; lint True; pass_to_pass True
- Mutation (None): killed None, survived None, timeout None, no tests None, unrun None, None s; incomplete: None; warning: None; error: stryker wrote no report (exit 1): Item.execute (file:///srv/lab/agent-harness/deps/fix-lens/node_modules/@stryker-mutator/core/dist/src/concurrent/pool.js:34:28)
    at async file:///srv/lab/agent-harness/deps/fix-lens/node_modules/@stryker-mutator/core/dist/src/concurrent/pool.js:71:13 {
  innerError: undefined
}

Node.js v26.12.1

- Survivors (up to 12):
none

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 88] test/static-checks.test.js:15 The new check only catches a dynamic JSON import when `)` comes straight after the path string. A dynamic import with a second options argument is missed. That 

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1']}

## Fix pass
pass 1 (gates)

## Hidden acceptance suite
Hidden acceptance suite on trusted main `e721f31862`: **59/59** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 3 | 3 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-render.test.js | 5 | 5 |  |
| acc-timeline.test.js | 14 | 14 |  |

Newly passing: 6. No regressions.

Failing hidden tests, by name:

- none

## Implementer, finder and Codex use
- **Implementer: `gpt-6-sol` (openai-codex), first pass and gate fix pass. No fallback seen.** The table's `gpt-6.2-sol` rows (1 implementer, 1 planner call) are **my verification calls** after the model switch; the ticket did not run on it. Codex use for the ticket: implementer 3 sessions, 44 calls, 85,052 in / 11,297 out; planner 1 session, 12 calls, 30,109 in / 4,906 out. The 3 implementer sessions include sessions from my earlier tiny checks if any fell in the ticket's window; I did not separate them.
- **Finder: `deepseek-flash`**, one session.
- **Against the Qwen tickets:** first-attempt gates failed (AC2); one gate fix pass; one person-approved test edit; one review block for a harness config gap (fixed by D18); nothing blocking in review (note F1); hidden suite 59/59, no regressions. Mutation gave no result (`stryker wrote no report`), to be looked at in D19. Accepted in a real browser (FXL-8-landed-review).
