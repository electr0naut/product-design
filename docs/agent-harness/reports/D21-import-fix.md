# D21: the loader can be imported again (D21-review.md)

Branch `d21-import-fix` in agent-harness, on `c06cd27`, at **`7c190a2d696add2fb63f4d409a03e34498e018eb`**. **Not merged, not deployed. No ticket loaded.** `master`, the host kit and the container copy are still `c06cd27`.

## The change (3 files; 4 lines added and 2 removed outside the new tests)
1. **`evidence.py`:** `fixloop` is imported inside `_passes`, its only use. That cuts `loader` → `pipeline` → `evidence` → `fixloop` → `loader` and moves no behaviour. I did not look for a larger cut: the other one I can see is moving `create_card` and `write_rule` out of `loader`, which moves code for no gain here.
2. **`tests/test_d21.py` (new):**
   - **one test per module** under `src/harness/` (28), each starting its own interpreter with `import harness.<name>`;
   - **every script in `tools/`** (14), in a fresh process: `--help` for the seven that exit on it (`load_tickets` and `review_variant` among them); `record_tickets` has no `--help`, so it is run with no arguments to its usage message; the six with neither `--help` nor a dry run are executed only up to their `__main__` guard, which makes all their imports (the seed scripts would act if run);
   - a list test, so a new tool has to be put in one of those three groups;
   - a loader `--dry-run` in a fresh process, and the alert text being plain words.
   Each fresh process gets an empty `HOME`.
3. **`alert.py`:** the emoji is gone from the alert text. `harness_notify.py` still has its own emoji: you named only `alert.py`.

## The tests catch the bug
Run on the **unfixed** `c06cd27` code: **10 failed, 35 passed.** The failures were the modules `loader` and `variants`; the tools `load_tickets`, `record_tickets`, `review_variant`, `seed_fixfail`, `seed_js` and `seed_risk` (your six); the loader dry run; and the alert text.

## Test output (fresh clone of `7c190a2`)
```
568 passed, 3 skipped in 35.83s
ruff check: All checks passed!      ruff format --check: 94 files already formatted
```
`tests/test_d21.py -v`:
```
test_a_module_imports_first_in_a_fresh_process[acceptance] PASSED
test_a_module_imports_first_in_a_fresh_process[alert] PASSED
test_a_module_imports_first_in_a_fresh_process[copies] PASSED
test_a_module_imports_first_in_a_fresh_process[decisions] PASSED
test_a_module_imports_first_in_a_fresh_process[evidence] PASSED
test_a_module_imports_first_in_a_fresh_process[fixloop] PASSED
test_a_module_imports_first_in_a_fresh_process[gatekeeper] PASSED
test_a_module_imports_first_in_a_fresh_process[gates] PASSED
test_a_module_imports_first_in_a_fresh_process[hostkit] PASSED
test_a_module_imports_first_in_a_fresh_process[isolated] PASSED
test_a_module_imports_first_in_a_fresh_process[keys] PASSED
test_a_module_imports_first_in_a_fresh_process[loader] PASSED
test_a_module_imports_first_in_a_fresh_process[loader_gate] PASSED
test_a_module_imports_first_in_a_fresh_process[mutation] PASSED
test_a_module_imports_first_in_a_fresh_process[pipeline] PASSED
test_a_module_imports_first_in_a_fresh_process[publish] PASSED
test_a_module_imports_first_in_a_fresh_process[queue] PASSED
test_a_module_imports_first_in_a_fresh_process[records] PASSED
test_a_module_imports_first_in_a_fresh_process[repos] PASSED
test_a_module_imports_first_in_a_fresh_process[reviewer] PASSED
test_a_module_imports_first_in_a_fresh_process[risk] PASSED
test_a_module_imports_first_in_a_fresh_process[runner_status] PASSED
test_a_module_imports_first_in_a_fresh_process[score] PASSED
test_a_module_imports_first_in_a_fresh_process[specs] PASSED
test_a_module_imports_first_in_a_fresh_process[statefile] PASSED
test_a_module_imports_first_in_a_fresh_process[trusted] PASSED
test_a_module_imports_first_in_a_fresh_process[usage] PASSED
test_a_module_imports_first_in_a_fresh_process[variants] PASSED
test_a_tool_reaches_its_help[approve_test_edit] PASSED
test_a_tool_reaches_its_help[deploy] PASSED
test_a_tool_reaches_its_help[deploy_host_kit] PASSED
test_a_tool_reaches_its_help[load_tickets] PASSED
test_a_tool_reaches_its_help[migrate_fix_ledger] PASSED
test_a_tool_reaches_its_help[reset_attempt] PASSED
test_a_tool_reaches_its_help[review_variant] PASSED
test_a_tool_without_help_reaches_its_usage_message[record_tickets] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[extract_literals] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[harness_notify] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[merge_config] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[seed_fixfail] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[seed_js] PASSED
test_a_tool_without_help_or_dry_run_makes_all_its_imports[seed_risk] PASSED
test_every_tool_is_in_one_of_the_lists PASSED
test_the_loader_dry_run_works_in_a_fresh_process PASSED
test_the_alert_text_is_plain_words PASSED
============================== 45 passed in 1.26s ==============================
```
Also, with the **deployed kit's own interpreter** (Python 3.14.9) on the fresh clone, each module imported as the first import: **28 modules, 0 failed.**

