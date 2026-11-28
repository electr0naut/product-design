# FXL-21: evidence

Patch: `FXL-21.patch` (`git format-patch d75fb74..e23113c` of the trusted repo).
```
e23113c FXL-21: Keep timeline and cards in step with page controls
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| bk-sp-max | qwen4-max | alibaba-token-plan | 5 | 5 | 694 | 6680 | 0.0000 |
| bk-sp-plus | qwen3.7-plus | alibaba-token-plan | 8 | 8 | 194031 | 62311 | 0.0000 |
| implementer | gpt-6.2-sol | openai-codex | 1 | 20 | 196533 | 10938 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 14 | 132797 | 6983 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 5 | 20479 | 6257 | 0.0070 |
| scribe | deepseek-flash | deepseek | 1 | 32 | 38757 | 19821 | 0.0226 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 7 | 66403 | 4441 | 0.0000 |

Claude on the review(s): **$1.4429**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/page.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 20; lint True; pass_to_pass True
- Mutation (stryker): killed 74, survived 5, timeout 0, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
- src/main.js:24 `const view = { orderId: null, filters: {}, page: 1 };` -> `{}` ACs ['AC11', 'AC12']
- src/main.js:49 `if (typeof results?.scrollIntoView === 'function') results.scrollIntoV` -> `results.scrollIntoView` ACs ['AC11', 'AC12']
- src/render.js:112 `button.addEventListener('click', () => handlers?.setPage?.(destination` -> `handlers?.setPage(destination)` ACs ['AC11', 'AC12', 'AC5']
- src/render.js:112 `button.addEventListener('click', () => handlers?.setPage?.(destination` -> `handlers.setPage` ACs ['AC11', 'AC12', 'AC5']
- src/render.js:288 `const pageNumbers = new Set(info.items.filter(entry => entry.message).` -> `info.items` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- Host copies the review read: commit `b50786bfd690`, design sha256 `a03130f35e5b`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [high, conf 95] src/render.js:289 AC7 requires timeline rows for SequenceGap rows to follow their message, and the timeline to hold the events whose message number is on the page. pageNumbers is
- F2 [high, conf 80] src/render.js:287 AC10 requires div.stats, div.trades and filter options to be identical across pages; renderStats/renderTrades/renderFilters are called with full decoded/shown/e

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `e23113c3cd`: **214/214** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-delimiters.test.js | 14 | 14 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-events.test.js | 11 | 11 |  |
| acc-filters.test.js | 8 | 8 |  |
| acc-framing-rules.test.js | 11 | 11 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 4 | 4 |  |
| acc-order-story.test.js | 12 | 12 |  |
| acc-orders.test.js | 10 | 10 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-pager.test.js | 24 | 24 |  |
| acc-paging.test.js | 14 | 14 |  |
| acc-performance.test.js | 2 | 2 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-21 has landed:
- `acc-pager.test.js`: 24 of 24 pass, met

Host copies from commit `b50786bfd690`: 20 hidden test files.

Retired on purpose (not counted): `test/acc-analyse.test.js > over a limit nothing is decoded`, `test/acc-check.test.js > bad tags`, `test/acc-limits.test.js > byte limit is UTF-8 and inclusive at 1,048,576`, `test/acc-limits.test.js > message limit: 1,000 accepted, 1,001 refused, warning names both numbers`, `test/acc-presentation.test.js > empty states and the size warning`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- none

Newly passing: 23. No regressions.
