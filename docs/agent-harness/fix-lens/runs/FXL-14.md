# FXL-14: evidence

Patch: `FXL-14.patch` (`git format-patch bfb67b7..ee91fe2` of the trusted repo).
```
ee91fe2 FXL-14 Present decoded FIX logs with timeline and themes
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 27 | 244234 | 20066 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 9 | 98496 | 6610 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 8 | 101238 | 48883 | 0.0458 |
| scribe | deepseek-flash | deepseek | 1 | 50 | 67799 | 28984 | 0.0375 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 10 | 73658 | 7229 | 0.0000 |

Claude on the review(s): **$0.6364**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/page.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 14; lint True; pass_to_pass True
- Mutation (stryker): killed 227, survived 12, timeout 0, no tests 2, unrun 0, static (not measured) 4; incomplete: False; error: None
- Survivors (up to 12):
- src/main.js:8 `const systemTheme = window.matchMedia?.('(prefers-color-scheme: dark)'` -> `window.matchMedia('(prefers-color-scheme: dark)')` ACs ['AC13', 'AC2', 'AC9']
- src/main.js:10 `const isDark = () => override ?? systemTheme?.matches ?? false;` -> `systemTheme.matches` ACs ['AC13', 'AC2', 'AC9']
- src/main.js:15 `systemTheme?.addEventListener?.('change', updateThemeLabel);` -> `systemTheme.addEventListener` ACs ['AC13', 'AC2', 'AC9']
- src/main.js:21 `themeButton.hidden = false;` -> `true` ACs ['AC13', 'AC2', 'AC9']
- src/render.js:6 `if (className) node.className = className;` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:7 `if (text != null) node.textContent = text;` -> `true` ACs ['AC0', 'AC1', 'AC10', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:12 `const direction = (sender, target) => `${sender ?? ''} → ${target ?? '` -> `"Stryker was here!"` ACs ['AC9']
- src/render.js:12 `const direction = (sender, target) => `${sender ?? ''} → ${target ?? '` -> `"Stryker was here!"` ACs ['AC9']
- src/render.js:61 `add(head, 'h3', null, message.label.replace(/^Message \d+: /, ''));` -> `/Message \d+: /` ACs ['AC0', 'AC1', 'AC10', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:61 `add(head, 'h3', null, message.label.replace(/^Message \d+: /, ''));` -> `/^Message \d: /` ACs ['AC0', 'AC1', 'AC10', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:76 `add(row, 'td', null, message.supported === false ? '' : field.enumName` -> `false` ACs ['AC0', 'AC1', 'AC10', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/render.js:89 `const head = add(card, 'header', 'card-head');` -> `""` ACs ['AC0', 'AC1', 'AC3', 'AC6', 'AC8', 'AC9']
- Host copies the review read: commit `23952fd05985`, design sha256 `023e2adfdb09`

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
Hidden acceptance suite on trusted main `ee91fe240a`: **149/173** pass.

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
| acc-order-story.test.js | 2 | 12 |  |
| acc-orders.test.js | 10 | 10 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 0 | 14 |  |

Host copies from commit `23952fd05985`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-order-story.test.js > a selected order shows only its messages and events, with full-log numbers` (fail)
- `test/acc-order-story.test.js > an OrderID of NONE is plain text, not a button` (fail)
- `test/acc-order-story.test.js > an order with no ExecutionReport has no state, and empty terms make no span` (fail)
- `test/acc-order-story.test.js > ids made of markup stay text and never become attributes` (fail)
- `test/acc-order-story.test.js > missing parts of the terms and the state leave no stray separator` (fail)
- `test/acc-order-story.test.js > on the page: click an id, show all, and Decode again clears the selection` (fail)
- `test/acc-order-story.test.js > order ids are buttons in the timeline and in the cards, and call pick with the id alone` (fail)
- `test/acc-order-story.test.js > the banner of a replaced order: every id, no price, and a state without fills` (fail)
- `test/acc-order-story.test.js > the banner: ids, terms from the first NewOrder, state from the last ExecutionReport` (fail)
- `test/acc-order-story.test.js > the summary strip is narrowed while an order is selected` (fail)
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

Newly passing: 19. No regressions.
