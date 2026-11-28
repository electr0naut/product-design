# FXL-2: evidence

Patch: `FXL-2.patch` (`git format-patch 8057bbf..main` of the trusted repo; commits below).
```
f36221c FXL-2: fix tests to properly validate checkMessage
40c10b6 FXL-2: detect malformed messages with checkMessage
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | qwen3.7-plus | alibaba-token-plan | 2 | 74 | 274513 | 52116 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 1 | 10854 | 5 | 0.0000 |
| planner | qwen3.7-plus | alibaba-token-plan | 1 | 12 | 96435 | 14822 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 2 | 3 | 12776 | 38034 | 0.0248 |
| reviewer | qwen3.7-plus | None | 1 | 0 | 0 | 0 | 0.0000 |
| reviewer | qwen3.7-plus | alibaba-token-plan | 2 | 4 | 54247 | 62816 | 0.0000 |
| scribe | deepseek-flash | deepseek | 1 | 35 | 44877 | 16635 | 0.0222 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 25 | 136129 | 12989 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.6898**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 12; lint True; pass_to_pass True
- Mutation (stryker): killed 90, survived 58, timeout 3, no tests 53, unrun 0, 6.8 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/framing.js:169 `while (cursor < text.length) {` -> `cursor <= text.length` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:174 `if (fieldEnd < text.length) {` -> `true` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:174 `if (fieldEnd < text.length) {` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:174 `if (fieldEnd < text.length) {` -> `fieldEnd <= text.length` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:174 `if (fieldEnd < text.length) {` -> `fieldEnd >= text.length` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:174 `if (fieldEnd < text.length) {` -> `{}` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `sep === "\n" && sep === "\r"` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `""` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']
- src/framing.js:176 `if (sep === "\n" || sep === "\r") break;` -> `""` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6']

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 72] src/framing.js:169 The raw-field re-parse in checkMessage (the `while (cursor < text.length)` loop plus the rule 1/rule 2 loops over `rawFields`) runs to the end of the line/text 
- F2 [medium, conf 55] src/framing.js:281 The missing_checksum position is derived from `lastFieldEnd + 1`, which is the 1-based position of the last field's trailing delimiter when one is present, and 

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2']}

## Fix pass
pass 1 (gates)
