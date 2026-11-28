# D27 second bake-off: spec pass and prove (D27-proposal-review)

Short report (the VM session hit its usage limit while writing it). Raw replies and script: `D27-bakeoff2/`.

**Setup:** two throwaway profiles, no `fallback_providers`, `tools.tool_search.enabled = off`, `-t context_engine`. Hermes's own `get_tool_definitions` lists **no tool** for this (the wire request was not captured). 23 sessions each: `tool_call_count` 0, no message with a tool call, intended model on all (one `qwen3.7-plus` session has no provider recorded), no "Fallback activated". **Both profiles deleted.** Sources were given in the prompt (largest about 114,000 characters); no hidden test in any prompt. Model tests ran in a no-network container on the buggy and fixed commits. Control: Claude's five recorded proof tests all failed on the buggy state and passed on the fixed one. FXL-1 had no design file or spec pass at the time: ticket only. The runs overlapped FXL-19 to FXL-21.

| | `qwen4-max` | `qwen3.7-plus` |
|---|---|---|
| prove: 5 proven bugs, 2 runs: test fails on buggy, passes on fixed | **10 of 10** | **1 of 10**; the other 9 filled `could_not_prove_because` (mostly "no tools to run it"), which counts as no test, as in production. **Their test source was not run**, so its quality is unknown |
| spec pass, FXL-1B's 3 spec-found bugs, reaching the review (run 1 / run 2). My matching, by reading the claims | **3 / 2** (run 2 found the third; the line filter dropped it) | **0 / 0** (run 1 found the prefix bug; its quote was not verbatim, so dropped) |
| spec pass, FXL-1's proven bug | reached in both runs | run 1 missed; run 2 found, dropped (quote) |
| seven clean v1.2 reviews, one run each | 0 findings | 0 findings |
| rejected replies | 0 of 21 | 2 of 23 (one exit 1, one wrong shape) |
| seconds per call: median / mean / p90 / max | 36 / 80 / 164 / 321 | 110 / 198 / 509 / 789 |

`qwen4-max` also reported other findings on the buggy states (see raw results); I have **not** judged them. Limits: two buggy states, one codebase; zero findings on "clean" states does not show they have no defect (the validation found some in v1.2).

**Reading:** `qwen4-max` is clearly ahead on both steps. For the build: tell the model that not being able to run the test is no reason to fill `could_not_prove_because`. The model choice is Ubay's.
