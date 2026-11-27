# V12-go-review6: FXL-9 mutation rerun, the two decisions, and the load of FXL-17 then FXL-14 to FXL-16

## 1. `tools/rerun_mutation.py FXL-9` (official, from the deployed kit `6c483e6`, no card on the board unfinished)
Exit 0, 14:12:29 to 14:14:45. Output, verbatim:
```
{
 "key": "FXL-9",
 "repo": "fix-lens",
 "base": "e721f3186288ac0f93d0403a7eb2be959c8099c7",
 "head": "60b1211023d1f00874e6231d5c98c94501613581",
 "mutation": {
  "ran": true,
  "killed": 187,
  "survived": 70,
  "timeout": 32,
  "no_tests": 156,
  "unrun": 0,
  "incomplete": false,
  "static_not_measured": 2,
  "source_text_tests_left_out": [
   "test/static-checks.test.js"
  ]
 },
 "record": "/home/ubay/.local/state/agent-harness/records/FXL-9/001795785285040-mutation-rerun-w0tm90.json",
 "raw_report": "/home/ubay/.local/state/agent-harness/records/FXL-9/001795785285040-mutation-rerun-w0tm90.stryker-report"
}
```
**187 killed, 70 survived, 32 timeout, 156 without tests, 0 unrun, complete, 2 static (not measured)**: as expected.
**Raw report:** the `raw_report` path above (host-only records).
**Against my trial,** from that raw report, changed lines, matching each mutant by line, column, mutator, replacement, status and static flag: **identical** in both files (`src/framing.js`: 70 survived and 2 static survived, 25 without tests, 32 timeout, 187 killed of which 2 static; `tools/audit-source.mjs`: 131 without tests). So the lines in `FXL-9-trial-survivors.md` are the official ones; its mutant ids come from the trial and were not compared. No later ticket's mutation run has errored. The tool left no scratch folder behind.

## 2. `D-20261127-6` and `D-20261127-7`: both applied, copies verify
Runner journal at 14:06:03:
```
decision applied D-20261127-6: retired 5 hidden test(s) from the fix-lens history
decision applied D-20261127-7: refreshed the fix-lens copies from 9448c0b99295: design sha256 4c2cb3fd5236, 17 hidden test files
```
The kit's `copies.verify` passes at `9448c0b99295` with 17 hidden files (next section). acceptance history: 116 passed ids, 2 retired entries ([2, 5] ids).

## 3. Step 2 re-check, 14:14:55, verbatim
```
ok   cards for FXL-14..17: []
ok   worker cards running: []
ok   worker cards ready or blocked: []
ok   host kit: 6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953
ok   host reviewed-sha: 6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953
ok   container kit: 6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953
ok   copies verify: commit, design, hidden files: ('9448c0b99295', '4c2cb3fd5236', 17)
ok   acc-render absent, acc-framing-rules present: ([], True)
ok   worker reading copies: ['4c2cb3fd5236']
ok   fix-lens trusted main: 8881fce
ok   fix-lens work repo (main, changes): ('8881fce', '')
ok   D-20261127-6 and -7: ['applied', 'applied']
ok   pipeline: unfinished, held, or FXL-14..17 entries: []
ok   runner status ok: True
ok   runner timer: active
ok   old driver running: 0
RESULT: nothing differs
```

## 4. Load
Ticket files copied from the branch (last commits: FXL-17 `445c622`, FXL-14 `1b47d32`, FXL-15 `ab1db50`, FXL-16 `7afa4d1`). Loader from `~/dev/agent-harness-d12`, whose `src` and `tools` equal the deployed `6c483e6`; a dry run first. No Telegram card subscriptions, as for the first batch.
- **Call 1, FXL-17 alone** (14:16:03, exit 0; log `work/v12-fxl17-load.log`).
- **Call 2, FXL-14, FXL-15, FXL-16** (14:17:07, exit 0; log `work/v12-batch2-load.log`). FXL-17's triage had started by then; no later FXL-17 stage had.

| ticket | triage | planner | implementer | gatekeeper | reviewer | scribe | accept |
|---|---|---|---|---|---|---|---|
| FXL-17 | t_92bca993 | t_6905d5ff | t_dde83dee | t_cc28b233 | t_7de9897e | t_51c1cd44 | t_9274729e |
| FXL-14 | t_dd6389b0 | t_bbe71d47 | t_fca290c0 | t_ff7465b1 | t_4ff072a0 | t_86269b16 | t_0651a5c1 |
| FXL-15 | t_5303f899 | t_d2004843 | t_fb80ebfe | t_0c234ab4 | t_b3087bc2 | t_1bf9d87b | t_bee107ec |
| FXL-16 | t_5c6fcb50 | t_f107d370 | t_22102270 | t_1dfef4cc | t_4a1b0dc5 | t_91b6240e | t_975106d9 |

**Wait links, read from the live board, verbatim** (each triage also has its own ticket card as a parent):
```
FXL-17 · triage (t_92bca993) waits on: FXL-17
accept FXL-17 (t_9274729e) waits on: FXL-17 · scribe | assignee: None | todo
FXL-14 · triage (t_dd6389b0) waits on: FXL-14, accept FXL-10, accept FXL-11, accept FXL-17, accept FXL-9
accept FXL-14 (t_0651a5c1) waits on: FXL-14 · scribe | assignee: None | todo
FXL-15 · triage (t_5303f899) waits on: FXL-15, accept FXL-11, accept FXL-14
accept FXL-15 (t_bee107ec) waits on: FXL-15 · scribe | assignee: None | todo
FXL-16 · triage (t_5c6fcb50) waits on: FXL-16, accept FXL-12, accept FXL-13, accept FXL-15
accept FXL-16 (t_975106d9) waits on: FXL-16 · scribe | assignee: None | todo
cards for FXL-14..17: 32
not done: [('running', 'FXL-17 · triage')]
```
**FXL-14's triage waits on `accept FXL-17`.** After the load, 14:17:30: trusted `main` still `8881fce`, work repo clean, no `acc-*.test.js` under `work/`, runner ok.

## From here
Watching as before; blocks reported, not unblocked; each ticket's mutation line reported as it lands. D24 is being built in a clone; nothing is deployed.
