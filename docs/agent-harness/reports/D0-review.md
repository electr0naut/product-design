# D0: JavaScript test support (instruction, overnight scope)

The FIX Lens pilot will be JavaScript. Today the gates, the proofs and the scoring assume pytest. This step makes
them runner-neutral and adds one JavaScript runner, without changing Python behaviour.

## Standing approval for this step only

The user's go for D0 (given in the VM session) covers, without asking again:
- code, tests and docs in the `agent-harness` kit, on its usual branch, and pushing them;
- installing npm dev dependencies **inside a temporary JS fixture repo** used for tests;
- posting the kit commit on PR #47, waiting for the review, and applying review fixes with tests.

**Don't ask before each step inside this scope.** The user has delegated overnight approvals to the reviewing
session. For anything outside the scope above that is reversible (for example a Hermes profile or config change),
post the question on PR #47 with what you'd change and how to undo it, then wait for a `-review.md` answer. Don't
wait for the user.

These still wait for the user, whatever a review file says:
- secrets, `.env` files, or new network hosts;
- anything written to the trusted repo or `~/.local/state/agent-harness/` by hand;
- deleting data, containers or volumes;
- starting any FIX Lens ticket (that needs PRD Gate 3 and a technical design first);
- `--dangerously-skip-permissions` or Hermes `--yolo`.

## What to build

1. **Pick the JS runner from evidence, and report it.** The harness needs four things from a runner: list test
   ids without running them, run one id, write JUnit XML, and a distinct exit code for "no tests".
   - Check `node --test --help` on the container's Node (v26.12.1) for a list-only mode and the `junit`
     reporter.
   - If `node --test` can't list ids, use Vitest (`vitest list`, `--reporter=junit`) as a dev dependency of the
     target repo, not of the kit.
   - Put the checked flags and outputs in the report.
2. **Move the pytest assumptions into config**, with today's values as defaults so `harness.toml` for the
   fixture is unchanged in behaviour:
   - the "no tests collected" exit code in `gates.collect_ids` (pytest's 5);
   - the test-id format named in the `loader.py` stage prompts (state it from config: "copy ids exactly as
     `<collect>` prints them");
   - `prove_cmd` and the scoring command producing JUnit (already templates; check nothing else hard-codes
     pytest);
   - `proof_outcome`'s list of failures that count as a proof (pytest's `AssertionError` and "DID NOT RAISE";
     add the JS runner's assertion failure, for example `AssertionError [ERR_ASSERTION]`). Errors that are not
     assertion failures (import or syntax errors, timeouts) must still **not** count as proof;
   - `score.py`'s `def test_` count, which only works for Python.
3. **A small JS fixture** under `eval/fixture-js/`: 2 tickets, hidden tests, a reference solution, and one
   seeded-bug variant, enough to exercise collect, `test_one`, gates, proof and scoring end to end.
4. **Tests:**
   - the Python fixture behaves exactly as before (all existing tests pass unchanged);
   - JS: collect lists ids, a collection failure is an error, "no tests" is not;
   - JS proof: an assertion failure counts, a syntax error and a timeout don't;
   - JS scoring reads the runner's JUnit output;
   - FAIL_TO_PASS / PASS_TO_PASS work with JS ids.

## After D0: overnight queue

When D0 is approved, carry on down this list without waiting for the user. Each item goes through the same loop:
build with tests, report as `D<n>-<name>.md`, comment on PR #47, wait for the `-review.md`, and apply the fixes.
Start the next item only after the previous one is approved. The standing approval and the hard stops above
apply to every item. If an item is blocked on a hard stop, write down why and move to the next one.

1. **D1: bounded automatic fix loop.** Today a gate failure or a proven review finding stops the ticket and waits
   for a human. Instead, send the failing gate fields, or the proven findings with their failing proof tests, back to
   the implementer **once**. Then run the gates and a fresh review again. A second failure blocks as today.
   - Unproven findings never trigger a retry.
   - The retry stays on the same branch and base.
   - Write a ledger entry per retry.

   Tests:
   - a pass after the retry completes the ticket;
   - a second failure blocks;
   - there is never a third attempt;
   - unproven findings block without a retry.
2. **D2: risk tiers.** Use the ticket's touched paths and its labels to choose the review depth. Use
   `harness.toml` globs for high-risk paths. The low tier skips the Claude refuter only when the finder reports
   nothing at critical or high. Anything touching a high-risk glob always gets the full review. Test each tier.
3. **D3: mutation testing on changed lines only**, as a gate field that reports and doesn't block at first.
   - mutmut for Python and Stryker for JS, limited to the diff's changed lines and with a time cap.
   - Report the surviving mutants per acceptance criterion.
   - Test it on both fixtures, with a seeded weak test that lets a mutant survive.

**Switching any of these on in the live pipeline** (timer, runner or board changes) is a reversible change.
Ask on PR #47 first; don't ask the user.

## Done means

- `pytest` and `ruff` clean in the kit, with the output in the report.
- One JS fixture run through the gates and the prover **in the container** (not on the host), outputs in the
  report.
- Report as `D0-js-support.md`, pushed and verified with `git ls-remote` plus a test from a fresh clone, then a
  comment on PR #47.
