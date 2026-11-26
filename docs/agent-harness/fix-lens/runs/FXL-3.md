# FXL-3: BLOCKED for a human

## FXL-3 · planner (t_702a1690) is blocked
```
  [2026-11-26 01:39] promoted
  [2026-11-26 01:39] [run 228] claimed {'lock': 'ailab:149916', 'expires': 1795654494, 'run_id': 228}
  [2026-11-26 01:39] [run 228] spawned {'pid': 277249, 'started_at': '5cbd1797-904c-4b65-9ecb-a7b2ae61c3ca:514|14249951'}
  [2026-11-26 01:39] [run 228] owner_admitted {'db': '/opt/data/profiles/planner/state.db', 'session_id': 'local-dfef03a1a1c6c321dbec4506de4237b0b061f87c622e6321fc4a28d3dfa35cbc', 'request_id': 'kanban:["default","t_702a1690",228]', 'pid': 149916, 'birth': 125302.57}
  [2026-11-26 01:39] [run 228] worker_bound {'pid': 277255, 'claim_lock': 'ailab:149916', 'started_at': '5cbd1797-904c-4b65-9ecb-a7b2ae61c3ca:514|14250107'}
  [2026-11-26 01:40] [run 228] heartbeat
  [2026-11-26 01:41] [run 228] heartbeat
  [2026-11-26 01:42] [run 228] heartbeat
  [2026-11-26 01:43] [run 228] heartbeat
  [2026-11-26 01:43] [run 228] blocked {'reason': 'Cannot write plan.json to /srv/lab/agent-harness/work/runs/FXL-3/plan.json. The write_file tool is blocked by HERMES_WRITE_SAFE_ROOT=/opt/data, and the task requires writing to /srv/lab/agent-harness/work/runs/FXL-3/ which is outside that path. The execute_code tool is also blocked in single-query mode. The plan is complete and covers all 6 acceptance criteria, but I cannot write it to the required location with the available tools.', 'kind': 'capability', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #228 blocked      @planner  190s  2026-11-26 01:39
        → Cannot write plan.json to /srv/lab/agent-harness/work/runs/FXL-3/plan.json. The write_file tool is blocked by HERMES_WRITE_SAFE_ROOT=/opt/data, and the task req
```

Run files: readiness.json, repo.txt

## Run summary
Fix pass: none

## Diagnosis (read-only; nothing was changed or unblocked)
**FXL-3 did not fail on its ticket: its planner blocked itself because the file tool refused the path.** The planner had a finished plan (its summary says it covers all 6 acceptance criteria) but could not write `plan.json`.
- The planner's session (`state.db`, read-only): `write_file` to `/srv/lab/agent-harness/work/runs/FXL-3/plan.json` returned `Write denied: ... is outside HERMES_WRITE_SAFE_ROOT (/opt/data)`; it then tried `execute_code` (which says it is blocked in single-query mode) and called `kanban_block`, **without** trying the terminal tool. A few terminal attempts follow the block call in the transcript; the run was already blocked and `plan.json` was never written (`work/runs/FXL-3/` holds only `readiness.json` and `repo.txt`).
- **This restriction is not new.** The container has `HERMES_WRITE_SAFE_ROOT=/opt/data` (its config and the gateway have not changed since 2026-11-25 20:51 and 20:53). Counting `write_file` results that say "outside HERMES_WRITE_SAFE_ROOT" per profile since yesterday evening: the planner has them in **6 sessions** (25th 18:43, 20:57, 23:39, 23:49, 26th 01:00, 01:39), triage in 6, the implementer in 6 and the scribe in 6, so almost every worker session hits it at least once. Normally the worker works around it: FXL-1's planner wrote `write_plan.py` under `/opt/data/profiles/planner/cache/scratch/` with `write_file` (inside the safe root) and ran it with the terminal tool, which wrote `plan.json` (5 174 bytes). FXL-3's planner did not.
- **The card text makes this worse:** every stage card says "Write files with the file-writing tool, never with shell redirection or heredocs", which is exactly what the safe root forbids for `/srv/lab` paths, so each worker has to discover the workaround alone; some sessions lose turns on it and this one gave up.
- Block details: card `FXL-3 · planner` (`t_702a1690`) is `blocked` with the reason above; no other FXL-3 card has run. FXL-1's card is still blocked too. The trusted `main` is still `544c8c5`, so nothing has landed from either ticket.

## What would fix it (for the reviewer or the user to choose; I did none of these)
1. **Card text (a kit change, needs a review and a deploy, so not tonight's running system):** replace the "file-writing tool only" line with the real rule: "`write_file` is limited to `/opt/data`; to create a file in the work folder, write a short Python script under `/opt/data/profiles/<your profile>/cache/scratch/` with `write_file` and run it with the terminal tool; never use `execute_code`".
2. **A wider write root for workers:** add `/srv/lab/agent-harness/work` to `HERMES_WRITE_SAFE_ROOT`. That is a Hermes/container environment change (a stop for the user), and it widens what a worker's file tool can write; the workers already write there through the terminal tool, so it is mostly honest bookkeeping, but it is the user's call.
3. **For FXL-3 itself:** it needs a human decision. Unblocking the planner card lets it retry (a worker may or may not find the workaround again); archiving and reloading FXL-3 alone does the same from scratch. I will do neither without a review file or the user.

## Unblocked once, as approved in `FXL-3-decision-review.md`
The only board command run for this (at about 02:08 on 2026-11-26), nothing else touched:
```
kanban unblock t_702a1690        # FXL-3 · planner
```
Approved because the card never completed its stage. If it blocks again for the same reason it stays blocked until the morning; no other card is unblocked. The planner returned to `ready` and was dispatched; the result is below (or in the next evidence commit). The evidence driver for FXL-3 was started again for this run.
