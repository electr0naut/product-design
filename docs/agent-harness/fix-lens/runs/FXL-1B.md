# FXL-1B: evidence

Patch: `FXL-1B.patch` (`git format-patch f36221c..main` of the trusted repo; commits below).
```
7f47748 FXL-1B: respect candidate starts and validation bounds
3bb9a7e FXL-1B: align splitMessages interface and candidate boundaries
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 2 | 38 | 135664 | 12255 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 13 | 42480 | 4191 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 3 | 12 | 92251 | 82009 | 0.0650 |
| reviewer | qwen3.7-plus | None | 1 | 0 | 0 | 0 | 0.0000 |
| scribe | deepseek-flash | deepseek | 1 | 38 | 47577 | 19844 | 0.0256 |

Claude (refuter and prover) on the review(s): **$4.8321**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/framing-f1.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 9; lint True; pass_to_pass True
- Mutation (stryker): killed 39, survived 30, timeout 0, no tests 36, unrun 0, 5.2 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/framing.js:51 `(text[cursor - 1] === delim || text[cursor - 1] === "\n" || text[curso` -> `true` ACs ['AC3']
- src/framing.js:63 `if (fieldEnd >= text.length) { cursor = text.length; end = text.length` -> `false` ACs ['AC2']
- src/framing.js:63 `if (fieldEnd >= text.length) { cursor = text.length; end = text.length` -> `fieldEnd > text.length` ACs ['AC2']
- src/framing.js:135 `if (fields.length > 0) {` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:135 `if (fields.length > 0) {` -> `fields.length >= 0` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:139 `end: end === -1 ? text.length : end,` -> `false` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:139 `end: end === -1 ? text.length : end,` -> `+1` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:142 `pos = end === -1 ? cursor : end;` -> `true` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:142 `pos = end === -1 ? cursor : end;` -> `false` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:142 `pos = end === -1 ? cursor : end;` -> `end !== -1` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:142 `pos = end === -1 ? cursor : end;` -> `+1` ACs ['AC0', 'AC1', 'AC2', 'AC3']
- src/framing.js:179 `while (cursor < rawText.length) {` -> `cursor <= rawText.length` ACs ['AC2']

## Reviews that led to a fix pass
### review-3.json (cost $3.6803, decision {'blocking': ['F1', 'F2', 'F3', 'F4'], 'blocking_unproven': [], 'notes': []})
- F1 [high, conf 85] src/framing.js:387 The added prefix rejection (`prev === "="` or `/^\d+=/.test(textBefore)`) imposes a third condition that AC1/design step 2 and the function's own doc comment do not have (a candidate starts when the c
- F2 [high, conf 95] src/framing.js:387 findMessageStart adds exclusions the rule doesn't have. It rejects 8=FIX when the preceding character is '=', or when the line prefix starts with digits followed by '='. It does this even though the p
- F3 [high, conf 85] src/framing.js:363 A new filter accepts 8=FIX only when the next character is '.', 'T', '|', SOH, a line end or end of text. The design has no condition on what follows 8=FIX. As a result, some starts are dropped both o
- F4 [high, conf 88] src/framing.js:52 splitMessages now ends a candidate without a CheckSum where the next one starts on the same line. checkMessage ignores candidate.end and re-parses from candidate.start to the line end. The earlier can
- proof F1: proven=True (AssertionError: assertion failed) test `test/f1-prefix-equals.test.js > F1 delimiter-free prefix containing '=' > keeps a message whose prefix starts with digits and '='`
- proof F2: proven=True (AssertionError: assertion failed) test `test/f2-prefix-equals.test.js > F2: message start after a non-digit with no delimiter on the line > finds 8=FIX preceded by '=' or by a prefix starting with digits and '='`
- proof F3: proven=True (AssertionError: assertion failed) test `test/framing-f3.test.js > F3: no condition on what follows 8=FIX > returns a candidate when a digit follows 8=FIX`
- proof F4: proven=True (AssertionError: assertion failed) test `test/f4-candidate-bound.test.js > F4: checkMessage respects the candidate boundary > reports missing_checksum for a candidate cut off by the next message`


## Findings and proofs (final review)
Findings:
- F1 [high, conf 92] src/framing.js:50 The new delimiter-adjacent split guard requires findMessageStart(text, cursor) === cursor, but findMessageStart itself skips any 8=FIX hit whose line prefix con
- F3 [medium, conf 68] src/framing.js:96 The CheckSum terminator tests the numeric value Number(tagStr) === 10, so fields such as `010=123` or `0010=123` end the candidate although they do not start wi

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F3']}

## Fix pass
pass 3 (review)

## Hidden acceptance suite
Hidden acceptance suite on trusted main `7f47748347`: **15/42** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 5 | 9 |  |
| acc-decode.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-dictionary.test.js | 1 | 4 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 0 | 9 | module did not import (feature not built yet?) |

Newly passing: 15. No regressions.
