# FXL-16: evidence

Patch: `FXL-16.patch` (`git format-patch 8cce6aa..d520fe7` of the trusted repo).
```
d520fe7 FXL-16: Show the trading summary and the filters
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | deepseek-v4.1-flash-1017 | alibaba-token-plan | 1 | 36 | 132740 | 46765 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 15 | 128614 | 8930 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 4 | 22246 | 9525 | 0.0092 |
| scribe | deepseek-flash | deepseek | 1 | 42 | 61238 | 22735 | 0.0310 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 11 | 83351 | 7260 | 0.0000 |

Claude on the review(s): **$2.4488**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/render.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 18; lint True; pass_to_pass True
- Mutation (stryker): killed 136, survived 9, timeout 0, no tests 1, unrun 0, static (not measured) 19; incomplete: False; error: None
- Survivors (up to 12):
- src/main.js:38 `} else if (value == null) {` -> `false` ACs ['AC13']
- src/render.js:87 `if (chosen[key] != null && values.includes(chosen[key])) select.select` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:87 `if (chosen[key] != null && values.includes(chosen[key])) select.select` -> `chosen[key] != null || values.includes(chosen[key]` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:87 `if (chosen[key] != null && values.includes(chosen[key])) select.select` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC11', 'AC12', 'AC13', 'AC14', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:89 `select.addEventListener('change', () => handlers?.setFilter?.(key, val` -> `handlers?.setFilter(key, values[select.selectedInd` ACs ['AC13', 'AC7']
- src/render.js:89 `select.addEventListener('change', () => handlers?.setFilter?.(key, val` -> `handlers.setFilter` ACs ['AC13', 'AC7']
- src/render.js:94 `button.addEventListener('click', () => handlers?.setFilter?.(null, nul` -> `handlers?.setFilter(null, null)` ACs ['AC13', 'AC8']
- src/render.js:94 `button.addEventListener('click', () => handlers?.setFilter?.(null, nul` -> `handlers.setFilter` ACs ['AC13', 'AC8']
- src/render.js:255 `const wholeOrder = result.decoded.filter(message => numbers.has(messag` -> `result.decoded` ACs ['AC0', 'AC11']
- Host copies the review read: commit `23952fd05985`, design sha256 `023e2adfdb09`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [high, conf 92] src/render.js:268 renderStats uses `narrowed` for the orders count, but AC10 says the N of M strip should show the orders among the messages shown. The order count is patched onl
- F2 [high, conf 90] src/render.js:257 Malformed errors that pass the account/sender filter are dropped from the count but still rendered. renderMessages is passed `errors = result.errors` unchanged;
- F3 [critical, conf 88] src/render.js:262 The `errors` empty-state path uses NO_MATCHES only when entries has length 0, but with a filter set and errors still present, narrowed=false is not passed. More
- F4 [medium, conf 85] src/render.js:259 `shown` includes only decoded numbers even though `narrowed` is true when a filter is set: the summary gets `shown` only for decoded messages. AC10 counts malfo
- F5 [medium, conf 80] src/render.js:245 `renderTrades` always renders when the summary has rows, but AC12/AC9 require the trades panel to reflect only the shown messages while the note/unmatched logic

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2', 'F3', 'F4', 'F5']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `d520fe7617`: **173/173** pass.

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
| acc-limits.test.js | 3 | 3 |  |
| acc-order-story.test.js | 12 | 12 |  |
| acc-orders.test.js | 10 | 10 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-16 has landed:
- `acc-trades.test.js`: 14 of 14 pass, met

Host copies from commit `23952fd05985`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- none

Newly passing: 14. No regressions.
