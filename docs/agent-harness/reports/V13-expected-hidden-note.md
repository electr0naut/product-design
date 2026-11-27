# V13-go-review, step 4: it is a kit change, so it needs a review and a deploy before step 5

Read the review. Steps 1 to 3 are yours; **nothing is built yet.** One thing to plan for:

- `[expected_hidden.fix-lens]` is in **`harness.host.toml`, a tracked file of `agent-harness`** (D24), not a host-only setting. Adding FXL-19 to FXL-21 is therefore a commit on a branch with tests, **your review of that commit, then Ubay's `harness-deploy`**, all before `load_tickets` (step 5). It must also wait for an idle board.
- **I wait for your step-3 commit:** it names the new paging test files. Then the change is three table lines. A listed file missing from the host copy is an error before the run (D24), so the order stays: your commit, `refresh_copies`, the table's deploy, then load.
- It is the next kit change, so the pending test (a timed-out call is no success even with a complete result in its output, `D27-code-review2.md`) can go with it. The standing session can build it, or a job, as you say.

Seen at 19:12: no `FXL-19` to `FXL-21` ticket is in `fix-lens/tickets/`, the board has no running, ready or blocked card, and the deployed kit is `be46d02`. The validation files are not acted on.
