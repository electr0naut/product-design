# FXL-3B: evidence

Patch: `FXL-3B.patch` (`git format-patch 356ab44..main` of the trusted repo; commits below).
```
0acbcbf Make top-level dictionary test detect base API
540f56f Align dictionary API and isolated dependency-free build
```

## Models and cost (sessions started while this ticket ran)
| profile | model | provider | sessions | api calls | input tok | output tok | cost USD |
|---|---|---|---|---|---|---|---|
| implementer | gpt-6-sol | openai-codex | 2 | 49 | 102144 | 12561 | 0.0000 |
| planner | gpt-6-sol | openai-codex | 1 | 10 | 37005 | 3720 | 0.0000 |
| reviewer | deepseek-flash | deepseek | 1 | 1 | 13422 | 1274 | 0.0028 |
| scribe | deepseek-flash | deepseek | 1 | 36 | 51341 | 19235 | 0.0257 |
| triage | qwen3.7-plus | alibaba-token-plan | 1 | 8 | 32066 | 4928 | 0.0000 |

Claude (refuter and prover) on the review(s): **$1.4376**.

## Tier, gates, mutation
- Tier: **high** (the diff edits or deletes the existing test test/dictionary.test.js); refuter skipped: False
- Gates: passed **True**; valid tests 13; lint True; pass_to_pass True
- Mutation (stryker): killed 0, survived 83, timeout 0, no tests 0, unrun 0, 1.5 s; incomplete: False; warning: None; error: None
- Survivors (up to 12):
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-])\s*=\s*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([^\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\W:-]+)\s*=\s*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s=\s*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\S*=\s*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\s("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\S*("[^"]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\s*("[^"]"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\s*("["]*"|'[^']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\s*("[^"]*"|'[^']')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `/([\w:-]+)\s*=\s*("[^"]*"|'[']*')/g` ACs []
- tools/build-dictionary.mjs:21 `for (const match of tag.matchAll(/([\w:-]+)\s*=\s*("[^"]*"|'[^']*')/g)` -> `{}` ACs []

## Reviews that led to a fix pass (none)

## Findings and proofs (final review)
Findings:
- F1 [high, conf 90] tools/build-dictionary.mjs:39 The field regex /<(?:[\w-]+:)?field\b([^>]*?)>/g scans the whole document, including inside <codeSet> blocks, but the codeSet regex only consumes codeSet conten
- F3 [medium, conf 80] test/dictionary.test.js:28 test_dictionary_tests_register_at_top_level asserts `source.match(/^test\s*\(/gm)` has length >= 6, but the file registers the top-level tests without a leading
- F4 [medium, conf 75] test/dictionary.test.js:24 test_dictionary_unknown_inputs_return_null calls `expect(lookup(version, 35)?.name).toBe('MsgType')` twice in a row (lines 26 and 27), leaving the actual tagged

Proofs:
none

Decision: {'blocking': [], 'blocking_unproven': [], 'notes': ['F1', 'F3', 'F4']}

## Fix pass
pass 1 (gates)

## Hidden acceptance suite
Hidden acceptance suite on trusted main `0acbcbff61`: **22/42** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 0 | 4 | module did not import (feature not built yet?) |
| acc-dictionary.test.js | 4 | 4 |  |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 0 | 3 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 0 | 9 | module did not import (feature not built yet?) |

Newly passing: 3. No regressions.

## Implementer, finder and Codex use
- **Implementer: `gpt-6-sol` (openai-codex), first pass and fix pass. No fallback.** Codex use: implementer 2 sessions, 49 calls, 102,144 in / 12,561 out; planner 1 session, 10 calls, 37,005 in / 3,720 out. No rate-limit message seen.
- **Finder: `deepseek-flash`**, one session.
- **Against the Qwen tickets:** first-attempt gates failed (AC4), one gate fix pass, no review pass; no blocking finding (notes F1, F3, F4); hidden suite after landing 22/42, `acc-dictionary` 4/4, no regressions.
- **Operator note:** the mutation line (killed 0, survived 83, in 1.5 s) says nothing about test quality either way; the mutated file is the build script, and I have not checked why no mutant is killed. **F1 (high, a note, unproven)** is about the dictionary build's field regex also scanning inside `<codeSet>` blocks; worth a look although the hidden dictionary tests pass.
- A person-approved fix-pass edit to `test/dictionary.test.js`: see FXL-3B-block.md.

## Independent check of F1 (FXL-3B-landed-review.md)
A Python standard-library extractor using `xml.etree` (only the `field` children of `repository/fields`, only the `codeSet` children of `repository/codeSets`), run on the vendored XML and compared with the committed JSON, all read with `git show` from the trusted `main` (`e4aef93`, which is after FXL-4; scratch folder outside the repo, read-only).

| version | fields, independent / committed | fields with enums | enum entries | only on one side | tags with a different name, type or enums |
|---|---|---|---|---|---|
| FIX 4.2 | 405 / 405 | 111 / 111 | 654 / 654 | none | **0** |
| FIX 4.4 | 912 / 912 | 274 / 274 | 2371 / 2371 | none | **0** |

**Identical: F1 is a false alarm on these files.** The regex is still not a parser (a differently shaped XML file could break it), but the committed dictionary is right. No duplicate field ids or code-set names.
**Timing:** the review arrived after FXL-4 had already run and landed, so no hold was placed.
**Mutation:** I did not test your `execSync` explanation.
