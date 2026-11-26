# FXL-7: evidence

Patch: `FXL-7.patch` (`git format-patch d8a2477..main` of the trusted repo; commits below).
```
8db74fc Build local FIX Lens page and privacy checks
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 4 | 53 | 110745 | 11269 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 14 | 54074 | 4416 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 4 | 6874 | 60538 | 0.0377 |
| scribe | deepseek-flash | deepseek | 1 | 27 | 34840 | 14117 | 0.0177 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 10 | 76283 | 4586 | 0.0000 |

Claude (refuter and prover) on the review(s): **$1.6363**.

## Tier, gates, mutation
- Tier: **high** (ticket label security is high-risk); refuter skipped: False
- Gates: passed **True**; valid tests 9; lint True; pass_to_pass True
- Mutation (stryker): killed 50, survived 8, timeout 0, no tests 1, unrun 0, 11.5 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- src/render.js:10 `if (className) node.className = className;` -> `true` ACs ['AC4', 'AC5', 'AC7']
- src/render.js:20 `const card = add(decodeSection, 'article', '');` -> `"Stryker was here!"` ACs ['AC4', 'AC5', 'AC7']
- src/render.js:23 `add(card, 'div', `${field.tag} ${field.name}: ${field.value}${field.en` -> `true` ACs ['AC4', 'AC5', 'AC7']
- src/render.js:23 `add(card, 'div', `${field.tag} ${field.name}: ${field.value}${field.en` -> `false` ACs ['AC4', 'AC5', 'AC7']
- src/render.js:23 `add(card, 'div', `${field.tag} ${field.name}: ${field.value}${field.en` -> `field.enumName !== null` ACs ['AC4', 'AC5', 'AC7']
- src/render.js:23 `add(card, 'div', `${field.tag} ${field.name}: ${field.value}${field.en` -> `"Stryker was here!"` ACs ['AC5', 'AC7']
- src/render.js:23 `add(card, 'div', `${field.tag} ${field.name}: ${field.value}${field.en` -> ```` ACs ['AC4', 'AC7']
- src/render.js:28 `add(timelineSection, 'p', `Message ${event.number}: ${event.name}${eve` -> `"Stryker was here!"` ACs ['AC4', 'AC7']

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [medium, conf 88] src/analyse.js:15 `analyse().messages` holds the raw `splitMessages` candidates, which have only `{ number, start, end, fields }`. `analyse()` never adds the `beginString` and `m
- F2 [high, conf 75] src/render.js:28 The Timeline section shows only the message number, event name and detail. It drops SendingTime, sender (49), target (56) and MsgSeqNum (34), and also ClOrdID a
- F3 [medium, conf 70] test/static-checks.test.js:16 The regex that strips comments ignores string literals. A `//` or `/*` inside a string is treated as the start of a comment, so real forbidden API calls after i
- F4 [medium, conf 50] src/render.js:23 The renderer ignores `supported: false`. Fields of an unsupported-version message are not shown raw: each one gets a made-up 'Unknown tag X' name, including sta

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F2', 'F3', 'F4']}

## Fix pass
no fix pass

## Hidden acceptance suite
Hidden acceptance suite on trusted main `8db74fca82`: **53/53** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 3 | 3 |  |
| acc-page.test.js | 4 | 4 |  |
| acc-timeline.test.js | 14 | 14 |  |

Newly passing: 8. No regressions.

Failing hidden tests, by name:

- none
