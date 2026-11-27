**Yes, tests have written more than `runner-status.json`:** the live `labels.json` still holds keys from the loader tests of 11-25. And today's suite can also clear the "runner alert sent" marker in `alert-state.json`, though I found that it never did on this VM. **D24 is stopped here until you have read this.** I have not started the `conftest.py` fix either.

# Live-writes audit (LIVE-writes-review)

## Answer, item by item, for today's suites (D21 to D24)
| live item | can today's suite write it? |
|---|---|
| `work/runner-status.json` | **yes, and it did** (14:19:17, two `test_hostkit.py` tests). Fixed on the D24 branch at `a18c096` |
| `alert-state.json` | **yes, by code:** `test_d11`'s runner test runs a good pass, and `alert.runner_recovered()` removes the marker **if there is one.** **Not on this VM:** the file does not exist, the kit never deletes it, and any write leaves it behind. Still unfixed |
| acceptance history, copies and their hashes, `pipeline.json`, ticket records, outbox, decisions ledger, fix ledger, `state.json` | **no change seen** (container runs below) |
| trusted repositories, publish and decisions repositories | **no change seen** |

## Where the older writes are
- **`labels.json`:** it holds `A-1`, `B-2`, `C-3` (and `PRC-1`, which is also a real fixture ticket). Run in the container, the suites of `0a9479c` and `815e543` (11-25, 23:36 and 23:44) **create `labels.json` from nine `test_loader.py` tests,** which use those keys. So the live entries very likely came from suite runs then; I saw it happen in the container, not on the VM. Today's versions do not write it. The test keys have empty label lists and no FIX Lens key; labels only set a ticket's review tier. **Not removed.**
- **`trusted/r.git` (11-25 17:21) and `trusted/repo.git` (11-25 23:41):** their commits are by `t` with messages `b`, `base`, `head`, which is how test helpers commit. **Origin not established:** the committed suites at `5d01038`, `0a9479c` and `815e543` did not recreate them (I cannot rerun uncommitted working trees of that time). Today's versions create nothing there. `pipeline.json` names neither. Left in place; deleting them is Ubay's.

## Checks of the live state (about 14:28, before FXL-17 landed)
- **Acceptance history:** 116 passed ids; last run **FXL-13 on `8881fce`, 121**; two retirements (`D-20261127-2`: 2 ids, `-6`: 5), none of them back in `passed`; the earlier runs are the tickets that ran, in order.
- **`pipeline.json`:** exactly SMK-1, SMK-2, FXL-9 to FXL-13, FXL-17, FXL-14, FXL-15, FXL-16. No other key.
- **Records folders:** only loaded keys. **Decisions ledger:** 9 ids, equal to the 9 files then in the repository, all applied. **Outbox:** empty.
- **Fix ledger:** 26 entries, keys of real tickets and of the seed tickets (`SEED-*`, `JSEED-2`, `RISK-3`). Its last write, 14:23:16, falls just before a run that started 14:23:18, after FXL-17's failed gates record (14:23:06), while its fix pass was being created.
- **Copies** verified at `23952fd05985` at about 14:20.

## Modification times
30 host commands ran the suite or part of it today (some more than once): 01:31 to 02:23, 12:54 to 13:02, 13:23 to 13:34, 14:18 to 14:25, taken from my session transcript. Under the host state folder, the live kit's `work/` and `~/.local/share/agent-harness` (without the kit checkout), 6,720 entries, **18 files** have a time inside a window:
| files | time | written by |
|---|---|---|
| 7 objects in `decisions.git` | 01:46:41 | the runner's pass 01:46:39 to 01:46:44 (journal), which fetches decisions |
| `runs/FXL-10/handoff.md`, `mr.md` | 13:02:06 | the FXL-10 scribe card (12:58:49 to 13:02:15) |
| `runs/FXL-17/base.txt`; `fix-lens`: `src/filters.js`, 6 git objects, `test/filters.test.js` | 14:21:22 to 14:24:47 | FXL-17's implementer cards (14:20:53 to 14:22:33; fix 1 from 14:23:55) |

In an earlier scan, before the 14:40 rewrite, `state.json` showed 14:24:37.566: the runner pass that logged at 14:24:37.567.
**A modification time shows only the last write,** so this cannot clear a file the runner rewrote later, and it does not show deletions. The container runs are the stronger evidence.

## Container runs
Throwaway `--network none` containers from the Hermes image, nothing of the host mounted but a clone, `pytest` and the logging plugin. The live paths existed only as empty temporary filesystems. A hook logged in-process reads and writes; checksums of every file before and after also catch child processes.
- At `7c190a2`, `0dee234`, `6c483e6`: all tests pass; **only `runner-status.json` and `alert-state.json` change.** At `59dcc7c` (D24 head, with the hostkit fix): only `alert-state.json`.
- **Again at `6c483e6` and `59dcc7c` with a placeholder for every state file, folder and repository in place** (so code that writes only what already exists would show): the same result.
- The first container pass had three failures, because the image had no user entry and tools started with a bare environment found no home folder. With a user entry, all pass; the figures above are from those runs.
- Limits: placeholders are not real content, so a write that depends on particular content could be missed.

## Tests that relied on a real path (for the fix)
| path | tests | access |
|---|---|---|
| live kit `work/runner-status.json` | `test_hostkit.py` (2) | write (fixed at `a18c096`) |
| `alert-state.json` | `test_d11.py` (the runner-records-each-pass test) | read and write |
| `fix-ledger.json` | `test_review_diff.py`, `test_reviewer.py`, `test_risk.py` | read |
| `~/.local/share/agent-harness/reviewed-sha` | `test_d20.py`, `test_d24.py` | read |
| `/srv/lab/agent-harness/.venv-mutation/bin/mutmut` | `test_mutation.py`'s skip check, at collection | runs `--version` |

Also: the three tool tests (`test_d11`, `test_d13`, `test_hostkit`'s `PYTHONPATH` test) start processes without `HOME`; on the host those find the real home folder. An in-process fixture alone does not reach them, so the fix has to set `HOME` in their environments too.

## Suite runs after your instruction
It was pushed at 14:21:14. I read it at about 14:25. Before that, host runs started at 14:21:04, 14:21:59, 14:23:18 and 14:24:13 (the last from a fresh clone). They had a guard that blocks and logs in-process writes to live paths: the first logged the hostkit writes (blocked), the others nothing. The guard does not reach child processes; the container runs, which do, show no other write. **Since reading it, every suite run has been in a container.**
