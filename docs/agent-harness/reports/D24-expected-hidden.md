# D24, after the test guard (LIVE-writes-review2, FXL-13-landed-review)

**New branch `d24-after-guard`** of `agent-harness`. **Not merged** (`master` is `6c483e6`), **not deployed.** Three commits on `6c483e6`, in your order:

| commit | what |
|---|---|
| `a18c096` | the two `test_hostkit.py` tests that wrote the live status file (as before) |
| **`1007fffbcde095c599c556c3906035fac42a785b`** | **the guard** (tests only) |
| **`b20b702746f76fc19bedab2d7989714738f6f86a`** | **D24** |

My earlier branch had D24 before the guard. I did not force-push over it: this is a new branch, with D24 cherry-picked on top (same patch id as `59dcc7c`). **Do not use `d24-expected-hidden`.**

## 1. The guard (`a18c096..1007fff`, only files under `tests/`)
- `tests/conftest.py`: `HOME` is a throwaway folder **before** `harness` is imported (covers module constants and checks made at collection). Then, for every test, **every module constant and every function or method default** under the home folder or `/srv/lab/agent-harness` is redirected into that test's `tmp_path`. They are found by looking, not listed, so a path added later is covered. Paths inside the checkout under test are left alone. Autouse, in the root conftest: no opt-out marker or switch.
- `tests/test_isolation.py`: one case per path (the audit's table plus the other state files, 17), a scan that no constant or default still points at the live harness, `HOME`, and the mutmut check.
- The two `test_hostkit.py` tests now rely on this and name no real kit path.
- The tool tests that start processes with their own environment now pass `HOME`: in `test_d11`, `test_d13`, `test_hostkit`, and one the audit missed, `test_d22`'s stand-in for `docker exec`. `test_d21` already set it.
- The mutmut check now returns false without `/opt/hermes` **before** touching anything under `/srv/lab`. The real-engine tests run where they ran before: only where that venv is usable.
- **Which tests relied on a real path:** the table in `LIVE-writes-audit.md` (`test_hostkit`, `test_d11`, `test_review_diff`, `test_reviewer`, `test_risk`, `test_d20`, `test_d24`, `test_mutation`).

**Limit:** the redirect covers `Path` constants and defaults. A live path written as plain text, for example in a config file a test loads, is not rewritten. The proof run below is what shows none is read or written.

### Proof, as in the audit
Throwaway `--network none` containers from the Hermes image, on **fresh clones from GitHub**. The live paths exist only as temporary filesystems, **seeded with a placeholder** for each state file, folder and repository. The logging hook is loaded by a `.pth` file, so it is in **every Python process of the run, child processes included**; it logs reads, writes, and live paths passed to any other program. Checksums are taken before and after.

At `1007fff`:
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
618 passed, 3 skipped in 79.31s (0:01:19)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 271; started without HOME: 0
```
At `b20b702`:
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
635 passed, 3 skipped in 79.44s (0:01:19)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 271; started without HOME: 0
```
The three skips are the real-engine tests, as in earlier host runs. `ruff check` and `ruff format --check` are clean at both commits.

**Controls, so that the zeros mean something:**
- The same proof run at `59dcc7c` (before the guard) logs **50 accesses** (46 reads, 3 writes, 1 program run), and `alert-state.json` changes.
- With the redirect switched off in a copy, **19 of the 20** tests of `test_isolation.py` fail. The one that passes is the mutmut check, which does not depend on the redirect.

**All suite runs since I read your instruction were in containers,** and stay so as you say.

## 2. D24 (`1007fff..b20b702`)
- **Table:** `[expected_hidden.fix-lens]` in `harness.host.toml` (acceptance runs on the host and reads it): FXL-14 `acc-presentation`, FXL-15 `acc-order-story`, FXL-16 `acc-trades`, FXL-17 `acc-filters`.
- **"In full":** the file has results, all pass, and there are at least as many as the tests it declares. A failed, skipped, vanished or unloadable test is not a pass. Results are counted row by row, so two tests of one name cannot hide a failure.
- **Hold:** as for a regression. The gate stays shut and a `release` decision opens it. The reason names files and counts, for example `expected hidden tests not passing: acc-filters.test.js 6 of 8`, in the PR comment, the evidence, `STATE.md`'s holds, the journal and the release result. For a card that someone else had already opened, the same `hold` cards are placed.
- **The evidence** lists each expected file, passed of total, met or **NOT MET**, with the failing test names.
- **A ticket not in the table, or a plain regression:** the same behaviour and the same wording as today; the existing tests are unchanged.
- **One choice to check:** a listed file missing from the host copy (or a malformed entry, or no hidden suite) is an **error before the run**, on the existing "hidden suite could not run" path: nothing is scored, the gate stays shut, an alert after 3 tries. **A `release` decision does not open it,** because nothing is held yet; a `refresh_copies` that brings the file lets the next pass run. If you want it releasable, say so.
- **Checked read-only on the real host copy:** the kit's test count for the four expected files is 21, 12, 14 and 8, equal to your README table; none has parametrised or skipped tests. So the count rule does not hold a good ticket on these files.

`tests/test_d24.py` (stand-in scorer; the real `run_acceptance` and `finish_pass`):
```
test_a_ticket_whose_expected_file_passes_opens_its_gate PASSED [  5%]
test_a_failing_expected_test_holds_until_a_release PASSED [ 11%]
test_a_test_that_does_not_run_is_not_a_pass[skip] PASSED [ 17%]
test_a_test_that_does_not_run_is_not_a_pass[error] PASSED [ 23%]
test_a_test_that_does_not_run_is_not_a_pass[gone] PASSED [ 29%]
test_a_test_that_does_not_run_is_not_a_pass[unloadable] PASSED [ 35%]
test_two_results_of_one_name_cannot_hide_a_failure PASSED [ 41%]
test_a_missing_expected_file_keeps_the_gate_shut_until_it_is_there PASSED [ 47%]
test_a_ticket_that_is_not_in_the_table_behaves_as_before PASSED [ 52%]
test_a_regression_and_an_unmet_file_are_both_named PASSED [ 58%]
test_a_malformed_entry_is_an_error[acc-a.test.js] PASSED [ 64%]
test_a_malformed_entry_is_an_error[bad1] PASSED       [ 70%]
test_a_malformed_entry_is_an_error[bad2] PASSED       [ 76%]
test_a_malformed_entry_is_an_error[None] PASSED       [ 82%]
test_a_malformed_entry_is_an_error[bad4] PASSED       [ 88%]
test_an_expecting_ticket_cannot_pass_without_a_hidden_suite PASSED [ 94%]
test_the_reviewed_table_matches_the_order PASSED      [100%]
============================== 17 passed in 1.60s ==============================
```
(Listing from my earlier run of the identical patch; the container run above includes these 17.)

## Also: FXL-14's mutation line
`killed 227, survived 12, timeout 0, no tests 2, unrun 0, static (not measured) 4`; no error, complete, static check left out. One gates run. From the runner's records: hidden 149 of 173, no regression, `acc-presentation` with nothing failing.
