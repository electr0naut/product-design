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

## Operator notes for the reviewer (read from the patch and the run files; nothing changed)
- **FXL-3 completed on the trusted main as `4e3aaac`** (first and only commit after the operator's `544c8c5`), with no fix pass; the planner finished on its single unblock, the later stages ran unattended. Scribe: `deepseek-flash`, $0.0162; everything else `qwen3.7-plus` at $0; Claude $0 because the finder reported nothing.
- **A deviation from the ticket that the gates and the review did not catch:** the ticket says the build writes `src/dictionary/fix42.json` and `src/dictionary/fix44.json` (lower case); the landed files are **`src/dictionary/FIX42.json` and `src/dictionary/FIX44.json`** (upper case), and `src/dictionary.js` and the 17 tests use those names. On a case-sensitive file system a later ticket (FXL-4's decode, FXL-7's page) or a hidden check that follows the ticket's spelling will not find them. The finder reported no findings, so this was not looked at as a defect. It is the reviewer's call whether this is a ticket-text point or a rework item.
- **Tier is `high` only because of size:** the diff is 9,608 lines (limit 500), nearly all generated JSON (2,501 + 6,572 lines). The size rule fired as designed; the refuter was not skipped, but with zero findings no Claude call was made.
- **Mutation:** Stryker 24 killed, 0 survived, **72 mutants with no covering test** (the changed lines of `tools/build-dictionary.mjs` that no test executes, apparently its command-line entry and file-writing code), 3.8 s. Report-only, as designed.
- `FXL-1` is still blocked; `FXL-2` and `FXL-4` to `FXL-7` wait behind it as designed (FXL-4 needs FXL-1 and FXL-3, and FXL-3 is now done).
