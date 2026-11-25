# Phase C final: 22/22 hidden tests

Fixture repo and trusted repo both fresh. Kit `agent-harness@573a163` (final). Run 2: PRC-1 to PRC-6 loaded together 2026-11-25 17:35 CET; PRC-5 re-run alone after the serialization change (rerun finished 18:53). Planner on Qwen (Codex limit until 2026-11-26 08:21 CET; one Codex planner check is still to do). All numbers below come from `python -m harness.score`, `work/runs/*/review.json`, `gates.json`, and `python -m harness.usage` (new, read-only, from the per-profile `state.db`).

## Score
| Hidden file | Pass |
|---|---|
| test_prc_1 | 6/6 |
| test_prc_2 | 4/4 |
| test_prc_3 | 4/4 |
| test_prc_4 | 5/5 |
| test_prc_5 | 3/3 |
| **Total** | **22/22**; baseline (existing + implementers' tests) **25/25** |

Trusted `main`: `45db90f` PRC-1, `6702730` PRC-2, `bcba135` PRC-3, `fd8de01` PRC-4, `6cb01d4` PRC-5, each fast-forwarded by the host runner only after a clean review. PRC-6 bounced at triage (no baseline for "faster"), as designed. Scoring ran on the trusted main, not on the work repo.

## Per ticket
| Ticket | Stage seconds (triage / plan / implement / gates / review / scribe) | Blocks | Findings | Claude | Gates | resolved_ids |
|---|---|---|---|---|---|---|
| PRC-1 | 99 / 135 / 140 / 36 / 38 / 64 | 0 | 0 | $0 | pass | none |
| PRC-2 | 66 / 165 / 162 / 43 / 24 / 70 | 0 | 0 | $0 | pass | none |
| PRC-3 | 72 / 144 / 157 / 34 / 110 (+136 failed) / 120 | 1 | 0 | $0 | pass | none |
| PRC-4 | 87 / 177 / 178 / 23 (+37 failed) / 112 / ~120 | 1 | 0 | $0 | pass | none |
| PRC-5 (rerun) | 95 / 123 / 141 / 18 / 27 / 84 | 0 (1 in the first attempt) | 0 | $0 | pass | none |
| PRC-6 | triage 60, blocked | 1 (intended) | n/a | $0 | n/a | n/a |

Fix loops: 0. Human blocks needing a decision: 3 (PRC-3 reviewer, PRC-4 gatekeeper, PRC-5 stale base), all pipeline defects, all fixed in the kit; PRC-6 is the intended bounce.

## Models and cost (since 17:35 CET, `harness.usage`)
| Profile | Model (provider) | Sessions | API calls | Input tok | Output tok | Cost USD |
|---|---|---|---|---|---|---|
| triage | qwen3.7-plus (alibaba-token-plan) | 7 | 65 | 208,993 | 24,267 | 0 (plan) |
| planner | qwen3.7-plus | 6 | 85 | 404,307 | 42,320 | 0 (plan) |
| implementer | qwen3.7-plus | 6 | 121 | 433,344 | 35,806 | 0 (plan) |
| gatekeeper | deepseek-flash (deepseek) | 7 | 61 | 56,087 | 19,154 | 0.0246 |
| reviewer (finder) | qwen3.7-plus | 9 | 34 | 127,870 | 23,360 | 0 (plan) |
| scribe | deepseek-flash | 5 | 134 | 122,732 | 65,693 | 0.0737 |

DeepSeek total **$0.098**. Claude: **$0** in run 2 (no review had findings; the earlier $0.31 PRC-3 refuter re-check and the $1.94 + $0.66 variant runs are separate). Codex: none (rate-limited). Wall time: 4,708 s (78 min) from first load to the last scribe, including the stalls and my fixes; the pipeline's own stage time for the five tickets is about 40 min of agent time.

## Against DESIGN section 12
| Metric | Target | Result |
|---|---|---|
| Correctness | 5/5 on the fixture | **5/5** tickets (22/22 tests) |
| Regressions | 0 | **0** (baseline 25/25) |
| Cost per merged ticket | 30% below baseline | $0.02 DeepSeek per ticket, Claude $0; the `baseline` profile was **not run**, so no ratio |
| Haiku share | 100% in pipeline mode | **not applicable**: this build uses Qwen/DeepSeek, not Haiku |
| Review recall | at least 5/6 | **6/6** (B-variants, B6 run) |
| False blocks | 0/4 on clean variants | **0/4**; on real tickets 1 in run 1 (PRC-3, refuter lacked context; now refuted with Read access), 0 in run 2 |
| Test economy | at most 2 new tests per criterion; FAIL_TO_PASS at least 0.8 | gates passed on all five; not aggregated |
| Mutation survivors | reported | not run in this build |
| Wall time | tiered <= baseline | no baseline run |
| Escalations | reported | 3 pipeline-defect blocks (above), 1 intended bounce |

## What went wrong on the way (all fixed, in the kit, with tests)
Run 1: a worker merged unreviewed PRC-3 into `main` (host-only trusted main, branch-lineage gates, refuter with Read, host never runs git in a work repo, finder tools removed). Run 2: finder echoed the schema (first valid object, raw replies saved, one re-ask), gatekeeper card ended in a stray `.`, PRC-5's base went stale (tickets now serialized: each triage waits for the previous scribe).

## Open
- **Bounced tickets hold the queue.** With serialization a triage-bounced ticket blocks every later ticket. The loader cannot know at load time which ticket will bounce, so the review's "independent later ticket still runs" case is not met; PRC-6 is last in the fixture so it did not matter. Options for the reviewer: queue vague tickets last, or an explicit `--skip` for a bounced ticket.
- **Planner on Codex:** one run after 2026-11-26 08:21 CET.
- **Gatekeeper into deterministic code** (post-Phase C, per the review).
- **Prove worktree symlink race** (review's residual note), not closed.
- **Nightly backup check** of the 03:00 run, output in `cron/output/50fbaafad58b/` (not read yet today).
- **Telegram:** `notify-subscribe` has no per-event filter, so every stage card pings on completion as well as problems.
