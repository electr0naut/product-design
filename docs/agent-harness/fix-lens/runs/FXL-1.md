# FXL-1: evidence

Patch: `FXL-1.patch` (`git format-patch 4e3aaac..main` of the trusted repo; commits below).
```
8057bbf FXL-1: reject 8=FIX inside a field value when no delimiter precedes it
8df6b78 FXL-1: split pasted log into messages and parse fields
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | qwen3.7-plus | alibaba-token-plan | 2 | 55 | 246751 | 37796 | 0.0000 |
| planner | qwen3.7-plus | alibaba-token-plan | 1 | 10 | 75256 | 6570 | 0.0000 |
| reviewer | qwen3.7-plus | alibaba-token-plan | 3 | 4 | 44159 | 52970 | 0.0000 |
| scribe | deepseek-flash | deepseek | 1 | 40 | 42507 | 20827 | 0.0254 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 29864 | 3794 | 0.0000 |

Claude (refuter and prover) on the review(s): **$0.6659**.

## Tier, gates, mutation
- Tier: **high** (the diff changes 785 lines (limit 500)); refuter skipped: False
- Gates: passed **True**; valid tests 24; lint True; pass_to_pass True
- Mutation (stryker): killed 116, survived 76, timeout 25, no tests 61, unrun 0, 11.9 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/framing.js:28 `if (typeof text !== "string" || text.length === 0) return [];` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:28 `if (typeof text !== "string" || text.length === 0) return [];` -> `typeof text !== "string" && text.length === 0` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:28 `if (typeof text !== "string" || text.length === 0) return [];` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:28 `if (typeof text !== "string" || text.length === 0) return [];` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:33 `while (pos < text.length) {` -> `pos <= text.length` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:44 `let end = -1; // end offset (exclusive) of the whole candidate` -> `+1` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:46 `while (cursor < text.length) {` -> `cursor <= text.length` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:53 `if (eqIdx === -1) {` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:71 `if (!/^\d+$/.test(tagStr)) {` -> `false` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:71 `if (!/^\d+$/.test(tagStr)) {` -> `/\d+$/` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:71 `if (!/^\d+$/.test(tagStr)) {` -> `/^\d+/` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC7', 'AC8']
- src/framing.js:88 `if (tag === 10 && /^\d{3}$/.test(value)) {` -> `/\d{3}$/` ACs ['AC1', 'AC2', 'AC3', 'AC4', 'AC5', 'AC6', 'AC8']

## Reviews that led to a fix pass
### review-2.json (cost $0.6659, decision {'blocking': ['F1'], 'blocking_unproven': [], 'notes': []})
- F1 [high, conf 95] src/framing.js:158 findMessageStart accepts '8=FIX' inside a field value when the field is at the start of a line (or after a line end) and the preceding character is not a digit.
- proof F1: proven=True (AssertionError: assertion failed) test `test/framing-f1.test.js > AC3: 8=FIX inside another field > does not start a message at 8=FIX inside the first field on a line`


## Findings and proofs (final review)
Findings:
none

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': []}

## Fix pass
pass 2 (review)
