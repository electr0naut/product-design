# D27 part 1, second review (`d27-claude-limit-r2` @ `be46d02`): approved

**Approved. Fast-forward `master` to `be46d0267f4082a3b0a87b9ac4d4c7444bc1d008`.** Fresh worktree at that
commit: `830 passed, 3 skipped in 98.76s`; `ruff check` and `ruff format --check` clean. `git range-diff` shows
the four commits I reviewed at `f326802` unchanged, on top of `dc3b60c` (J-3), plus the one R2 commit. Nothing
under `jobs/` or `systemd/` changes, so no root-owned file has to be reinstalled.

- **R1 is shown** on the real `hermes kanban` (2026.9.24), scratch board, no network: `schedule` on a claimed
  and on a ready card, the status name `scheduled`, the ready list leaving it out, `unblock` back to `ready`,
  ten park and unpark rounds without a counter firing, three dispatcher ticks leaving scheduled cards alone.
  The two rules the first version did not know (`schedule` refuses a scheduled or blocked card; `block` refuses
  a scheduled one) are now in the code and in the stand-in board. Your stated limit stands: the live gateway's
  own dispatcher has not met a scheduled reviewer card.
- **R2 is done:** a refused park no longer fails the pass; it is tried on the next two passes and then ends as
  the old transient block; a park that took but lost its answer counts as done; a refused unpark is said once
  and retried, because the board will not block a scheduled card.
- **I broke six rules by hand; the tests caught five.** Not caught: letting a timed-out call succeed when a
  complete result is already in its output. That would be harmless (the result is whole), so it does not block;
  add a test for it with the next change.

## Deploy (Ubay; I give him the line in chat, the board is idle and no job is queued)
```
harness-deploy be46d0267f4082a3b0a87b9ac4d4c7444bc1d008
```
It carries J-3's change too, so it copies the new alert script into the container. The previous version is
`6ff69fa`.

## After the deploy, read-only
1. The usual: copies identical, imports, `--help`; two clean runner passes.
2. One real review call through the new path is not needed again; you made one. **The first real limit is the
   real test.** When one happens, report the raw `rate_limit_event` and result fields (no prompt text), so the
   matcher can be checked against reality.

## Then, in this order
1. `D27-proposal.md` and the free bake-off for part 2 (`D27-go-review2.md`). The bake-off is also my best
   evidence on a wider question: in ten v1.2 tickets the Claude review cost about $9 (notional) and proved no
   finding. Include, per model, how its verdicts on those tickets' findings compare.
2. The small kit items for the job files (`J-20261127-3-review.md`): they can be the next **job**, not a
   standing-session task.
