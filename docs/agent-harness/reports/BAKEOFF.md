# BAKEOFF: token-plan implementers against FXL-1B (BAKEOFF-review.md)

Ten runs, two per model, same inputs: FXL-1B's ticket text, the loader's implementer card body (paths rewritten to the scratch folders), and Codex's `plan.json` from attempt 3. Base `f36221c`. No Claude was used. The live implementer profile was not changed.

## Results

| run | gates, first time | missing_acs | acc-framing | acc-check | base test files touched | minutes | API calls | input tok | output tok | cache-read tok |
|---|---|---|---|---|---|---|---|---|---|---|
| qwen4-max #1 | **passed** | none | 9/9 | 5/9 | framing-f2, framing | 8.2 | 31 | 96,861 | 47,143 | 1,831,424 |
| qwen4-max #2 | **passed** | none | 9/9 | 5/9 | framing-f2, framing | 7.7 | 28 | 89,530 | 42,769 | 1,501,696 |
| qwen3.8-max #1 | **passed** | none | 9/9 | 5/9 | framing-f1, framing-f2, framing | 27.6 | 23 | 114,907 | 67,260 | 1,448,320 |
| qwen3.8-max #2 | **no result** (timed out, nothing committed) | n/a | n/a | n/a | none committed | 30.0 | 12 | 112,890 | 69,668 | 453,120 |
| qwen3.7-max #1 | **passed** | none | 9/9 | 5/9 | framing-f2, framing | 5.1 | 30 | 124,991 | 24,076 | 1,212,032 |
| qwen3.7-max #2 | **passed** | none | 9/9 | 4/9 | framing-f2, framing | 7.6 | 24 | 143,339 | 49,658 | 1,327,360 |
| deepseek-v4-pro #1 | **passed** | none | 9/9 | 5/9 | framing-f2, framing | 12.8 | 37 | 77,193 | 29,815 | 1,820,416 |
| deepseek-v4-pro #2 | **passed** | none | 9/9 | 5/9 | framing-f2, framing | 13.6 | 40 | 84,316 | 36,173 | 1,831,936 |
| glm-5.3 #1 | **passed** | none | 9/9 | 5/9 | framing-f1, framing-f2, framing | 20.5 | 56 | 174,835 | 112,980 | 6,351,360 |
| glm-5.3 #2 | **passed** | none | 9/9 | 5/9 | framing-f1, framing-f2, framing | 21.3 | 39 | 168,969 | 118,068 | 4,535,808 |
| *reference:* gpt-6-sol, attempt 3 first pass (`3bb9a7e`) | **passed** | none | 9/9 | 5/9 | framing-f2, framing | about 3 | 19 | 72,297 | 6,192 | 987,136 |
| *reference:* base `f36221c`, no change | n/a | n/a | 4/9 | 4/9 | n/a | | | | | |

Earlier live record: `qwen3.7-plus` did not land FXL-1B in two attempts. Attempt 1 was stopped by a harness bug (the gates saw a cut-off test list, D11), so only attempt 2 says something about the model: it passed the gates, and the reviews then proved bugs twice. Every session in the table used only the named model on `alibaba-token-plan` (checked in `state.db`; the profiles had no fallbacks).

## What the numbers say
- **9 of 10 runs passed the gates first time, all with `acc-framing` 9/9.** That is what Codex's first pass scored.
- **`acc-check`:** 8 runs scored 5/9, the same as Codex's first pass. The four checks they all fail (CheckSum over SOH, a pipe-byte CheckSum, UTF-8 BodyLength, missing CheckSum) all fail at the base and passed after FXL-2B; they are not this ticket's work, and Codex fails them at this point too. A fifth, "CheckSum that is not 3 digits", also fails at the base: every other scored run and Codex fixed it, **`qwen3.7-max` #2 did not (4/9)**.
- **`qwen3.8-max` is the weak one on time:** 27.6 minutes on run 1 and a 30-minute timeout on run 2, with a new test file written and nothing committed.
- **Speed:** Codex about 3 minutes. `qwen3.7-max` 5.1 and 7.6, `qwen4-max` 8.2 and 7.7, `deepseek-v4-pro` 12.8 and 13.6, `glm-5.3` 20.5 and 21.3.
- **Tokens:** every candidate used more than Codex's pass; `glm-5.3` wrote about 18 times as much output.

## What this does not show
- **The gates and these two hidden files do not measure what made Qwen fail live.** In live attempt 2, `qwen3.7-plus` passed the gates and the **review** then proved bugs. Codex's own first pass also passed the gates, scores 9/9 on `acc-framing` here, and its review then proved four bugs. This bake-off ran no review, so a candidate that ties Codex here may still differ a lot in review findings. A fairer next step would be one review of each of the best one or two candidates' heads.
- `acc-framing` is saturated (everyone 9/9), so it cannot rank them. Two runs per model is a small sample.
- Every candidate had **Codex's plan**. None was tested as a planner, or without that plan.

## Odd things, and the conditions
- **No loops or kanban calls** (0 kanban tool calls in every run).
- **Reading outside the scratch folders:** several runs went looking for the technical design, which the ticket cites and they could not read (`qwen3.8-max` #2 ran `find /` for it). All of those searches ran before my reading copies existed (created 22:32:30); the one run still going then, `glm-5.3` #2, did not open it. `qwen3.8-max` read the harness's own `docs/DESIGN.md` and `BUILD_SPEC.md` (root-owned, read-only). `deepseek-v4-pro` #2 listed `work/bake`, which held only its own folder. I found no access to the live `work/fix-lens`, `work/runs`, `work/prove` or any hidden test file, searching the tool calls for those paths and relative forms; that is a text search, not a filesystem audit.
- **Isolation:** each clone held history only up to the base; finished runs were moved to a host-only folder before the next began. The hidden files were run **in a separate throwaway container with no network** (same image and dependencies), not with `harness.score` in the live container, so that live FXL workers could never see them. Gates ran with `harness.gates` in the live container as asked, with a copy of the config with `require_trusted_main = false`.
- `qwen3.8-max` #1 was paused for a few seconds while I scored FXL-3B's hidden suite, so its minutes are very slightly high. The other runs shared the machine with the live pipeline.
- Tokens are `state.db` sums for the run's sessions. Plan-token cost is not shown by `state.db` (it reads $0).
