# FXL-9: evidence

Patch: `FXL-9.patch` (`git format-patch e721f31..60b1211` of the trusted repo).
```
60b1211 FXL-9: support FIX log delimiter forms and literal values
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 25 | 251614 | 15908 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 17 | 150618 | 8152 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 4 | 43799 | 1412 | 0.0076 |
| scribe | deepseek-flash | deepseek | 1 | 50 | 68384 | 27797 | 0.0367 |

Claude on the review(s): **$1.6305**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/framing-f1.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 19; lint True; pass_to_pass True
- Mutation (None): killed None, survived None, timeout None, no tests None, unrun None; incomplete: None; error: stryker wrote no report (exit 1): Item.execute (file:///srv/lab/agent-harness/deps/fix-lens/node_modules/@stryker-mutator/core/dist/src/concurrent/pool.js:34:28) at async file:///srv/lab/agent-harness/deps/fix-lens/node_modules/@stryker-mutator/core/dist/src/concurrent/pool.js:71:13 { innerError: un
- Survivors (up to 12):
none
- Host copies the review read: commit `ae216b0f82e0`, design sha256 `4c2cb3fd5236`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [high, conf 75] tools/audit-source.mjs:44 auditElements checks a <template>'s inert content, but that content is not reachable from the document that JSDOM would execute. Inline code hidden inside a <te
- F2 [medium, conf 85] tools/audit-source.mjs:44 The on...= attribute check only runs for elements that are in the document's DOM tree; it does not inspect the content of a <template>.
- F3 [high, conf 60] src/framing.js:100 scanCandidate breaks at any '8=FIX' that starts at a field position, whether or not the text is a valid separator boundary, so a text-delimited candidate whose 
- F4 [medium, conf 55] src/framing.js:48 findFieldBoundary accepts the delimiter after a checksum-shaped field as the end of the message without checking that the segment before it is a complete '10=dd

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2', 'F3', 'F4']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `60b1211023`: **77/166** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-delimiters.test.js | 14 | 14 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-events.test.js | 0 | 11 | module did not import (feature not built yet?) |
| acc-filters.test.js | 0 | 8 | module did not import (feature not built yet?) |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 3 | 3 |  |
| acc-order-story.test.js | 0 | 12 |  |
| acc-orders.test.js | 0 | 10 | module did not import (feature not built yet?) |
| acc-page.test.js | 5 | 5 |  |
| acc-presentation.test.js | 4 | 21 |  |
| acc-render.test.js | 5 | 5 |  |
| acc-summary.test.js | 0 | 17 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 0 | 14 |  |

Host copies from commit `ae216b0f82e0`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-events.test.js > <collection>` (error)
- `test/acc-filters.test.js > <collection>` (error)
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
- `test/acc-orders.test.js > <collection>` (error)
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
- `test/acc-summary.test.js > <collection>` (error)
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
