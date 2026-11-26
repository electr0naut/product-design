# FXL-2B: evidence

Patch: `FXL-2B.patch` (`git format-patch 7f47748..main` of the trusted repo; commits below).
```
356ab44 Strengthen checksum regressions against base and delimiter mutant
b36354c Compute FIX CheckSum over SOH-normalized bytes
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 2 | 38 | 91673 | 8939 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 11 | 27460 | 3540 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 11 | 74704 | 28540 | 0.0296 |
| scribe | deepseek-flash | deepseek | 1 | 32 | 40852 | 14193 | 0.0195 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 11 | 34490 | 4166 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.5855**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/framing.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 4; lint True; pass_to_pass True
- Mutation (stryker): killed 6, survived 0, timeout 0, no tests 0, unrun 0, 1.9 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
none

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 85] test/helpers/fix.js:49 The helper converts the delimiter to SOH only when it is `|`. It accepts any `opts.delim`, and for any other non-SOH delimiter it still computes CheckSum over t

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1']}

## Fix pass
pass 1 (gates)

## Hidden acceptance suite
Hidden acceptance suite on trusted main `356ab44656`: **19/42** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-dictionary.test.js | 1 | 4 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 0 | 9 | module did not import (feature not built yet?) |

Newly passing: 4. No regressions.
