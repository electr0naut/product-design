# FXL-4: evidence

Patch: `FXL-4.patch` (`git format-patch 0acbcbf..main` of the trusted repo; commits below).
```
e4aef93 Decode FIX candidates into ordered annotated fields
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 1 | 24 | 36949 | 5419 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 10 | 27953 | 3663 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 3 | 3225 | 5918 | 0.0041 |
| scribe | deepseek-flash | deepseek | 1 | 19 | 32411 | 12332 | 0.0147 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 30412 | 2857 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.6972**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 7; lint True; pass_to_pass True
- Mutation (stryker): killed 33, survived 3, timeout 0, no tests 2, unrun 0, 2.6 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/decode.js:5 `const beginString = message.fields.find(field => field.tag === 8)?.val` -> `message.fields.find(field => field.tag === 8).valu` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/decode.js:5 `const beginString = message.fields.find(field => field.tag === 8)?.val` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/decode.js:19 `? `Message ${message.number}: ${msgType?.enumName ?? msgType?.value ??` -> `msgType.enumName` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC6']

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 92] src/decode.js:15 On an enum field, a value that matches an inherited Object property name (`constructor`, `toString`, `valueOf`, `__proto__` and so on) isn't reported as `unknow

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `e4aef93e56`: **26/42** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 4 | 4 |  |
| acc-dictionary.test.js | 4 | 4 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 0 | 9 | module did not import (feature not built yet?) |

Newly passing: 4. No regressions.
