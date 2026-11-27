# D27 part 2 bake-off: `qwen4-max` and `qwen3.7-plus` on 32 recorded findings

**What this measures: the refute step only.** The spec pass (which *finds* deviations) and the prove step (which decides what blocks) were **not** replayed. Free on the token plan; nothing live changed.

## How
- **Cases:** every finding in the recorded reviews: FXL-9 to FXL-18 (12 findings, in FXL-9, 15 and 16; the other seven reviews had none) and the earlier reviews (20, FXL-1, whose review led to a fix pass, and FXL-1B's two among them). Each at the commit that was reviewed (the matching `gates*.json`). For FXL-9, 15 and 16 the run files equal the host's trusted records; the earlier ones come from the run folders only.
- **Prompt:** `Runner.refute`'s, with one change: no Read tool; instead the sources at that commit are in the prompt (all of `src/` but the generated dictionaries, `index.html`, `package.json`, the finding's own file). 14 to 45 thousand characters. Claude could also read tests and anything else.
- **Models:** two throwaway profiles cloned from `triage`, the model set, **`fallback_providers` removed**, `chat --oneshot -t todo --ignore-rules`. All 95 sessions (one smoke call each included) ran on the intended model; no "Fallback activated" line. One failed session has no provider recorded. **Both profiles and the empty work folder are deleted;** the 27 earlier profiles are there.
- Replies checked against the kit's `refutations` schema; one re-ask. One run of all 32, and **a second run of the 12 from v1.2**.
- Script, scoring and every raw reply: `reports/D27-bakeoff/`.

## Tools: check this one
`qwen3.7-plus` made no tool call. **`qwen4-max` made 30:** 29 `tool_search` ("read file source", "run javascript node test", ...) and one `tool_describe` of `todo_list`. Every search found one tool available, the to-do list, and matched nothing; the list itself was never called. **Nothing read a file, ran a command or left the model call.** So `-t todo` is not "no tools", and this model goes looking.

## Against Claude's recorded verdict
| | `qwen4-max` | `qwen3.7-plus` |
|---|---|---|
| same verdict, all 32 | **30** (the others: Claude `unsure` → `stands`; one with no verdict) | **27** |
| same, the 12 of v1.2 (Claude: all `refuted`) | 12, and 12 again in run 2 | 11 (`FXL-16` F4 `stands`); run 2: 11 (`FXL-9` F3 `stands`) |
| changed between the two runs | 0 of 12 | **2 of 12** |
| **would let through what Claude blocked** (5 findings, all proven; model says `refuted`) | **none** | **none** (one, FXL-1B F3, `unsure`: still goes to a proof) |
| high/critical Claude refuted, model did not (so it **goes on to a proof**) | none | FXL-7 F2 (**a real one**); in run 2, FXL-9 F3 (a wrong one) |
| would block outright (`blocking_unproven`: `stands` at confidence 80 or more with no test written) where Claude cleared | none | none (the two above are at 75 and 60) |

The v1.2 row says little by itself: **answering `refuted` every time would score 12 of 12.** The 13 `stands` among the older ones are what tell them apart from that.

## Against what happened
I could judge 20 findings from your landing reviews and the proof results: **12 real, 8 wrong** (wrong: all five of FXL-16, FXL-3B F1, FXL-9 F3 and F4). **12 are not judged** (FXL-15 F1, F2; FXL-1B round 1 F1, F3; FXL-2 F1, F2; FXL-2B F1; FXL-3B F3, F4; FXL-5 F1; FXL-7 F1, F3).
| | on the 12 real: stands / refuted / other | on the 8 wrong: refuted / stands |
|---|---|---|
| Claude | 8 / **4** / 0 | **8** / 0 |
| `qwen4-max` | 7 / **4** / 1 no verdict | **8** / 0 |
| `qwen3.7-plus` | 8 / **3** / 1 unsure | **7** / 1 (FXL-16 F4, medium) |

All three refuted FXL-9 F1, F2 and FXL-15 F3, which you called true (F1, F2 "true and small"). **Agreeing with Claude includes agreeing with these.** FXL-7 F2 is the one real finding only `qwen3.7-plus` kept.

## Malformed answers and time
| | `qwen4-max` | `qwen3.7-plus` |
|---|---|---|
| replies rejected | 2 of 45 (no JSON, FXL-8 F1, both tries: **no verdict**; in service the card would wait for Claude) | 4 of 48 (3 wrong shape; 1 call exit 1 after 335 s: the model "fell into a repetition loop" and the stream was stopped); all recovered on the re-ask |
| seconds per call: median / mean / 90th / worst | 41 / 44 / 67 / **90** | 41 / 71 / 131 / **358** |

Plan consumption is not shown by `state.db` (as in the earlier bake-off).

## Limits
- **Refute only** (above). Of FXL-1B's four proven bugs, three came from the spec pass.
- **Not independent for some early cases:** `qwen3.7-plus` was the finder in FXL-1 (so there it judged its own model's finding), and one of two finder models in the FXL-1B and FXL-2 evidence; their `find` findings may be its own. The v1.2 findings come from `deepseek-flash`.
- One codebase, small enough to put whole in the prompt. One run for 20 findings. "Real" and "wrong" are your judgements or a failing test; I made none of my own.
- On your wider question (about $9 notional in v1.2, no finding proven; the ten records sum to $9.06): all three refuted all 12. This says nothing about whether another model would **find** better.

## My reading (the choice is Ubay's, on your recommendation)
On this step `qwen4-max` is the better of the two: closer to Claude, no change on repeat, no wrong finding upheld, a far shorter worst case, and eligible on more tickets (`D27-proposal.md`). Against it: it hunts for tools, and one finding got no verdict. **I would not choose on this alone:** the spec pass and prove are untested and can be replayed the same free way.
