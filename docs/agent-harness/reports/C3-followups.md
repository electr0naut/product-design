# C3: follow-ups after Phase C (items 2, 5, 6; 1, 3, 4 pending)

Kit commit `agent-harness@e043d5f` (pushed, `git ls-remote` confirmed). 112 tests pass on host and in container; ruff clean.

## Done
- **Item 6, backup check (read-only):** the 03:00 run on 2026-11-25 completed and pushed ("Backup complete and pushed: 2026-11-25 03:00:26", commit `89753cb` in the backup repo). A names-only scan of the pushed `config.yaml` found 0 secret-named keys with a plain value, so the new redaction held.
- **Item 2, bounced ticket no longer holds the queue:** new `harness.queue`. The loader writes `work/cards/queue.json` (order and `blocked_by`); the host runner calls `relink_bounced` before every review pass (every minute). When a ticket's `triage` card is blocked and the next ticket is not `blocked_by` it and has not started, the runner unlinks the next ticket's triage from the bounced ticket's `scribe` and links it to the nearest earlier ticket's `scribe`, and logs the change. Tests: an independent later ticket proceeds; a dependent one keeps waiting; no queue file or no bounce changes nothing.
- **Item 5, prove-worktree symlink race:** the proof test is now copied between the two worktrees with `copy_nofollow`, which opens each path component relative to its parent with `O_NOFOLLOW` (and `mkdir` relative to the parent), so a worker cannot swap a directory for a symlink between the check and the copy. Test: a symlinked file or directory at the source or the destination is refused and the target is untouched.

## Pending
- **Item 1, Codex planner check:** after 2026-11-26 08:21 CET.
- **Item 3, Telegram alerts through a Hermes no-agent cron script:** this creates a cron job (and a script in the Hermes data folder), which the builder rules say needs the user's approval. Not started; I will ask the user.
- **Item 4, deterministic gatekeeper:** not started. I propose running `harness.gates` from the host runner through `docker exec`, as `prove_cmd` does, and replacing the gatekeeper card with a status step; this changes the card graph, so I would like your design review first. Question for the reviewer: should the runner also complete the gatekeeper card with the gates report as metadata, or should the gates run before the card exists?
