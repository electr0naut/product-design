# FXL-24: evidence

Patch: `FXL-24.patch` (`git format-patch 4c479c6..e1a91b6` of the trusted repo).
```
e1a91b6 FXL-24 Restart timeline sequencing on Logon 1
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 18 | 180285 | 6986 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 12 | 117230 | 6744 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 2 | 6556 | 12182 | 0.0083 |
| scribe | deepseek-flash | deepseek | 1 | 52 | 42597 | 24558 | 0.0298 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 6 | 28783 | 2696 | 0.0000 |

Claude on the review(s): **$0.4757**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/timeline.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 8; lint True; pass_to_pass True
- Mutation (stryker): killed 15, survived 0, timeout 0, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
none
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
Hidden acceptance suite on trusted main `e1a91b6974`: **263/277** pass.

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
| acc-pick.test.js | 2 | 11 |  |
| acc-presentation.test.js | 21 | 21 |  |
| acc-restart.test.js | 11 | 11 |  |
| acc-single-byte.test.js | 4 | 9 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-24 has landed:
- `acc-restart.test.js`: 11 of 11 pass, met

Host copies from commit `2a7550244286`: 25 hidden test files.

Retired on purpose (not counted): `test/acc-analyse.test.js > over a limit nothing is decoded`, `test/acc-check.test.js > bad tags`, `test/acc-limits.test.js > byte limit is UTF-8 and inclusive at 1,048,576`, `test/acc-limits.test.js > message limit: 1,000 accepted, 1,001 refused, warning names both numbers`, `test/acc-presentation.test.js > empty states and the size warning`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- `test/acc-pick.test.js > a half is still found when the whole part has eight, nine or ten digits` (fail)
- `test/acc-pick.test.js > a thousand averages on a half, each checked against decimal arithmetic` (fail)
- `test/acc-pick.test.js > an OrigClOrdID button carries its message too` (fail)
- `test/acc-pick.test.js > an average exactly on a half is rounded away from zero` (fail)
- `test/acc-pick.test.js > every id button calls pick with the id and the number of its message` (fail)
- `test/acc-pick.test.js > on the page: the OrderID button of message 4 opens order B, not the order whose ClOrdID has that value` (fail)
- `test/acc-pick.test.js > on the page: two clients with the same ClOrdID, each button opens its own client's order` (fail)
- `test/acc-pick.test.js > quantities and the net on a half: away from zero on both sides` (fail)
- `test/acc-pick.test.js > view.orderMessage decides which order is shown when a value belongs to two` (fail)
- `test/acc-single-byte.test.js > a fill with an accented account name, counted one byte per character, is in the trading summary` (fail)
- `test/acc-single-byte.test.js > each delimiter form, and both ways of counting in one paste` (fail)
- `test/acc-single-byte.test.js > every character from U+0080 to U+00FF counts as one byte with its own value` (fail)
- `test/acc-single-byte.test.js > the neighbours of a malformed single-byte message are untouched` (fail)
- `test/acc-single-byte.test.js > the validation's message: counts right for one byte per character, valid` (fail)

Newly passing: 4. No regressions.
