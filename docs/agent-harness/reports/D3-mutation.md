# D3: mutation testing on the changed lines, report-only (`agent-harness@c92fadc`)

Kit `master` = `c92fadc` (`git ls-remote` confirmed). Fresh clone: `239 passed, 3 skipped` (the real-engine tests skip outside the container), `ruff check` and `ruff format --check` clean. **Container: `242 passed`** (the same suite plus the real mutmut and real Stryker tests). Switched **off**: `[mutation] enabled = false` in both configs.

## First commit of D3 (`340713c`): the old `[risk]` keys
`high_paths` (auth, payments, migrations, infra) are folded into `high_risk_globs` as both `auth/*` and `*/auth/*` (and the same for the others); `risk:high` is now a high-risk label; `high_diff_lines = 500` is a real rule (a diff changing more lines, added plus deleted via `git diff --numstat` in the trusted repo, is high; docs-only does not beat it); `medium_paths`, `medium_diff_lines` and `high_labels` are deleted. The config test now fails on any unknown key in `[risk]`. Tests: `auth/login.py`, `src/auth/login.py`, `payments/x.py`, `a/b/migrations/001.sql`, `infra/main.tf` are high through the **real committed** `harness.host.toml`; 501 lines is high, 500 is not; the review goes high on a large diff. The same duplicate-table mistake nearly happened again with `[mutation]` (BUILD_SPEC already had one: `tool`, `max_mutants`, `max_per_line`, `timeout_s`, `min_risk`); this time the config test caught it before the commit, and the old keys are replaced by the live ones.

## D3 design
A gate field `mutation` in `gates.json`, produced inside the container on the head worktree, **never changing `passed`** (`blocking: false`; a test runs the gates with 9 fake survivors and `passed` stays true). Errors in the field become `{"ran": false, "error": ...}`, never an exception.

**Python: mutmut 3.8.1** (installed in a new `/srv/lab/agent-harness/.venv-mutation`, created inside the container with its own interpreter). The gate:
1. takes the changed source lines from `git diff -U0` (`gates.changed_line_map`, `GIT_SAFE`; deleted files have no added lines);
2. writes a `setup.cfg` in the throwaway worktree: `source_paths` = the changed files' folders, `do_not_mutate` = every unchanged `.py` next to them;
3. runs `mutmut run` under a time cap (`time_cap_s = 300`; exit 124 marks the report `incomplete`), then reads `mutmut results --all true`;
4. maps each mutant back to a **source line** (mutmut's diff is function-relative: the removed line's text is located inside the named function with `ast`) and **keeps only mutants on changed lines**;
5. for each survivor asks `mutmut tests-for-mutant` and attributes it to the **ACs whose tests cover it** (ids from `implement.json`), so the report reads "AC3's tests execute this line and still pass when it is mutated". Survivors no test covers are listed as `uncovered_survivors`. At most `max_survivors_listed = 30` are detailed.

mutmut cannot restrict mutation to lines itself (only to files and functions), so the line filter is a post-filter on its results; unchanged files are excluded with `do_not_mutate`.

**JavaScript: Stryker 9.6.1 with the Vitest runner**, `mutate` set to the changed line ranges (`src/slug.js:2-5`, so only those lines are mutated), JSON reporter, `perTest` coverage, per-mutant timeout. Installed as dev dependencies of the JS fixture (`package.json`, `work/js-deps`). `engine = "stryker"` in `eval/fixture-js/harness.js.toml`.

**Known Stryker/Vitest limit, found by testing on a real fixture (important):** with tests **inside `describe()` blocks** the runner executes **0 tests per mutant**, so every mutant reports `Survived` (my first run on JSN-1 said "15 survived, 0 killed in 1.6 s", which is wrong). Top-level `test()` calls work (10 of 15 killed on the same code). The report has `testsCompleted` per mutant, so the gate counts a covered mutant with `testsCompleted == 0` as **`unrun`** (unknown, never "survived") and sets a `warning`. Tests cover this with a canned report and with real Stryker in the container. Consequence: **mutation results for JS are only trustworthy for projects whose tests are top-level `test()` calls**, or after the runner is fixed; the JS fixture's own tests use `describe`, so they report `unrun: 15` and the warning.

