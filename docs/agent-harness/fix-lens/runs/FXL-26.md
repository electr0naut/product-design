# FXL-26: evidence

Patch: `FXL-26.patch` (`git format-patch f1dd618..572a089` of the trusted repo).
```
572a089 FXL-26 Resolve order links by message and round decimal halves away from zero
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 17 | 161918 | 7430 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 13 | 133476 | 7034 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 18 | 90588 | 99158 | 0.0775 |
| scribe | deepseek-flash | deepseek | 1 | 36 | 42343 | 19594 | 0.0240 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 66947 | 5354 | 0.0000 |

Claude on the review(s): **$0.5516**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/page.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 6; lint True; pass_to_pass True
- Mutation (stryker): killed 40, survived 4, timeout 0, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
- src/main.js:24 `const view = { orderId: null, orderMessage: null, filters: {}, page: 1` -> `{}` ACs ['AC3', 'AC4', 'AC5']
- src/render.js:29 `const decimal = /^(\d+)\.(\d{5,})$/.exec(Math.abs(value).toPrecision(1` -> `/(\d+)\.(\d{5,})$/` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/render.js:37 `return value < 0 ? -rounded : rounded;` -> `value <= 0` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/render.js:171 `button.addEventListener('click', () => handlers?.pick?.(id, number));` -> `handlers?.pick(id, number)` ACs ['AC0', 'AC1', 'AC3', 'AC4', 'AC5']
- Host copies the review read: commit `2a7550244286`, design sha256 `3163bb3260c2`

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
Hidden acceptance suite on trusted main `572a0895a7`: **277/277** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-delimiters.test.js | 14 | 14 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-events.test.js | 11 | 11 |  |
| acc-executions.test.js | 15 | 15 |  |
| acc-filters.test.js | 8 | 8 |  |
| acc-framing-rules.test.js | 11 | 11 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 4 | 4 |  |
| acc-order-story.test.js | 12 | 12 |  |
| acc-orders.test.js | 10 | 10 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-pager.test.js | 24 | 24 |  |
| acc-paging.test.js | 14 | 14 |  |
| acc-parties.test.js | 17 | 17 |  |
| acc-performance.test.js | 2 | 2 |  |
| acc-pick.test.js | 11 | 11 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-restart.test.js | 11 | 11 |  |
| acc-single-byte.test.js | 9 | 9 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-26 has landed:
- `acc-pick.test.js`: 11 of 11 pass, met

Host copies from commit `2a7550244286`: 25 hidden test files.

Retired on purpose (not counted): `test/acc-analyse.test.js > over a limit nothing is decoded`, `test/acc-check.test.js > bad tags`, `test/acc-limits.test.js > byte limit is UTF-8 and inclusive at 1,048,576`, `test/acc-limits.test.js > message limit: 1,000 accepted, 1,001 refused, warning names both numbers`, `test/acc-presentation.test.js > empty states and the size warning`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- none

Newly passing: 9. No regressions.
