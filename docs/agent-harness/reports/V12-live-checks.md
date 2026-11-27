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
