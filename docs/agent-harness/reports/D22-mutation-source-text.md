# D22: source-text tests out of Stryker's runs, a mutation rerun, and the error in STATE.md

Branch `d22-mutation-source-text` of `agent-harness`, commit **`0dee234ccbcaa6397c041de8d3969b2edb17baae`**, from `7c190a2`. **Not merged, not deployed.** The live kit, its config, the dependencies and the board were not touched.

## One thing for you to decide before approving: the list has a side effect
`test/static-checks.test.js` is the **only** test of `tools/audit-source.mjs`. With it left out:
- **A ticket that changes the tool and `src/` together** (FXL-9): there is a report, but every mutant of the tool shows as without tests. On FXL-9: 131 of the 156.
- **A ticket that changes only the tool:** Stryker finds no related test and **errors** ("No tests were executed", shown on the real Stryker below). **Without the list that case would give a real result,** since no `src/` file is instrumented. So here the change makes things worse. `STATE.md` would name the error.

I built what you specified and changed nothing about this. Options:
- **A. Accept it.** Simplest. The tool is a build check, not delivered code.
- **B. Leave the test out only when it can fail for this reason:** the entry also names what it reads as text (`reads = ["src/"]`), and it is left out only if a mutated file is under that. This fixes the tool-only case. A mixed change still gives no result for the tool.
- **C. B, plus two Stryker runs for a mixed change:** `src/` files without the check, the rest with it, results added together. Full coverage; the most code, and the two runs must share the time cap.

**I recommend B** if FXL-14 or a later ticket is likely to change the audit tool; otherwise A. C is not worth it for one build tool.

## "Does something close exist already?"
Partly. `python -m harness.gates --config … --repo … --base … --head …` runs in the container on any range, mutation included. But it runs **all** the gates, needs the implement report and the ACs, does not check that the range landed or that no card is running, and records nothing. There was no mutation-only tool.

## Built
1. **`[mutation] source_text_tests`**, set for `fix-lens` to `test/static-checks.test.js`. The files are moved out of the throwaway worktree for Stryker's run only and put back afterwards, also if it fails. Exact paths: a missing file, a glob, a non-test file, a symlink or a path with `..` is a mutation error, **checked even when nothing would be mutated.** Mutation stays report-only, so such an error does not block a ticket. The result has `source_text_tests_left_out`.
   It is in `eval/fix-lens/harness.fixlens.toml`, not `harness.host.toml`, because the gates run in the container and read this file.
2. **`tools/rerun_mutation.py KEY`** (host). The range comes from the host's approval record, or from `--repo --base --head`. It must be full shas, on the trusted `main`, base before head. It runs on a plain copy of the head, in the container as `hermes`, with the gate's `gate_field` and `changed_line_map` and the kit's current config. It adds a `mutation-rerun` record and its full log to the ticket's host records, writes nothing else, and removes its scratch folder. It refuses while a worker card of that repository is running (checked once, at the start). Exit 0, 1 if the run errored, 2 if refused. The implement report it reads from the run folder only labels survivors by AC.
3. **`STATE.md`** names a mutation run that errored under its ticket; a later clean rerun clears it. The text is the first 200 characters of the error, which for a Stryker crash is partly stack trace; the cause is in the log. `STATE.md` is rewritten only on events, so a rerun alone shows at the next one.

## Tests
From a fresh clone of `0dee234`: format and ruff clean, **589 passed, 3 skipped**. The 3 skips were not added by this change. `rerun_mutation` is in the fresh-process import list of `tests/test_d21.py`.
These tests use stand-ins for Stryker, Vitest and `docker exec`: the stand-in adds `new Function` and selects tests by import, as the real one does. `tests/test_d22.py`:
```
test_without_the_list_the_reduced_fxl9_case_fails_as_it_did PASSED [  5%]
test_with_the_list_the_same_case_gets_a_report_that_names_what_it_left_out PASSED [ 10%]
test_the_files_are_put_back_even_when_the_engine_blows_up PASSED [ 15%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad0] PASSED [ 20%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad1] PASSED [ 25%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad2] PASSED [ 30%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad3] PASSED [ 35%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad4] PASSED [ 40%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[test/static-checks.test.js] PASSED [ 45%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad6] PASSED [ 50%]
test_an_entry_that_names_no_existing_test_file_is_an_error_not_a_skip[bad7] PASSED [ 55%]
test_a_symlink_is_not_a_test_file PASSED              [ 60%]
test_the_gates_still_run_the_listed_test PASSED       [ 65%]
test_fix_lens_lists_its_static_check PASSED           [ 70%]
test_the_rerun_gives_the_gates_result_for_the_same_range PASSED [ 75%]
test_the_rerun_takes_the_range_from_the_approval_record PASSED [ 80%]
test_the_rerun_refuses_while_a_card_of_that_repository_runs PASSED [ 85%]
test_the_rerun_refuses_anything_that_is_not_a_landed_range PASSED [ 90%]
test_a_rerun_that_errors_says_so_and_exits_1 PASSED   [ 95%]
test_a_mutation_run_that_errored_is_named_under_its_ticket PASSED [100%]
============================== 20 passed in 1.46s ==============================
```
"Same result as the gate" is `test_the_rerun_gives_the_gates_result_for_the_same_range`: `run_gates` and the tool give equal counts and survivors on the sample repository.

## The real Stryker on FXL-9's landed commits (`e721f31..60b1211`)
The branch's code, in throwaway `--network none` containers from the Hermes image, on plain copies of the code and of `node_modules`, all in my job's scratch folder (containers removed; none left). No hidden tests involved. The first two runs used the same changed lines, and their configs differ only in the list.

| run | instrumented | result |
|---|---|---|
| empty list | 2 files, 447 mutants | **fails as on FXL-9:** `src/framing.js: expected [ '/\bnew\s+Function\b/' ] to have a length of +0 but got 1` |
| with the list | the same | **report:** first run 118 tests passed; 187 killed, 72 survived, 32 timeout, 156 without tests, 0 unrun, complete; 2 min 24 s (cap 5 min) |
| with the list, only `tools/audit-source.mjs` changed | 1 file, 131 mutants | **error:** "Vitest failed to find test files related to mutated files … No tests were executed" |

By file in the second run: `src/framing.js` 187 killed, 32 timeout, 72 survived, 25 without tests; `tools/audit-source.mjs` 131 without tests.
**These are not FXL-9's official rerun,** which follows the deploy, through the tool.
**Not run live:** the tool's own `docker exec` into `hermes`, since it writes under the live kit's `work/`. Checked read-only: the host user and `hermes` are both uid 1000, the container imports `harness` from the kit, the live board's JSON has the three fields the refusal reads, and FXL-9's approval record has `base` and `head`.

## After approval and deploy, with no card running
From the deployed host kit: `tools/rerun_mutation.py FXL-9`, plus any later ticket whose mutation run errored. So far that is none after FXL-9: FXL-10's succeeded.
