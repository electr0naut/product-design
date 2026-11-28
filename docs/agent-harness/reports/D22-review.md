# D22: keep source-text tests out of Stryker's runs, and rerun mutation for a landed ticket (instruction)

`FXL-9-checks-and-mutation.md` is accepted: both landing checks are met, and the Stryker cause is shown from its
own log (the static check read Stryker's instrumented copy of `src/framing.js`, which contains `new Function`).
I agree with your reading of when it recurs, and with the fix you propose.

**Build it, on a branch of `agent-harness`, from `7c190a2`. Do not merge, do not deploy, and do not touch the
live kit, its config or the dependencies: cards are running.** Building and testing happen in a clone only.

## What to build
1. **Source-text tests.** A list in the reviewed host config for a repository (for `fix-lens`:
   `test/static-checks.test.js`). Stryker's runs leave those files out; the gates keep running them on the real
   code. An entry that names no existing test file is an error, not a silent skip. The mutation report names
   the files left out.
2. **Rerun for a landed ticket.** One tool that runs mutation for a ticket on its landed commit range, in a
   throwaway worktree, with the same settings and the same changed-line ranges as the gate would use, and
   writes the result beside the ticket's other run records without changing anything else. It refuses to run
   while a worker card of that repository is running. Say first whether something close exists already.
3. **A mutation run that errors is named in `STATE.md`** under the ticket, so it is seen without opening the
   evidence.

Nothing else in this change. The journal line, the gate summary wording, finished tickets in `STATE.md` and the
deploy tool's undo line stay on the list for a later one.

## Tests I will look for
- With the list set, a sandbox whose static check would fail on instrumented text still gets a mutation report
  (the FXL-9 case, reduced), and without the list the same case fails as it did.
- The gates still run the listed test.
- The rerun tool on a small sample repository: same result as the gate's run for the same range, and the
  refusal while a card is running.
- A fresh-process import of the new tool (it joins `tests/test_d21.py`'s lists).

Report as `D22-mutation-source-text.md` with the commit, the test output, and a run of the reduced FXL-9 case.

## After my review
Ubay deploys at a moment when no card is running. Then you rerun mutation for FXL-9, and for any later ticket
whose mutation run errored, and report the results. v1.2 is not called finished before those are in.

## FXL-10's mutation log
Report it on the PR when its gates have run, as you say: whether Stryker wrote a report, and the counts.
