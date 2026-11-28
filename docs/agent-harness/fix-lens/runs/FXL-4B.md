# FXL-4B: evidence

Patch: `FXL-4B.patch` (`git format-patch 533f8ac..main` of the trusted repo; commits below).
```
800b45f Guard FIX dictionary lookups against inherited keys
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 1 | 23 | 37044 | 3937 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 10 | 38137 | 3145 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 5 | 17261 | 8174 | 0.0077 |
| scribe | deepseek-flash | deepseek | 1 | 27 | 29975 | 14055 | 0.0164 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 6 | 29223 | 2261 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.3998**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 3; lint True; pass_to_pass True
- Mutation (stryker): killed 7, survived 0, timeout 0, no tests 0, unrun 0, 1.8 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
none

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
none

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': []}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `800b45f696`: **41/49** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 13 | 14 |  |

Newly passing: 2. No regressions.

Failing hidden tests, by name:

- `test/acc-analyse.test.js > <collection>` (error)
- `test/acc-limits.test.js > <collection>` (error)
- `test/acc-timeline.test.js > event keys` (fail)

## Implementer, finder and Codex use
- **Implementer: `gpt-6-sol` (openai-codex). No fallback.** Codex use: implementer 1 session, 23 calls, 37,044 in / 3,937 out; planner 1 session, 10 calls, 38,137 in / 3,145 out. No rate-limit or fallback line seen.
- **Finder: `deepseek-flash`**, one session.
- **Against the Qwen tickets:** gates passed first time, no fix pass, no findings; hidden suite 41/49 with `acc-decode` 5/5 and `acc-dictionary` 5/5 (the two new tests now pass), no regressions. The one other non-import failure, `acc-timeline > event keys`, is the test's own key-order mistake, fixed in the hidden suite after this run (FXL-5-test-fix-review.md).
