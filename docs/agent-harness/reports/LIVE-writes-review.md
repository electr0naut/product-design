# The kit's tests wrote a live file: audit first, then fix (instruction)

Your correction is accepted on both points. The refresh came before the load, the copies verify at
`23952fd05985`, and FXL-17 started after it. Good that you said the earlier line was stale.

The second point matters more: **a test suite run on the VM wrote the runner's live status file.** A false
"runner failing" for under a minute is harmless. The question is what else a suite run can write, with cards
running.

## 1. Audit, now, read-only, before any more suite runs on the VM
- **Do not run the kit's test suite on the VM host again until this is fixed.** Run it in a throwaway container
  with no access to `~/.local/state/agent-harness` and the live kit, or not at all.
- List every file under `~/.local/state/agent-harness/` and under the live kit's `work/` whose modification
  time falls inside one of your suite runs today (D21, D22, D23, D24 so far). For each: what wrote it, a test or
  the runner. The runner's own passes fall in those windows too, so name which is which from the journal.
- Say plainly whether any of these could have been touched by a test: the acceptance history, the copies and
  their recorded hashes, `pipeline.json`, the records of a ticket, the outbox, the decisions ledger, the fix
  ledger, `state.json`.
- Check now that the acceptance history still shows what the runner last recorded (the run for FXL-13 on
  `8881fce`, 121 passed, and the retirements), and that `pipeline.json` lists exactly the tickets loaded.

Report as `LIVE-writes-audit.md`. If anything other than `runner-status.json` was written by a test, say so in
the first line and stop the D24 work until I have read it.

## 2. The fix, as its own commit on the D24 branch
- An autouse fixture in `tests/conftest.py`: for every test, `HOME` and every path the kit derives its trusted
  root, kit folder and status files from point into `tmp_path`. No test may opt out.
- One test that fails if the trusted root or the status file path resolves outside the test's temporary folder.
- The two tests in `tests/test_hostkit.py` use that, and no real kit path.
- Say which other tests relied on a real path.

I review that commit apart from D24.
