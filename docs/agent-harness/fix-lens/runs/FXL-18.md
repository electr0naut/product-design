# FXL-18: evidence

Patch: `FXL-18.patch` (`git format-patch d520fe7..6f2f554` of the trusted repo).
```
6f2f554 FXL-18: Style the order banner, the order links, the trading summary and the filters
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | deepseek-v4.1-flash-1017 | alibaba-token-plan | 1 | 33 | 49680 | 18129 | 0.0000 |
| planner | qwen3.7-plus | alibaba-token-plan | 1 | 13 | 79191 | 6298 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 2 | 3652 | 16903 | 0.0108 |
| scribe | deepseek-flash | deepseek | 1 | 21 | 23927 | 9523 | 0.0117 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 29546 | 3635 | 0.0000 |

Claude on the review(s): **$0.4590**.

## Tier, gates, mutation
- Tier: **standard** (no high- or low-risk signal); refuter skipped: False
- Gates: passed **True**; valid tests 11; lint True; pass_to_pass True
- Mutation (None): killed None, survived None, timeout None, no tests None, unrun None; incomplete: None; error: None
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
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `6f2f554ac5`: **173/173** pass.

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

Host copies from commit `23952fd05985`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-render.test.js > a second render replaces the first, and errors and the size warning are shown`, `test/acc-render.test.js > an unsupported version is labelled and its fields are shown raw, without made-up names`, `test/acc-render.test.js > decode rows show tag, name, raw value and enum meaning`, `test/acc-render.test.js > pasted markup is shown as text and creates no element`, `test/acc-render.test.js > timeline rows show every AC-010 field for an order event`, `test/acc-timeline.test.js > event keys`

Failing hidden tests, by name:
- none

Newly passing: 0. No regressions.
