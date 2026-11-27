# V12 live checks: STOPPED. The deployed D20 loader cannot be imported. Nothing loaded

2026-11-27, about 02:15 CET. Per `V12-go-review.md` and `V12-go-review2.md`: "If anything differs from this, in any way: load nothing, report, and wait. Do not fix and retry." **FXL-9 to FXL-13 are not loaded, from any commit. The fixture ticket is not loaded either.** No card was created.

## The fault (mine, in D20)
On the deployed kit `c06cd27`, `tools/load_tickets.py` crashes before doing anything:
```
ImportError: cannot import name 'create_card' from partially initialized module 'harness.loader' (most likely due to a circular import)
```
**Cause:** an import circle D20 created: `loader` imports `pipeline`, which imports `evidence`, which imports `fixloop`, which imports `create_card` from `loader`. On `76b094f` the loader imports cleanly.

| entry point on `c06cd27` | |
|---|---|
| `tools/load_tickets.py`, `tools/record_tickets.py` | **crash** |
| `import harness.loader` or `harness.variants` as the first import | **crash** |
| `tools/reset_attempt.py`, `approve_test_edit.py`, `migrate_fix_ledger.py` | start |
| every other `harness.*` module, imported first | imports |
| the host runner | **works:** 18 idle passes since the deploy to the time of the check, no error line, runner status ok. It reaches these modules in an order that closes the circle |

So **no ticket can be loaded at all** with this kit. Nothing else I tried is affected, and I see no reason to roll back: the queue is empty. `pipeline.json` does not exist.

**Why tests and review did not see it:** the tests run in one Python process, where an earlier test file has already imported the modules in an order that works. No test imported the loader in a fresh process or started a tool. My D20 live checks imported other modules first. My D20 report did list "the loader creating gate cards on the real board" as not run; I had not even started the tool.

## Proposed fix (not applied, not pushed)
In `src/harness/evidence.py`, import `fixloop` inside `_passes` instead of at the top (its only use). I tried it **in a throwaway clone of `c06cd27`, then deleted the clone:**
- every `harness.*` module imports as the first import;
- `load_tickets`, `reset_attempt`, `approve_test_edit`, `migrate_fix_ledger` start. `record_tickets --help` still exits non-zero only because it has no `--help` and reads it as a file name (it does the same on `76b094f`);
- a `--dry-run` of FXL-9 to FXL-13 from the current files lists them in the order 9, 10, 11, 12, 13, with FXL-12 waiting on FXL-10 and FXL-13 on FXL-11 (a dry run does not show the gate links);
- 523 passed, 3 skipped.

**The fix should come with the test that was missing:** start a fresh interpreter for every `harness.*` module and every script in `tools/`, and require a clean import. I have not written it. Say "build it" and it goes on a branch for review; then it needs Ubay's deploy.

## The go conditions
| condition | state |
|---|---|
| both units installed | **met** (`D20-live-checks.md`) |
| check 1: the fixture ticket through the pipeline | **cannot run** (the loader) |
| check 2: real hidden suite, isolated, no regression, two retired named apart, commit shown | ran: no regression, 67/166. **Note:** it ran at 02:02:34 on the copies of `db3b087`, **24 seconds before** `D-20261127-3` was applied (02:02:58). The hidden suite is identical in `db3b087` and `ae216b0`; only the design changed. I have not rerun it |
| check 3: test alert sent without error | **met** (02:02:48, exit 0); arrival not confirmed |
| `D-20261127-3` applied and the copies verify | **met:** applied 02:02:58; verification passes at `ae216b0f82e0`, 17 hidden files; recorded design sha256 changed from `4de073a86373…` to `4c2cb3fd5236…`, which equals the design at that commit; all four worker reading copies have the same hash |
| ticket files at or after the AC12 commit | the current `FXL-9.md` is from `1b47d32`, which has AC12 |

## For check 1 after the fix
The ticket files under `eval/` were written for earlier runs on the sample repositories, and I have not checked which are already merged there. I expect to write two small new tickets for a sample repository, and will put their text in the report.

