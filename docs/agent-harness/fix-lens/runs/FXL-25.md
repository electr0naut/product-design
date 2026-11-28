# FXL-25: evidence

Patch: `FXL-25.patch` (`git format-patch e1a91b6..f1dd618` of the trusted repo).
```
f1dd618 FXL-25: Accept valid ISO-8859-1 FIX framing
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6.2-sol | openai-codex | 1 | 22 | 178903 | 6294 | 0.0000 |
| planner | gpt-6.2-sol | openai-codex | 1 | 14 | 123850 | 5209 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 9 | 95375 | 66828 | 0.0556 |
| scribe | deepseek-flash | deepseek | 1 | 67 | 53470 | 42020 | 0.0473 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 65032 | 4392 | 0.0000 |

Claude on the review(s): **$0.4935**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/framing.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 9; lint True; pass_to_pass True
- Mutation (stryker): killed 49, survived 6, timeout 1, no tests 0, unrun 0, static (not measured) 0; incomplete: False; error: None
- Survivors (up to 12):
- src/framing.js:98 `let hasNonAscii = false;` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/framing.js:105 `if (separated) sum++;` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/framing.js:109 `if (code >= 0x80) hasNonAscii = true;` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/framing.js:109 `if (code >= 0x80) hasNonAscii = true;` -> `code < 0x80` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/framing.js:113 `return hasNonAscii && length === expectedLength && sum % 256 === expec` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
- src/framing.js:113 `return hasNonAscii && length === expectedLength && sum % 256 === expec` -> `hasNonAscii || length === expectedLength` ACs ['AC0', 'AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8', 'AC9']
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
Hidden acceptance suite on trusted main `f1dd618de8`: **268/277** pass.

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
| acc-single-byte.test.js | 9 | 9 |  |
| acc-summary.test.js | 18 | 18 |  |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 14 | 14 |  |

Hidden files expected to pass in full once FXL-25 has landed:
- `acc-single-byte.test.js`: 9 of 9 pass, met

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

Newly passing: 5. No regressions.
