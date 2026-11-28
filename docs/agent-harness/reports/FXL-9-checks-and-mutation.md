# FXL-9: the two landing checks, and why Stryker crashed (V12-go-review3, FXL-9-landed-review)

Read-only. Nothing changed in the kit, its config, the dependencies, the board or any repository. FXL-10 was running.

## Check 1: did the isolated hidden run happen? **Yes** (from the runner's records, not the gate's summary)
- `pipeline.json`, FXL-9: `enabled: true`, **77 of 166**, `trusted_main 60b1211023d1…`, `regressions: []`, `gate_was_open: false`, `ran_beside: []`, `errors: 0`, no blocks, not held. Scribe done 12:35:38, finished 12:36:09.
- Acceptance history: 77 `passed` (67 before), with the run `{FXL-9, 60b1211, 77}` recorded; one retired entry.
- `scoring/` is empty, no `harness-score-*` container is left, and no `acc-*.test.js` is under `work/`.
- Gate `accept FXL-9` (`t_86adfba0`) completed 12:36:08; its run record has no profile and no worker pid. (Its summary still says "hidden suite passed" with 47 tests failing as not built: "passed" means no regression. Already on the kit list.)

## Check 2: did the runner publish the evidence? **Yes**
Commits `ba2a47d` (`FXL-9.md`, `FXL-9.patch`) and `6722029` (`STATE.md`), both by `harness runner`; its PR comment "FXL-9 completed on the trusted main: patch and evidence ... (ba2a47d)" is there; the outbox is empty. The published patch matches `format-patch` of the trusted repository (signature lines aside).
No FXL card from 9 to 13 has any `blocked` or `unblocked` event so far.

## Why Stryker crashed
From the kept `work/runs/FXL-9/mutation-output.log`:
```
12:22:53 INFO  Instrumenter Instrumented 2 source file(s) with 447 mutant(s)
12:22:55 ERROR DryRunExecutor One or more tests failed in the initial test run:
	test_static_checks_ignore_comments_and_pass_delivered_sources
		src/framing.js: expected [ '/\bnew\s+Function\b/' ] to have a length of +0 but got 1
12:22:55 ERROR Stryker There were failed tests in the initial test run.
```
- The delivered `src/framing.js` at `60b1211` contains `new Function` **0 times.**
- **Stryker adds it.** To instrument a file it prepends a helper that contains it: `@stryker-mutator/instrumenter/dist/src/util/syntax-helpers.js:15`: `... || new Function("return this")();`
- The project's static check reads every file under `src/` **as text** and forbids `new Function` (design 8.4). In Stryker's sandbox it reads the instrumented copy and fails, so the unmutated first run fails and Stryker stops.

### Why not on every earlier ticket, when the old check had the same rule
The old `test/static-checks.test.js` also forbade `new Function` and also scanned `src/`. The difference is **whether Stryker runs that test at all.** Its Vitest runner (10.1.1) defaults to running only tests **related by import** to the mutated files (`vitest.related`, which the kit does not set; `vitest-test-runner.js:158-198`). The check reads sources through `fs`, so it imports none of them.
- Before FXL-9 it imported only `vitest`, `node:fs` and `jsdom`: never related, so never run. That is why my D19 reproduction on FXL-8's code passed its first run with 42 tests.
- **FXL-9 moved the check into a new module, `tools/audit-source.mjs`, which the test imports.** In FXL-9 that module was also one of the two mutated files. So the test became related, ran, and read the instrumented `src/framing.js`.

So it needs **both:** the diff changes `tools/audit-source.mjs` (so the static check is selected) **and** changes a `.js` file under `src/` (so there is an instrumented file for it to read). It is the interaction of FXL-9's new module with Stryker's instrumentation; not the kit's D19 change, and not a dependency fault.

## Will FXL-10 to FXL-13 hit it?
**I expect not, unless one of them changes `tools/audit-source.mjs`.** None of the four tickets asks for that; their text only says the check is enforced since FXL-9. FXL-10's plan names `src/execution.js`, `src/timeline.js`, `test/static-checks.test.js` and `test/timeline.test.js`: editing the **test** file does not select it, since test files are not mutated and it imports no `src/` module. This is a reading of the code and the plan, **not yet shown on a run:** I will check FXL-10's own mutation log when its gates have run, and say so on the PR. Two ways it would come back: an implementer touching the audit tool anyway, and **FXL-14**, if it extends that tool (your note about `<template>` content would do exactly that).
**Independent of the crash,** the same selection rule means mutation never runs the source-text checks unless the tool itself changes. They still run in the gates.

## For the next kit change (not made, not tried)
Give the reviewed config a short list of **source-text tests** (for `fix-lens`: `test/static-checks.test.js`) and leave them out of Stryker's runs only, for example through a Vitest config the kit writes into the mutation sandbox. The gates keep running them on the real code. Such tests cannot kill a mutant meaningfully, as they judge the text of the file and Stryker rewrites it. After the change: rerun mutation for FXL-9 (and any other ticket that missed it) on its landed commit, as your review says.
Also noted for that change: a mutation error named in `STATE.md`.
