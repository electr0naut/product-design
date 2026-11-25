# Phase C run 2: result (PRC-5 not approved: stale base)

Run 2: started 2026-11-25 17:35 CET, fresh fixture repo (`b13172e`) and fresh trusted repo, planner on Qwen (Codex limit). Kit at `agent-harness@bd64da6` at the time of writing (three mid-run fixes, below). Scored with `python -m harness.score` (hidden tests against the **trusted** main, in the container).

## Score
| Hidden file | Pass |
|---|---|
| test_prc_1 | 6/6 |
| test_prc_2 | 4/4 |
| test_prc_3 | 4/4 |
| test_prc_4 | 5/5 |
| test_prc_5 | 0/3 (module not on trusted main) |
| **Total** | **19/22** (target 22/22); baseline tests 22/22 |

Trusted main: `45db90f` PRC-1, `6702730` PRC-2, `bcba135` PRC-3, `fd8de01` PRC-4. PRC-6 blocked at triage as intended.

## Why PRC-5 is not in
PRC-5's review was clean (no findings), but approval blocked: `trusted main (fd8de01) is not the ticket's base (bcba135)`. PRC-5 started right after PRC-3 merged, while PRC-4 was still in flight; PRC-4 was approved first, so PRC-5's base went stale. The check did its job (a fast-forward onto a stale base would drop PRC-4), but the schedule produces this whenever two tickets run concurrently.
**Question for the reviewer (design):** what should happen to a ticket whose base is stale but which merges cleanly? Options: (a) rebase `harness/PRC-5` onto the trusted main on the host (in the trusted repo), then re-run gates and review on the new head, as an explicit pipeline step; (b) serialize tickets (one open ticket at a time, which costs wall time); (c) re-run the ticket from the new main. I changed nothing; the card stays blocked.

## Mid-run fixes (all pushed, tests added)
| Block | Cause | Fix |
|---|---|---|
| PRC-3 reviewer: `missing 'findings'` | Qwen's first reply was the findings **schema echoed back** (confirmed in `find-raw-1.txt` of PRC-5, which did the same) | parse every object, take the first that validates; save raw replies; one re-ask (`9b497cb`). PRC-5 used the re-ask and then returned `{"findings": []}`. PRC-3 passed first time on retry |
| PRC-4 gatekeeper: argparse error | my card text ended the command with a stray ` .` that the worker passed literally | removed (`632bdc7`), card bodies for PRC-4/5/6 edited |
| score: 0/0 | a missing module aborted collection | per-file results, unimportable modules count as 0 (`bd64da6`) |

## Per ticket (run 2)
| Ticket | Stage wall time (s) | Blocks | Findings | Claude | Gates | resolved_ids |
|---|---|---|---|---|---|---|
| PRC-1 | triage 99, plan 135, impl 140, gates 36, review 38, scribe 64 | 0 | 0 | $0 | pass | none |
| PRC-2 | 66, 165, 162, 43, 24, 70 | 0 | 0 | $0 | pass | none |
| PRC-3 | 72, 144, 157, 34, 110 (+136 failed run), 120 | 1 (finder reply) | 0 | $0 | pass | none |
| PRC-4 | 87, 177, 178, 23 (+37 failed run), 112, scribe running | 1 (card text) | 0 | $0 | pass | none |
| PRC-5 | 84, 167, 118, 20, 59 | 1 (stale base) | 0 | $0 | pass | none |
| PRC-6 | triage 60, blocked | 1 (intended) | n/a | $0 | n/a | n/a |

Wall time so far: about 60 minutes of pipeline time, 18:35 CET at the time of writing. Claude spend this run: $0 (no review had findings). Models per stage and DeepSeek usage are not read out yet (the container's per-profile `state.db` has them; no extraction tool yet).

## False blocks
0 in run 2 (run 1 had one, PRC-3, which the refuter now clears with Read access, $0.31). No review produced a finding at all in run 2, so refute/prove were not exercised on real tickets this time.

## Open
- PRC-4 scribe was still running when this was written.
- The PRC-5 stale-base decision above.
- Qwen ran a scratch script during PRC-3's first review (`profiles/reviewer/cache/scratch/verify_ac.py`): the finder profile has tools and used them. Harmless here, but the finder is meant to read a diff only.
- Per-stage model attribution and DeepSeek cost, plus the DESIGN section 12 comparison, once the PRC-5 question is settled.
