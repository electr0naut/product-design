# BAKEOFF round 2: FXL-5 as first written, scored by the 14 hidden timeline tests (BAKEOFF-round2-review.md, review2)

Twelve runs, six models, two each. Same inputs for all: `FXL-5.md` as it was before AC11 to AC15 (`25a216c^`), the first attempt's `readiness.json`, base `e4aef93`, the design readable, **no plan**. No fallbacks. No Claude. No live profile changed. **Every model could work without a plan:** all 12 runs committed and passed the gates.

## Per run
| run | gates, first time | acc-timeline | failing tests | base test files touched | minutes | API calls | input tok | cached input tok | output tok | of which reasoning tok |
|---|---|---|---|---|---|---|---|---|---|---|
| gpt-6-sol (reference) #1 | passed | 14/14 | none | none | 3.3 | 20 | 34,086 | 573,696 | 8,043 | 1,168 |
| gpt-6-sol (reference) #2 | passed | 14/14 | none | none | 2.9 | 17 | 35,733 | 457,600 | 6,553 | 573 |
| gpt-6.2-sol #1 | passed | 14/14 | none | none | 2.6 | 12 | 74,704 | 215,552 | 6,290 | 259 |
| gpt-6.2-sol #2 | passed | 14/14 | none | none | 2.8 | 14 | 81,175 | 257,792 | 6,938 | 482 |
| deepseek-v4.1-flash-1017 #1 | passed | 14/14 | none | none | 2.5 | 17 | 51,452 | 609,408 | 24,654 | 14,864 |
| deepseek-v4.1-flash-1017 #2 | passed | 14/14 | none | none | 3.6 | 29 | 61,426 | 1,131,008 | 33,829 | 21,459 |
| qwen4-max #1 | passed | 14/14 | none | none | 5.3 | 18 | 70,116 | 835,072 | 30,511 | 18,346 |
| qwen4-max #2 | passed | 14/14 | none | none | 7.3 | 24 | 65,084 | 1,117,696 | 33,613 | 19,860 |
| qwen3.7-max #1 | passed | 13/14 | **34 missing** | none | 5.2 | 19 | 105,002 | 722,432 | 30,024 | 12,493 |
| qwen3.7-max #2 | passed | 13/14 | **34 missing** | none | 3.6 | 27 | 190,576 | 837,760 | 20,406 | 6,889 |
| deepseek-v4-pro #1 | passed | 12/14 | **34 missing**; **bad NewSeqNo** | none | 13.5 | 31 | 79,993 | 1,550,848 | 36,072 | 11,926 |
| deepseek-v4-pro #2 | passed | 13/14 | **bad NewSeqNo** | none | 7.8 | 23 | 53,497 | 805,120 | 19,660 | 6,769 |

- **34 missing** = "a message without a usable 34 changes nothing, even a Logon with 141=Y".
- **bad NewSeqNo** = "a NewSeqNo that is not a positive integer falls back to 34 + 1".
- Base (`src/timeline.js` does not exist there) has nothing to score.
- The token columns are what Hermes stored in `state.db` from the providers' usage replies (`input_tokens`, `cache_read_tokens`, `output_tokens`, `reasoning_tokens`). I did not check them against a provider bill. The reasoning column is shown as stored; I have not verified whether each provider already counts it in output.
- **Plan quota:** I found no credit, request or quota figure for the Alibaba token plan in `state.db` (cost is `unknown`) or in the bake-off profiles' logs, and I did not open the provider's console. So there is no consumption column.

