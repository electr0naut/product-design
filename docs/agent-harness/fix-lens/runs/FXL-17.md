# FXL-17: evidence

Patch: `FXL-17.patch` (`git format-patch 8881fce..bfb67b7` of the trusted repo).
```
bfb67b7 FXL-17: verify order selection is unchanged by Heartbeats
3f4b42b FXL-17 Keep matching standalone messages in Account filter
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 2 | 31 | 283551 | 7385 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 12 | 103302 | 5013 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 10 | 20187 | 13368 | 0.0116 |
| scribe | deepseek-flash | deepseek | 1 | 44 | 36081 | 19820 | 0.0233 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 6 | 27360 | 2192 | 0.0000 |

Claude on the review(s): **$0.4450**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/filters.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 3; lint True; pass_to_pass True
- Mutation (stryker): killed 6, survived 0, timeout 0, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
none
- Host copies the review read: commit `23952fd05985`, design sha256 `023e2adfdb09`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
none

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': []}

## Fix pass
pass 1 (gates)

## Hidden acceptance suite
Hidden acceptance suite on trusted main `bfb67b7899`: **130/173** pass.

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
| acc-order-story.test.js | 0 | 12 |  |
| acc-orders.test.js | 10 | 10 |  |
| acc-page.test.js | 5 | 5 |  |
| acc-presentation.test.js | 4 | 21 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 0 | 14 |  |

Host copies from commit `23952fd05985`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-order-story.test.js > a selected order shows only its messages and events, with full-log numbers` (fail)
- `test/acc-order-story.test.js > an OrderID of NONE is plain text, not a button` (fail)
- `test/acc-order-story.test.js > an order id that matches nothing shows the whole log without a banner` (fail)
- `test/acc-order-story.test.js > an order with no ExecutionReport has no state, and empty terms make no span` (fail)
- `test/acc-order-story.test.js > ids made of markup stay text and never become attributes` (fail)
- `test/acc-order-story.test.js > missing parts of the terms and the state leave no stray separator` (fail)
- `test/acc-order-story.test.js > on the page: click an id, show all, and Decode again clears the selection` (fail)
- `test/acc-order-story.test.js > order ids are buttons in the timeline and in the cards, and call pick with the id alone` (fail)
- `test/acc-order-story.test.js > render(result) alone still shows the whole log` (fail)
- `test/acc-order-story.test.js > the banner of a replaced order: every id, no price, and a state without fills` (fail)
- `test/acc-order-story.test.js > the banner: ids, terms from the first NewOrder, state from the last ExecutionReport` (fail)
- `test/acc-order-story.test.js > the summary strip is narrowed while an order is selected` (fail)
- `test/acc-presentation.test.js > OrigClOrdID and ExecRefID are shown on the rows that have them` (fail)
- `test/acc-presentation.test.js > a message card: header, four column heads and one row per field` (fail)
- `test/acc-presentation.test.js > a second render replaces the first` (fail)
- `test/acc-presentation.test.js > a timeline row: number, time part, badge, direction, sequence number and ids` (fail)
- `test/acc-presentation.test.js > an unsupported version is labelled, without made-up field names` (fail)
- `test/acc-presentation.test.js > empty states and the size warning` (fail)
- `test/acc-presentation.test.js > every colour in the stylesheet is one of the properties` (fail)
- `test/acc-presentation.test.js > index.html: header, privacy line, theme button, not-started message and the three sections` (fail)
- `test/acc-presentation.test.js > main.js removes the not-started message, and Decode fills the page` (fail)
- `test/acc-presentation.test.js > malformed messages are error cards at their place in log order` (fail)
- `test/acc-presentation.test.js > row classes: gap, reject, order, session; the badge always names the event` (fail)
- `test/acc-presentation.test.js > text contrast is at least 4.5 to 1 in both themes` (fail)
- `test/acc-presentation.test.js > the colour properties are declared three times, as hex, with equal dark blocks` (fail)
- `test/acc-presentation.test.js > the summary strip has five counts, with singular forms` (fail)
- `test/acc-presentation.test.js > the theme button switches the class on <html> and names the theme it would switch to` (fail)
- `test/acc-presentation.test.js > the tool is hidden until the script starts, with the message outside it` (fail)
- `test/acc-presentation.test.js > two columns from 900px with a sticky timeline` (fail)
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

Newly passing: 14. No regressions.
