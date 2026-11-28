# D23: static mutants counted apart

Branch `d23-static-mutants` of `agent-harness`, commit **`9e04d00e291e84aeb6b7819ec32e63af29703a2c`**, one commit on `0dee234` (so it contains D22). **Not merged** (`master` is `0dee234`), **not deployed**, nothing live changed.

## A correction to my last report
`FXL-10-static-survivors.md` said the survivors list goes to "the reviewer and the evidence". **The host's automated review gets no mutation result at all:** `reviewer.py` builds its prompts from the acceptance criteria, the diff and, for the spec pass, the ticket and design. It never reads `gates.json`. Survivors reach `gates.json` (which the gatekeeper passes on and the scribe reads) and the published evidence (which you read). Your "review input" wording followed my mistake. So I **did not change the review prompt**; the count is in the two places that do exist. If you want the automated review to see mutation results, that is a new change and needs its own instruction.

## Built
- A `Survived` mutant with `static: true`, while `ignoreStatic` is on (now one constant used for the config and the count), goes into `static_not_measured`: not into `survived`, the survivors list, `survivors_by_ac` or `uncovered_survivors`.
- A static survivor for which **no test was run** stays `unrun`, as before, so that warning (a broken engine version) is not hidden.
- `Killed` and `Timeout` are unchanged. `ignoreStatic` stays on.
- In words: a new `summary` field in the gate's mutation result, and the evidence line `... unrun 0, static (not measured) 5; ...`. Older records and mutmut have no such count, and their line is unchanged.
- The rerun tool prints the new count.

## Tests
Fresh clone of `9e04d00`: format and ruff clean, **594 passed, 3 skipped**. `tests/test_d23.py` (stand-in engine):
```
test_a_static_survivor_is_counted_apart_and_not_listed PASSED [ 20%]
test_static_kills_and_timeouts_stay_as_they_are PASSED [ 40%]
test_a_survivor_that_is_not_static_stays_a_survivor PASSED [ 60%]
test_a_static_mutant_with_no_test_run_still_counts_as_unrun PASSED [ 80%]
test_the_evidence_line_shows_the_count_in_words PASSED [100%]
============================== 5 passed in 0.16s ===============================
```
**Real Stryker**, this branch's code, throwaway no-network containers, same ranges as before:

| range | result |
|---|---|
| FXL-10 | killed 104, **survived 0**, timeout 0, no tests 0, unrun 0, **static (not measured) 5**; no survivors listed |
| FXL-9, with D22's list | killed 187, **survived 70**, timeout 32, no tests 156, unrun 0, **static (not measured) 2** |

Both are what I predicted.

## Before the deploy: the official FXL-9 rerun will not give you all you asked for
`D22-code-review.md` asks for the survivors in `src/framing.js` with their lines. The kit lists at most **30** survivors (`max_survivors_listed = 30`; the FXL-9 run above lists 30 of 70), lists **no** untested mutants, and `rerun_mutation.py` **deletes Stryker's raw report** with its scratch folder. So the official run would give correct counts, but a partial list and no lines for the untested ones.
**Proposed, not built:** the rerun tool also saves the raw `mutation.json` beside its record in the host records (it already saves the log there). A few lines, plus a test; the gate is unaffected. If you want it in this deploy, tell me and I will add it on this branch. Otherwise `FXL-9-trial-survivors.md` is the full list, from a trial.
