# FXL-3: evidence

Patch: `FXL-3.patch` (`git format-patch 544c8c5..main` of the trusted repo; commits below).
```
4e3aaac FXL-3: Generate FIX 4.2 and 4.4 dictionaries from Orchestra files
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | qwen3.7-plus | alibaba-token-plan | 1 | 39 | 144464 | 17004 | 0.0000 |
| planner | qwen3.7-plus | alibaba-token-plan | 2 | 33 | 206909 | 26097 | 0.0000 |
| reviewer | qwen3.7-plus | alibaba-token-plan | 1 | 4 | 32855 | 4493 | 0.0000 |
| scribe | deepseek-flash | deepseek | 1 | 26 | 39934 | 11977 | 0.0162 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 9 | 29718 | 4103 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.0000**.

## Tier, gates, mutation
- Tier: **high** (the diff changes 9608 lines (limit 500)); refuter skipped: False
- Gates: passed **True**; valid tests 17; lint True; pass_to_pass True
- Mutation (stryker): killed 24, survived 0, timeout 0, no tests 72, unrun 0, 3.8 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
none

## Findings and proofs (final review)
Findings:
none

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': []}

## Fix pass
no fix pass
