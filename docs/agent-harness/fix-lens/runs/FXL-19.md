# FXL-19: evidence

Patch: `FXL-19.patch` (`git format-patch 6f2f554..4a611b1` of the trusted repo).
```
4a611b1 FXL-19 Raise inclusive FIX log paste limits
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| bk-sp-max | qwen4-max | None | 1 | 0 | 0 | 0 | 0.0000 |
| bk-sp-max | qwen4-max | alibaba-token-plan | 5 | 5 | 106494 | 68698 | 0.0000 |
| bk-sp-plus | qwen3.7-plus | None | 1 | 0 | 0 | 0 | 0.0000 |
| implementer | gpt-6.2-sol | openai-codex | 1 | 16 | 147805 | 7008 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 10 | 106803 | 5140 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 7 | 100025 | 20101 | 0.0279 |
| scribe | deepseek-flash | deepseek | 1 | 34 | 40448 | 24590 | 0.0265 |

Claude on the review(s): **$1.0329**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/analyse.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 9; lint True; pass_to_pass True
- Mutation (stryker): killed 9, survived 0, timeout 0, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
none
- Host copies the review read: commit `b50786bfd690`, design sha256 `a03130f35e5b`

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 97] test/performance.test.js:32 Both performance tests join their messages with an empty string instead of `\n`. This happens at line 32 (`frames.join('')`, the AC4 mixed log) and line 62 (`.j
- F2 [medium, conf 55] test/limits.test.js:52 The ticket names the `toBeLessThan(1048576)` line as one that must move to the new numbers. The rewritten count-refusal test still checks against the old size l

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `4a611b11d8`: **177/214** pass.

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
| acc-pager.test.js | 1 | 24 |  |
| acc-paging.test.js | 0 | 14 | module did not import (feature not built yet?) |
| acc-performance.test.js | 2 | 2 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-19 has landed:
- `acc-analyse.test.js`: 4 of 4 pass, met
- `acc-limits.test.js`: 4 of 4 pass, met
- `acc-performance.test.js`: 2 of 2 pass, met
- `acc-presentation.test.js`: 21 of 21 pass, met

Host copies from commit `b50786bfd690`: 20 hidden test files.

Retired on purpose (not counted): `test/acc-analyse.test.js > over a limit nothing is decoded`, `test/acc-check.test.js > bad tags`, `test/acc-limits.test.js > byte limit is UTF-8 and inclusive at 1,048,576`, `test/acc-limits.test.js > message limit: 1,000 accepted, 1,001 refused, warning names both numbers`, `test/acc-presentation.test.js > empty states and the size warning`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-pager.test.js > 10,000 messages: only one page of cards and timeline rows is built` (fail)
- `test/acc-pager.test.js > 450 messages: the page line and the cards of pages 1, 2 and 3` (fail)
- `test/acc-pager.test.js > First and Previous are disabled on page 1, Next and Last on the last page` (fail)
- `test/acc-pager.test.js > a filter that leaves 200 messages or fewer shows no pager` (fail)
- `test/acc-pager.test.js > a log of 201 messages has two pages: 200 cards, then one` (fail)
- `test/acc-pager.test.js > a malformed message alone on the last page` (fail)
- `test/acc-pager.test.js > a page that does not exist is made valid, and a missing page is page 1` (fail)
- `test/acc-pager.test.js > both events of a message are on its page: a sequence gap follows its message` (fail)
- `test/acc-pager.test.js > each pager holds the page line and four buttons, in order, and nothing else` (fail)
- `test/acc-pager.test.js > main.js: a second decode of a short log leaves no pager behind` (fail)
- `test/acc-pager.test.js > main.js: choosing, changing and clearing a filter each go back to page 1` (fail)
- `test/acc-pager.test.js > main.js: picking an order, returning to all messages and decoding again each go back to page 1` (fail)
- `test/acc-pager.test.js > main.js: the page buttons move through the pages and bring the results back into view` (fail)
- `test/acc-pager.test.js > main.js: where the results have no scrollIntoView, changing the page still works` (fail)
- `test/acc-pager.test.js > malformed messages count, at their place in the log` (fail)
- `test/acc-pager.test.js > styles: the pager is a wrapping row, its buttons are quiet, a disabled one is muted` (fail)
- `test/acc-pager.test.js > the buttons of both pagers call handlers.setPage with a page number` (fail)
- `test/acc-pager.test.js > the summary strip, the trading summary and the filter lists are those of the whole log on every page` (fail)
- `test/acc-pager.test.js > the timeline shows the events of the messages on the page, and no others` (fail)
- `test/acc-pager.test.js > the two pagers: last in #summary after the filters, last in #decode after the cards` (fail)
- `test/acc-pager.test.js > with a filter set the pages run over the messages shown, and the line says so` (fail)
- `test/acc-pager.test.js > with a filter set the trading summary is that of the whole filtered log on every page` (fail)
- `test/acc-pager.test.js > with an order selected the pages run over its messages, and the banner is the same on every page` (fail)
- `test/acc-paging.test.js > <collection>` (error)

Newly passing: 8. No regressions.
