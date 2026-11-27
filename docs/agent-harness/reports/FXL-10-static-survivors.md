# FXL-10's five "survivors" (FXL-10-landed-review), and D22 after approval

Read-only on everything live. Nothing in the kit, config, dependencies or board changed.

## D22
`agent-harness` `master` is fast-forwarded from `7c190a2` to **`0dee234ccbcaa6397c041de8d3969b2edb17baae`**. **Not deployed:** the host kit is still `7c190a2`. The audit-tool limit is in `HANDOFF.md`.

## The five mutants
The gate kept no raw Stryker report, so I reproduced the run: `60b1211..80116ec`, plain copies, a throwaway `--network none` container, nothing left out (the static check was not selected in the gate's run either). **Same counts as the gate: 104 killed, 5 survived, 0 timeout, 0 without tests, 0 unrun.** (Run with the `0dee234` code and an empty list.)

All five are in `src/timeline.js`, in the `ORDER_NAMES` table:

| id | line | mutator | status | static | coveredBy | killedBy | testsCompleted |
|---|---|---|---|---|---|---|---|
| 83 | 9 | ObjectLiteral | Survived | **true** | 1 test (`69`) | none | 1 |
| 84 to 87 | 10 | StringLiteral | Survived | **true** | 1 test (`69`) | none | 1 |

Test `69` is `test/page.test.js > test_page_second_decode_replaces_output_without_retaining_paste`.

## Why: yes, they are static, and each was run against one test only
- `ORDER_NAMES` is evaluated once, when the module loads.
- `page.test.js` loads the app **inside** that test (line 26, `await import('../src/main.js')`), so Stryker attributes the load-time code to it. A mutant that is both static and covered by a test is what Stryker calls hybrid.
- With `ignoreStatic` on, a static mutant with no covering test is `Ignored`; a hybrid one **is run, but only against its covering tests** (`@stryker-mutator/core` 10.1.1, `mutant-test-planner.js`, the `ignoreStatic && coveredBy.length` branch).
- The tests that would kill these (your 9 in `timeline.test.js`) import the module at the top of the file. They are not in `coveredBy`, so Stryker never ran them against these mutants.

So "Survived" here means only "the one page test did not fail". It says nothing about the other tests.

## How many of the 72 FXL-9 trial survivors have this shape
**2 of 72.** Both are in `src/framing.js`, static, covered only by the same page test, 1 test completed:
- line 2, `const SOH = "\x01";` to `""`
- line 4, `const isLineEnd = …` to `() => undefined`

**The other 70 are not static.** This change would not explain them. (That run is my trial with the static check left out, not the official rerun, and I have not checked any of the 70 by hand.) In the same run, 2 static hybrid mutants were **killed** by that page test; those kills are real.

## Proposed smallest change (not built)
In the kit's counting loop (`mutation.py`, `run_stryker`), while `ignoreStatic` is on:
- a mutant with `status == "Survived"` and `static == true` goes into a new count, **`static_not_measured`**, not into `survived`, and **not into the survivors list** that the reviewer and the evidence get;
- the evidence line shows it: `... unrun 0, static (not measured) 5`;
- `Killed` and `Timeout` static mutants stay as they are, since a test did detect them.
Tests: this shape, a static kill, and a non-static survivor. On the two runs above it gives FXL-10 104 killed, **0** survived, 5 not measured; the FXL-9 trial **70** survived, 2 not measured.

The cost: a static mutant that no test would catch is also shown as "not measured". The alternative is `ignoreStatic: false`, which runs **all** tests against every static mutant. That really measures them, but takes longer under the 5-minute cap (the FXL-9 trial already used 2 min 24 s), and I have not timed it. I suggest the counting change.