## Per model (mean per run for tokens)
| model | acc-timeline, two runs | minutes | input tok | cached input tok | output tok |
|---|---|---|---|---|---|
| gpt-6-sol (reference) | 14, 14 | 3.3, 2.9 | 34,909 | 515,648 | 7,298 |
| gpt-6.2-sol | 14, 14 | 2.6, 2.8 | 77,939 | 236,672 | 6,614 |
| deepseek-v4.1-flash-1017 | 14, 14 | 2.5, 3.6 | 56,439 | 870,208 | 29,241 |
| qwen4-max | 14, 14 | 5.3, 7.3 | 67,600 | 976,384 | 32,062 |
| qwen3.7-max | 13, 13 | 5.2, 3.6 | 147,789 | 780,096 | 25,215 |
| deepseek-v4-pro | 12, 13 | 13.5, 7.8 | 66,745 | 1,177,984 | 27,866 |

- **gpt-6-sol:** 14/14 twice, about 3 minutes, the fewest uncached input tokens of any model.
- **gpt-6.2-sol:** 14/14 twice, the fastest on average (2.6, 2.8); about twice gpt-6-sol's uncached input, less than half its cached input, and the fewest output tokens.
- **deepseek-v4.1-flash-1017:** 14/14 twice in 2.5 and 3.6 minutes: the best token-plan result here.
- **qwen4-max:** 14/14 twice, in 5.3 and 7.3 minutes.
- **qwen3.7-max:** 13/14 twice, the same miss (34 missing) both times; the most uncached input.
- **deepseek-v4-pro:** 12/14 and 13/14, and the slowest (13.5, 7.8).

## The question: is qwen4-max worth it as first fallback?
On this ticket, **`deepseek-v4.1-flash-1017` did the same work as well, faster and on somewhat fewer tokens**:

| per run, mean | minutes | input | cached input | output |
|---|---|---|---|---|
| deepseek-v4.1-flash-1017 | 3.0 | 56,439 | 870,208 | 29,241 |
| qwen4-max | 6.3 | 67,600 | 976,384 | 32,062 |

The time difference is clear; the token difference is small next to the spread between two runs of one model, and **tokens are not plan credits**: the plan may price these two models differently, which I could not see. The recommendation is yours and the decision is Ubay's.

## What this does and does not show
- **Four of six models scored 14/14 twice,** so this test separates only the other two. It cannot rank the top four on quality.
- **No review was run.** On live tickets, heads that passed the gates still had bugs proven in review.
- Two runs per model, one ticket.
- **Conditions that differ from live:** the prompt named the design's path (live cards do not yet; D16), and there was no planner. Several runs opened the `hermes` user's copy of the design instead of their own profile's; the two are identical.

## Isolation and access
- Each clone held history only up to the base; finished runs were moved to a host-only folder before the next began. Gates ran in the live container with `require_trusted_main = false`; the hidden file ran only in a separate no-network container.
- **Tool calls:** no kanban call; no path or relative path to `work/prove`, `work/runs`, `work/fix-lens`, `work/old` or `work/scratch`, and no `acc-*.test` name. Some runs ran `find` under `/srv/lab/agent-harness` or `/` for config files or the design, and some read the harness's own `harness.toml` files (read-only).
- **Exposure:** the first eight runs went on beside FXL-8, and one (`deepseek-v4-pro` #2) was active while the live pipeline's own scoring had hidden files under `work/prove` (23:44). The last four ran with no live ticket. See `AUDIT-hidden-suite.md`. Its search ran before the last runs had finished, so I repeated it on the complete copies of all six round 2 session databases: no hidden code line, hidden path or file name; the only distinctive title is the `deepseek-v4-pro` comment the audit explains.

## Deleted and kept (my own, from this job)
Deleted after scoring: the six Hermes profiles `bake-r2-qwen4-max`, `bake-r2-qwen3-7-max`, `bake-r2-deepseek-v4-pro`, `bake-r2-codex`, `bake-r2-deepseek-v4-1-flash`, `bake-r2-codex62`; the scratch folder `work/bake/`; my scripts in the container's `/tmp`. **Their session databases were copied first** to `~/.local/state/agent-harness-bake/audit/sessions/` on the host, so this round stays auditable (round 1's were not kept). Kept on the host: the clones, logs, scripts and results under `~/.local/state/agent-harness-bake/r2/`.
