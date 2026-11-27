# D20 review (`agent-harness` branch `d20-runner-evidence` @ `0458287`)

**Approved. Fast-forward `master` to `0458287e25d122daf91ab74845a6cbe392e8195f`** (it contains D19, so one
deploy covers both). Verified in the reviewing session on a fresh worktree: `522 passed, 3 skipped in 93.11s`;
ruff check and format are clean. I read the pipeline, the isolated scorer, the publisher, the alert and the
wiring into the runner, the loader and the decisions.

- **The order is built into the board,** not into the runner's timing: an unassigned `accept <KEY>` card after
  each scribe, which only the runner completes. A stopped or broken runner therefore holds the queue. Right.
- **The hidden suite runs in a throwaway container with no network,** from a mode-0700 folder that is refused if
  any worker mount contains it, and the old scorer now refuses a host-only folder. Your live check (59 of 59, and
  the worker container could not list the folder) is the evidence I wanted.
- **Evidence and block reports read host records only,** and publishing uses plumbing in a bare repository with
  fixed paths under the configured folder.
- **Within a pass, decisions are applied before the first acceptance run.** That is the order D19's review asked
  for.

## Your three questions

1. **The gate as the hold after a regression: accepted.** It is better than a new card: nothing to create, no
   window. A `release` decision for that ticket's key opens it.
2. **A worker with Kanban tools could complete a gate: accepted as detected, for now.** It is the same exposure
   the hold cards had. Prevention goes on the backlog (a board permission, or a separate owner for gate cards).
3. **Alerts to the Telegram home channel: accepted.** Ubay can name another chat later.

## Deploy (Ubay runs this; it installs both units)

```
harness-deploy 0458287e25d122daf91ab74845a6cbe392e8195f --install-unit
```

## After the deploy, in this order

1. **Post the seven exact ids** (`D19-code-review.md`). I push the `refresh_copies` and `retire_hidden`
   decisions in one commit.
2. **When both are applied, three live checks, before any FIX Lens ticket:**
   - **One fixture ticket through the new pipeline** (a sample repository, not `fix-lens`): the loader creates
     the `accept` card, the next card waits on it, the runner completes it after the scribe, and a second
     ticket loaded behind it starts only then. Report the card ids and the journal lines.
   - **One acceptance run on the real suite** with the kit's own tool against the trusted `main`, now that the
     copies are recorded. Expected: no regression; the two retired tests named apart; the new v1.2 files mostly
     failing as not built. Report the summary.
   - **One alert:** send a single test message through the alert path, so we know it arrives. Say in it that it
     is a test.
3. **Then stop and report.** Loading FXL-9 to FXL-13 waits for my go, which waits for Ubay's answer on the
   design clarifications (`fix-lens/technical-design-v1.2.1-proposed.md`).

## For the next kit change (not blocking)

- Remove the emoji from the alert text in `alert.py`: plain words only in anything the harness prints or sends.
- Record the backlog item from question 2 in `HANDOFF.md`.
- Step 6 of `D20-review.md` (delete the driver and `d6-driver`) stays for after the first FIX Lens ticket has
  gone through.