## Also
I missed `V12-go-review.md` on my earlier check: it arrived while I was pushing the D20 live-checks report, and I only saw it through `V12-go-review2.md`. Ubay's answer is quoted there, so under RULES section 1 it covers the fixture ticket and the first batch, under its conditions.

Created and deleted in this job: throwaway clones `/tmp/d20-fixtry` and `/tmp/d19chk`.

---

# After the D21 deploy (D21-code-review.md, steps 1 to 4)

2026-11-27, 02:32 to 02:55 CET. **Steps 1 and 2 are met. Step 3 is not: there is no answer about the test alert. So I stopped here. FXL-9 to FXL-13 are not loaded.** The section above this line is the earlier stop, kept as it was.

D21 is deployed (host kit, container copy and the runner's journal at `7c190a2` from 02:30:23). `master` was fast-forwarded to `7c190a2d696add2fb63f4d409a03e34498e018eb`.

## Step 1: the deployed kit, not a clone
| check | result |
|---|---|
| host kit, its own interpreter (3.14.9), `import harness.loader` first in a fresh process | **ok**, loaded from `~/.local/share/agent-harness/kit/src`, exit 0 |
| container copy, `.venv-container` interpreter (3.14.9), the same, as `hermes` | **ok**, loaded from `/srv/lab/agent-harness/src`, exit 0 |
| `tools/load_tickets.py --help` from the deployed path | **ok**, usage printed, exit 0 |

## Step 2: the fixture ticket check: **met**
**Repository: `fixture-repo` (Python), unchanged.** Before loading it was clean and detached, 21 tests passed, ruff was clean, no worker card was running and `pipeline.json` did not exist.
**Not the JavaScript sample:** `work/fixture-js-repo/node_modules` is a **dangling link** to `work/js-deps/`, which no longer exists (dependencies moved at D5.1). The loader keeps an existing link, so its workers could not run tests. The same code passes its 14 tests with the configured `deps/js`. I did not touch it.

**Tickets** (new, in `work/smoke-tickets/`):
- **SMK-1** `total(amounts: list[int])`: AC1 `total([2,3,5]) == 10`; AC2 `total([]) == 0`; AC3 a non-int value raises `TypeError`.
- **SMK-2** `largest(values: list[int])`: AC1 `largest([2,9,4]) == 9`; AC2 `largest([-3,-7]) == -3`; AC3 `largest([])` raises `ValueError`.

Both `blocked_by = []`, loaded with the deployed kit in **two separate calls**, so that only the gate could make SMK-2 wait. **This was the first real run of the command-line load path; both exited 0.**

| | SMK-1 | SMK-2 |
|---|---|---|
| ticket / triage / planner | `t_25eb2d0b` / `t_d7d1845f` / `t_6a360f19` | `t_f9bd957f` / `t_9c8f3cc6` / `t_8a3c9218` |
| implementer / gatekeeper / reviewer / scribe | `t_0d252eb7` / `t_e3ec9123` / `t_3629e8a2` / `t_03213b76` | `t_3e0e11b1` / `t_6cb7834a` / `t_4c60929e` / `t_eb90bc9e` |
| **gate card** | **`accept SMK-1` `t_f68afde6`**, unassigned, waits on SMK-1's scribe | **`accept SMK-2` `t_5e2371ae`**, unassigned, waits on SMK-2's scribe |

Right after loading, `SMK-2 · triage` was `todo` and **waited on `accept SMK-1`** (its only parent besides its own ticket card), while SMK-1's triage was already running.

### The order, from the board's own event times
| time | event |
|---|---|
| 02:41:35 | `SMK-1 · scribe` completed; `accept SMK-1` promoted |
| 02:41:35 to 02:41:56 | gate open to be completed, **`SMK-2 · triage` still `todo`** |
| **02:41:56** | **`accept SMK-1` completed**; `SMK-2 · triage` promoted the same second |
| 02:42:19 | `SMK-2 · triage` claimed (it had never been claimed before) |
| 02:49:26 | `SMK-2 · scribe` completed |
| 02:49:31 | `accept SMK-2` completed |

A watcher polling every 3 s recorded the same order.

**Who completed the gates:** each gate's run record has **no profile, no worker pid and no claim lock**, and carries the runner's own summary (`SMK-1: hidden suite passed`). Both completions fall inside a runner pass. I searched the tool calls of every profile since the load (107 messages with calls): only the two scribes named a gate card, to read it (`kanban_show`) and to mention it in their handoff note; their `kanban_complete` calls were on their own cards.

### The journal, and a gap
```
02:41:49 systemd: Starting harness-reviewer.service - Harness host reviewer runner (one pass)...
02:42:23 harness.reviewer: kit .../agent-harness/kit @ 7c190a2d696add2fb63f4d409a03e34498e018eb
02:42:23 idle; idle
02:42:23 systemd: Finished harness-reviewer.service
...
02:49:53 harness.reviewer: kit .../agent-harness/kit @ 7c190a2d696add2fb63f4d409a03e34498e018eb
02:49:53 idle; idle
02:49:53 systemd: Finished harness-reviewer.service
```
**You asked for the journal lines where the runner completes the gate. There are none: the runner logs nothing when it finishes a ticket or completes a gate.** (The lines above appear together because output is flushed when the pass ends.) That is a gap in D20, so the proof rests on the board events, the gate run records and `pipeline.json`. No error, skip or warning line since the load.

### `pipeline.json` at the end (as loaded, both had `result`, `finished` and `scribe_done_at` null)
```json

```

### The rest of the run
- Trusted `main` of `fixture-repo`: `7590ca0` → `063c52a` (SMK-1) → `341aedc` (SMK-2). Gates passed first time for both, no missing ACs (mutmut: 5 killed and 2 survived; 1 killed). Reviews: no findings, Claude $0.00. No fix pass, no block, no hold.
- Host records kept for each: gates, review, approval. `state.json` shows both finished; the runner published `STATE.md` itself (`3c9282e`, `bb1e55a`); the outbox is empty. No evidence was published, as `fixture-repo` has no `[evidence]` table. Nothing was left in `scoring/`.
- Sessions since the load: planner and implementer `gpt-6.2-sol` (openai-codex), triage `qwen3.7-plus`, reviewer and scribe `deepseek-flash`; two or more each, and no other model.
- FIX Lens is untouched: trusted `main` `e721f31`, history 67 `passed`, copies verify at `ae216b0f82e0` (design `4c2cb3fd5236`, 17 files), no card for FXL-9 to FXL-16.
- **Not exercised by this check:** the hidden suite inside a pipeline run (no hidden tests for this repository), a hold after a regression, a block report, and publishing a ticket's evidence.

## Step 3: the 02:02 test alert: **no answer**
Ubay's message to this job, 2026-11-27, read: *"Deployed 7c190a2. Continue with docs/agent-harness/reports/D21-code-review.md, steps 1 to 4, and work unattended. The 02:02 test alert: <arrived in chat X / did not arrive>."* **The last part is the unfilled placeholder,** so it says neither that the alert arrived nor that it did not. I take it as no answer, and I asked in the session; none has come by the time of this report. Per step 3: stop after the fixture check and report.

## Step 4: not run
Everything else needed for it is in place. **To go on, one line is needed from Ubay: whether the 02:02 message ("TEST ONLY, nothing is wrong ...") arrived, and in which chat.** If it arrived, I quote it here, re-check that nothing else has changed, and load FXL-9 to FXL-13 from `1b47d32` or later.

## For the next kit change
1. **Log a line** when a ticket is finished, and when a gate is completed or held.
2. The gate's completion summary says **"hidden suite passed" even where no suite is enabled** (both fixture gates say so). It should say that none ran.
3. `STATE.md` will list finished tickets (now SMK-1 and SMK-2) for as long as they stay in `pipeline.json`.
4. The dangling `node_modules` link in `fixture-js-repo` (not kit code; say if I should repair it).

## Created, kept and deleted in this job
Kept: the SMK-1 and SMK-2 cards (done), their run folders, the two commits on the fixture repository's `main`, the ticket files in `work/smoke-tickets/`, and the watcher and its log in `~/.local/state/agent-harness-bake/smk/`. Deleted: my scratch checkouts `work/scratch-smoke-pre` and two temporary query scripts in the container's `/tmp`.
