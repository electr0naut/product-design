# FXL-15: evidence

Patch: `FXL-15.patch` (`git format-patch ee91fe2..8cce6aa` of the trusted repo).
```
8cce6aa FXL-15: Show the story of a selected order
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 23 | 197701 | 10335 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 12 | 120149 | 5816 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 4 | 19094 | 8257 | 0.0080 |
| scribe | deepseek-flash | deepseek | 1 | 31 | 47517 | 23050 | 0.0262 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 10 | 68553 | 5463 | 0.0000 |

Claude on the review(s): **$1.5345**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/render.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 13; lint True; pass_to_pass True
- Mutation (stryker): killed 153, survived 7, timeout 0, no tests 0, unrun 0, static (not measured) 2; incomplete: False; error: None
- Survivors (up to 12):
- src/main.js:24 `const view = { orderId: null, filters: {} };` -> `{}` ACs ['AC8']
- src/render.js:68 `button.addEventListener('click', () => handlers?.clear?.());` -> `handlers?.clear()` ACs ['AC4', 'AC8']
- src/render.js:68 `button.addEventListener('click', () => handlers?.clear?.());` -> `handlers.clear` ACs ['AC4', 'AC8']
- src/render.js:71 `const canPickOrder = (tag, id) => id != null && id !== '' && (tag !== ` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:71 `const canPickOrder = (tag, id) => id != null && id !== '' && (tag !== ` -> `false` ACs ['AC0', 'AC1', 'AC10', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:76 `button.addEventListener('click', () => handlers?.pick?.(id));` -> `handlers?.pick(id)` ACs ['AC0', 'AC1', 'AC8']
- src/render.js:83 `else add(row, 'span', 'id', text);` -> `""` ACs ['AC2']
- Host copies the review read: commit `23952fd05985`, design sha256 `023e2adfdb09`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [high, conf 65] src/render.js:175 The summary banner and order span drop the group's identifiers when orderGroups() returns null/empty sets for them (order-state is drawn from a group whose clOr
- F2 [medium, conf 55] src/render.js:171 orderTerms() builds the '@ <44>' part as a separate space-joined item, so when 44 is present but 38/55 are missing the result begins with '@ 71.25' with a leadi
- F3 [medium, conf 60] src/render.js:150 orderState() uses messages.findLast, which depends on Array.prototype.findLast being available in the jsdom/node target; on older Node (<18) or browsers without

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2', 'F3']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `8cce6aa1a8`: **159/173** pass.

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
| acc-trades.test.js | 0 | 14 |  |

Hidden files expected to pass in full once FXL-15 has landed:
- `acc-order-story.test.js`: 12 of 12 pass, met

Host copies from commit `23952fd05985`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-trades.test.js > a filter and a selected order apply together` (fail)
- `test/acc-trades.test.js > a set filter is the selected option, and Clear filters appears and calls setFilter(null, null)` (fail)
- `test/acc-trades.test.js > changing a select calls setFilter with the value, or null for All` (fail)
- `test/acc-trades.test.js > figures: four decimals at most, no trailing zeros, no thousands separator, zero net without a sign` (fail)
- `test/acc-trades.test.js > filtering never changes a result: gaps keep their detail and no gap is invented` (fail)
- `test/acc-trades.test.js > five filters with their labels, All first, values in plain order, disabled when empty` (fail)
- `test/acc-trades.test.js > no orders and no fills: the empty text and no table` (fail)
- `test/acc-trades.test.js > nothing passes: the empty text, and malformed cards are hidden while a filter is set` (fail)
- `test/acc-trades.test.js > on the page: choose a filter, clear it, and Decode again resets the filters` (fail)
- `test/acc-trades.test.js > option texts made of markup stay text, and option values never hold pasted text` (fail)
- `test/acc-trades.test.js > the Account filter narrows the cards, the timeline, the strip and the trading summary` (fail)
- `test/acc-trades.test.js > the notes: the fixed note, and the unmatched note in plural and singular` (fail)
- `test/acc-trades.test.js > the summary holds the strip, then the trades, then the filters` (fail)
- `test/acc-trades.test.js > the trading table: heads and the figures of log A` (fail)

Newly passing: 10. No regressions.