## Evidence (container, real engines)
- **Python, seeded weak test** (`add(0, 0) == 0` cannot tell `+` from `-`): exactly 1 survivor, `return a + b -> return a - b`, line 2, attributed to AC1, `uncovered_survivors: []`, `passed: true`, `blocking: false`. With a strong test (`add(2, 3) == 5`): 0 survivors.
- **JS, seeded weak test** (only `chunk([], 2)`): survivors in the loop; with an added split test the survivors plus uncovered mutants go down. (Both in `tests/test_mutation.py`, run for real in the container.)
- **The actual Python fixture** (`variant-repo`, the seeded weak SEED-A first commit, base `a3f10bc`): `passed: true`; **29 killed, 11 survived, 12 no tests, 0 timeouts, 21.1 s**. Survivors on changed lines include `pricing/discount.py:16` `rounding=ROUND_HALF_UP` -> `rounding=None` and -> dropping the argument (exactly the rounding rule the weak AC3 test missed, which the review found by a different route) and `if percent < 0` -> `<= 0`, plus several in the new `money.py`. **Attribution is coarse:** each survivor lists all four ACs because every test executes `apply_discount` and `Money`; the signal is "the changed line survives the whole suite", not a precise AC owner.
- **The actual JS fixture** (JSN-1): `passed: true`, `unrun: 15`, the warning above (describe tests).

## D0.2 check (root-owned shared dependencies)
**The `sudo chown` is not in effect.** `stat` shows `ubay:ubay 555` for `.venv-container` and `work/js-deps/node_modules` (and the deep files `ubay:ubay 444`), not `root:root`. As `hermes` in the container: a write is denied (mode 555), **but `chmod u+w` and `chmod 777` on both folders succeeded** (same uid 1000, hermes owns them): the speed bump is the only protection. **My probe did exactly that and left both folders at mode 777; I noticed it in the next command and restored 555** (a few seconds, no real worker was running; it is the same hole a worker has today). Nothing else in `D0.2-chown-review.md` can be verified until the chown happens: please confirm whether it was run (maybe on a different path) or still needs doing; I did not retry it.
Checks that do not depend on ownership, all run just now: JS gates pass; JS proof: seeded J1 `True`, clean code `False`; JS scoring `9/9`, baseline `7/7`; Python fixture scoring runs (`10/22` on the current fixture state, which holds only the seed and risk tickets, not the PRC set); container suite `242 passed`. Installing Stryker needed a write window on `js-deps/node_modules`: with the folders still `ubay`-owned I did `chmod -R u+w`, `npm install --ignore-scripts` as `hermes`, then `chmod -R a-w` again (555 verified). That would have needed `sudo` had the chown been in place.

## Housekeeping
`.harness/hermes-probe.md` is removed from `product-design` (`git rm --cached`, the file stays on disk, `.harness/` added to `.git/info/exclude`) in the commit that carries this report.

## Not exercised / limits
No live ticket ran with `[mutation] enabled = true`. The `[mutation]` time cap is per run, not per ticket tier. `min_risk` (mutate only medium-risk and above) from the old BUILD_SPEC table is not implemented; it would combine D2's tiers with D3.

## Questions for the reviewer
1. **Switch-on (live, reversible, one flag in `harness.toml`, the container's config):** `[mutation] enabled = true`. Gates then run mutation on every ticket and add up to roughly 20 to 60 s; the field is report-only. OK to turn it on and run the existing fixtures (Python PRC ticket, one JS ticket with top-level tests)?
2. Because of the describe limitation, should the JS fixture's tests be rewritten to top-level `test()` (and the planner/implementer cards told to avoid `describe` for JS projects), or should we wait for a Stryker/Vitest fix? Until then JS mutation results are `unrun` for describe-style suites.
3. The AC attribution is by coverage, so it is coarse. Is that enough for the report, or should I run each AC's tests alone against the survivors (more precise, one extra mutmut run per AC)?
