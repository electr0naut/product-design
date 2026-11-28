# Phase C: user decisions (2026-11-25)

- **Telegram:** working. The "PRC-6 · triage blocked" alert reached the group.
- **Alert set:** the reduced one. Every card subscribes to `blocked`, `gave_up`, `crashed` and `timed_out`.
  Only the `scribe` card also subscribes to `completed`, giving one "done" ping per ticket. Change
  `--notify-telegram` in the loader to match, with a test, before loading.
- **Timing:** run Phase C **now**, with the planner on Qwen. After Codex resets (per the user on 2026-11-25: in about 18 hours, early on 2026-11-26), do one
  planner run to confirm that the Codex route works.

Everything else is as in `B6.1-review.md` ("Phase C: cleared").
