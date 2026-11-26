# FXL-6: evidence

Patch: `FXL-6.patch` (`git format-patch 800b45f..main` of the trusted repo; commits below).
```
d8a2477 Add standalone FIX paste size limits
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 1 | 18 | 34188 | 3461 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 13 | 38349 | 3188 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 6 | 44128 | 6348 | 0.0107 |
| scribe | deepseek-flash | deepseek | 1 | 21 | 30937 | 10083 | 0.0132 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 9 | 31982 | 2858 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.2436**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 8; lint True; pass_to_pass True
- Mutation (stryker): killed 12, survived 0, timeout 0, no tests 0, unrun 0, 1.8 s; incomplete: False; warning: None; error: None
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
Hidden acceptance suite on trusted main `d8a2477cea`: **45/49** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 3 | 3 |  |
| acc-timeline.test.js | 14 | 14 |  |

Newly passing: 4. No regressions.

Failing hidden tests, by name:

- `test/acc-analyse.test.js > <collection>` (error)
