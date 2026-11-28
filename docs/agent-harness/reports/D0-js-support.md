# D0: JavaScript test support (`agent-harness@e0789e5`)

Kit `master` = `e0789e5` (confirmed with `git ls-remote`). From a fresh clone of that commit: `141 passed`, ruff clean. In the container: `141 passed`. The 122 earlier tests pass unchanged (pytest defaults keep today's behaviour).

## 1. Runner choice, from evidence (container Node v26.12.1, npm 12.0.2)
`node --test`:
- `node --help` shows `--test-name-pattern`, `--test-reporter=junit` (works), but **no list-only mode**: nothing prints test ids without running them.
- Empty test dir: `ℹ tests 0`, **exit 0**, so there is no distinct "no tests" code.
- A syntax error is reported as one case named after the file (`failure="test failed"`), without the real reason.

So `node --test` fails requirements 1 and 4. **Vitest 5.1.2** (dev dependency of the target repo, installed with `npm install --ignore-scripts` as `hermes` in the container; not a kit dependency):
- list: `vitest list` prints `test/a.test.js > g > adds` per test; `--json` also exists. Syntax error in a file: exit 1.
- run one: `vitest run <file> -t "^g > adds$"`. The `-t` pattern is matched against `suite > test` (without the file). Other tests are written to the JUnit as `<skipped/>`.
- JUnit: `vitest run --reporter=junit --outputFile=x.xml`; `classname` = file, `name` = `suite > test`, `<failure type="AssertionError">` for `expect` and for `node:assert`.
- "No tests": `vitest list` with nothing prints nothing and exits 0; so JS config sets `no_tests_exit_codes = []` and an empty list is simply an empty list. A collection failure is exit 1, an error.
- Failure types seen: assertion `AssertionError`; timeout `TestTimeoutError`; syntax error `RolldownError` (reported as a case named after its file); missing import `Error`.

## 2. What moved into config (pytest values stay the defaults)
| Was hard-coded | Now |
|---|---|
| `collect_ids` accepted exit 5 | `commands.no_tests_exit_codes` (default `[5]`) |
| id split on `::` (gates, resolve, prover check) | `commands.id_sep` (default `::`); tokens `{id}`, `{file}`, `{name}`, `{name_re}` for `test_one` and `prove_cmd` (`{name_re}` is an anchored, escaped regex) |
| prompts said "pytest node id" | `commands.collect_display`, `id_example`, `id_kind` (defaults = old wording) |
| `proof_outcome`: pytest `assert`/`DID NOT RAISE` only | plus `review.proof_failure_types` (JUnit `type` values; Vitest: `["AssertionError"]`). Syntax, import and timeout types never count. When a run lists other tests as skipped, they are ignored; exactly one real case is still required |
| scoring: `.py`, `tests/`, `def test_` | `[score] junit_style`, `hidden_glob`, `tests_dir`, `count_regex`, `cmd` |
| nothing for dependencies | `commands.deps_dir`: an installed `node_modules` is symlinked into each fresh worktree (gates, prover, scoring); installing is not a gate step |

Also: `score --trusted-root` (tests use a throwaway trusted root), `tools/merge_config.py` (overlay a runner config on `harness.toml`).

## 3. JS fixture `eval/fixture-js/`
Repo baseline (`src/text.js` + test), tickets JSN-1 (slugify) and JSN-2 (chunk), hidden tests (4 + 5), reference solution, seeded variant **J1** (`chunk` drops the last short chunk), and `harness.js.toml` (the overlay). Variant plumbing in `variants.py` is still Python-fixture only; J1 is verified as data and by a hidden-test run (below), not through the variant runner.

## 4. Run in the container (not on the host)
- **Gates** (`harness.gates` via `docker exec` as `hermes`) on `harness/JSN-1` with the JS overlay: `passed: true`; `base_ids 2`, `head_ids 5`; new ids `test/slug.test.js > slugify > lowercases and hyphenates`, `... collapses separators`, `... rejects non-strings`; `valid_tests` = all three (they fail on base, pass on head), `fails_on_head []`, `missing_acs []`, `pass_to_pass` ran and passed.
- **Prover**, via the configured `prove_cmd` (`docker exec --workdir <worktree> hermes node_modules/.bin/vitest run {file} -t {name_re} --reporter=junit ...`) with the same "keeps the short last chunk" test:
  - seeded bug J1: exit 1, outcome `(True, 'AssertionError: assertion failed')`;
  - clean code: exit 0, outcome `(False, 'test passed')`.
  The model-written part (the prover writing the test) was not run; the test was written by hand. The execution, JUnit and outcome path is the real one.
- **Scoring** against a throwaway trusted main with JSN-1 and JSN-2 approved: `jsn1.test.js: 4/4`, `jsn2.test.js: 5/5`, `hidden: 9/9 pass; baseline: 7/7 pass`.
- J1 against the hidden tests: `jsn2.test.js` 4 pass, **1 fail** (`short last chunk`).
- The throwaway trusted root was `work/js-trusted-root` inside the kit; nothing was written to `~/.local/state/agent-harness/`, nothing to Hermes config, cron, services or containers.

## 5. Tests added (`tests/test_js.py`, 19)
Collect lists ids; a collection failure is an error; "no tests" is not (declared per runner); pytest exit 5 still empty by default. Proof outcomes from **real Vitest JUnit files** (`tests/data/vitest/`): `expect` failure and `node:assert` failure count, a passing test is false, syntax error, timeout and import error give `None`. Filtered runs with skipped cases count one test. Scoring reads Vitest JUnit (a file that cannot load is an `error`). FAIL_TO_PASS / PASS_TO_PASS with JS ids through `run_gates` using a fake runner in Vitest's id format. Variant edit applies exactly once.

## Limits
- Vitest only; `node --test` is not supported (no list mode).
- Dependencies are installed once into `commands.deps_dir`; a ticket that changes `package.json` needs a re-install by hand.
- The model-written proof test and the live card text for JS were not exercised.

## Questions for the reviewer
- OK to start D1 after approval? (Reading only the "After D0" queue; no live change is needed for D0.)
