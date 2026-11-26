# FXL-5: evidence

Patch: `FXL-5.patch` (`git format-patch e4aef93..main` of the trusted repo; commits below).
```
533f8ac Implement FIX session timeline and directional sequence gaps
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 1 | 19 | 44304 | 7323 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 10 | 28392 | 5874 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 1 | 4814 | 30405 | 0.0190 |
| scribe | deepseek-flash | deepseek | 1 | 36 | 47415 | 17486 | 0.0232 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 4 | 28814 | 3983 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.6368**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 21; lint True; pass_to_pass True
- Mutation (stryker): killed 168, survived 16, timeout 0, no tests 0, unrun 0, 8.1 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/timeline.js:8 `if (value === null || !/^\d+$/.test(value)) return null;` -> `value === null && !/^\d+$/.test(value)` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:8 `if (value === null || !/^\d+$/.test(value)) return null;` -> `false` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:8 `if (value === null || !/^\d+$/.test(value)) return null;` -> `/\d+$/` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:8 `if (value === null || !/^\d+$/.test(value)) return null;` -> `/^\d+/` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `false` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `type === 'A' || value(141) === 'Y'` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `type !== 'A'` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `""` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC15', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC14', 'AC2', 'AC6']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `value(141) !== 'Y'` ACs ['AC0', 'AC1', 'AC10', 'AC14', 'AC2', 'AC6']
- src/timeline.js:43 `if (type === 'A' && value(141) === 'Y' && expectedByDirection.has(dire` -> `""` ACs ['AC0', 'AC1', 'AC10', 'AC14', 'AC2', 'AC6']

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 65] src/timeline.js:38 The code treats a direction as seen only once it has a stored expected number. The design says it is seen once its first message has been processed. If that fir

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `533f8ac4eb`: **39/49** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 4 | 5 |  |
| acc-dictionary.test.js | 4 | 5 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 13 | 14 |  |

Newly passing: 13. No regressions.
