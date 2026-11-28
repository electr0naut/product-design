# D21 review (`agent-harness` branch `d21-import-fix` @ `7c190a2`)

**Approved. Fast-forward `master` to `7c190a2d696add2fb63f4d409a03e34498e018eb`.** Verified on a fresh worktree
at that commit: `568 passed, 3 skipped in 99.21s`; `ruff check` and `ruff format --check` are clean. The diff
against `c06cd27` is three files: the import moved into `evidence._passes`, the alert text, and
`tests/test_d21.py`. Nothing else changed.

- **The tests catch the bug.** With `evidence.py` and `alert.py` put back to `c06cd27`, `tests/test_d21.py`
  gives `10 failed, 35 passed` here: `loader`, `variants`, the six tools, the loader dry run and the alert text.
  The same ten you report.
- **The module list is taken from the folder,** and `test_every_tool_is_in_one_of_the_lists` fails when a tool
  is added without a case. `src/harness/` has no sub-packages, so the flat list covers every module.
- **The fresh process gets an empty `HOME`,** and the load-only cases assert that nothing was written. Good.
- **The smaller cut is the right one.** Moving `create_card` out of the loader is not needed for this.

I agree with your three limits: the dry run shows no gate links, the real command-line load path has never
run, and an import inside a function that is not reached is not covered. The fixture ticket check is there for
the first two.

## Deploy (Ubay runs this; the units did not change)

```
harness-deploy 7c190a2d696add2fb63f4d409a03e34498e018eb
```

Nothing is loaded and no card is running, so the deploy does not interrupt work. The previous version is
`c06cd27`.

## After the deploy, in this order

1. **Confirm the deployed kit, not a clone:** with the kit's own interpreter, `import harness.loader` as the
   first import of a fresh process, on the host kit and in the container copy, and `tools/load_tickets.py
   --help` from the deployed path. Report the three results.
2. **The fixture ticket check** of `V12-go-review.md`, added to `V12-live-checks.md`. It is the first real run
   of the load path, so report what a dry run cannot show: the `accept` card ids, that the second ticket waits
   on the first one's gate, the contents of `pipeline.json`, and the journal lines where the runner completes
   the gate.
3. **One more condition before FXL-9 to FXL-13:** Ubay's answer on the 02:02 test alert. If it arrived, quote
   his words in `V12-live-checks.md`. If it did not, or there is no answer yet, stop after the fixture check and
   report: a runner failure nobody hears about is not acceptable for an unattended batch.
4. **If all of that holds, load FXL-9 to FXL-13 only,** from ticket commit `1b47d32` or later, under the
   conditions of `V12-go-review.md` and `V12-go-review2.md`. Check 2 is not repeated.

## For the next kit change (not blocking)

- `tools/harness_notify.py` still has emoji in its messages. Same rule: plain words.
- The deploy tool's undo line and the order of the container reset (`D20-live-checks.md`).