## Dry run of loading FXL-9 to FXL-13, current ticket files
Fresh clone, that interpreter, `tools/load_tickets.py --dry-run --repo .../work/fix-lens`, files from product-design at the time of this report:

| ticket | last commit of the file | sha256 (first 12) |
|---|---|---|
| FXL-9 | `1b47d32` | `c9ef1f520c0a` |
| FXL-10 | `1b47d32` | `915fc4714704` |
| FXL-11 | `1b47d32` | `7fa4389df732` |
| FXL-12 | `1b47d32` | `6a20b2b38e78` |
| FXL-13 | `1b47d32` | `b467210139d5` |

```
FXL-9: parent + triage -> planner -> implementer -> gatekeeper -> reviewer -> scribe; waits on nothing
FXL-10: parent + triage -> planner -> implementer -> gatekeeper -> reviewer -> scribe; waits on nothing
FXL-11: parent + triage -> planner -> implementer -> gatekeeper -> reviewer -> scribe; waits on nothing
FXL-12: parent + triage -> planner -> implementer -> gatekeeper -> reviewer -> scribe; waits on ['FXL-10']
FXL-13: parent + triage -> planner -> implementer -> gatekeeper -> reviewer -> scribe; waits on ['FXL-11']
```
Exit 0. All five files are from `1b47d32`, the commit that adds AC12. Afterwards the board had no card for FXL-9 to FXL-16 and no gate card, and `pipeline.json` does not exist.

## What the dry run does not show
- **It prints only `blocked_by`.** The gate links are made only in a real load. There, FXL-9 should start at once (no open gate; its `blocked_by` is empty), and each later ticket should wait on the gate of the one before it as well as on its own blockers.
- **The real load path of the command line has still never run:** reading `[pipeline]`, creating gate cards on the real board, and writing `pipeline.json`. The D20 tests run `loader.load` with gates on a fake board only. **The fixture ticket check will be its first real run,** which is a good reason to keep it ahead of FXL-9.
- The import tests prove each file's top-level imports and, for the `--help` group, argument parsing. An import made inside a function that is not reached is not covered.

## Next (unchanged)
Your review; Ubay deploys; then `V12-go-review.md` and `V12-go-review2.md`: the fixture ticket check, added to `V12-live-checks.md`, and FXL-9 to FXL-13 only if everything holds. Check 2 is not repeated (D21-review).

Created and deleted in this job: scratch notes `/tmp/d21-*.txt`. `/tmp/fc` is the reused fresh-clone folder.
