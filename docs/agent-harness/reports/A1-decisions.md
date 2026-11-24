# Phase A1: user decisions on cron jobs (container)

The user chose these jobs. Apply them only after the user tells you to start A2; take the backups
(A2) before changing any job.

| ID | Name | Decision |
|---|---|---|
| 50fbaafad58b | hermes-nightly-backup | **keep**; investigate the exit 128 from its 03:00 run and report the cause |
| 1b69780181bc | discord-gateway-watchdog | **keep** |
| 6d1f41c29a21 | Health check 10 AM | **keep** |
| 412b87173203 | Health check 10 PM | **keep** |
| 437f83fb9805 | International Markets Daily Briefing | **remove** |
| 76028a4a5646 | call-home-insurance | **remove** (one-time date passed) |
| 7606fb1705ec | Agentic Stack setup progress | **remove** (paused) |
| 21848fb9969c | OpenAI Codex <-> DeepSeek failover | **remove** (paused; replaced by the fallback chain) |
| 23bf36de3892 | AI News Daily Briefing | **pause**, not remove (user gave no preference) |
| 0c7aed2555b3 | International Politics Daily Briefing | **pause** |
| 525496d2acdd | news-push-to-iphone | **pause** |
| 9246ce6dafc9 | monitor-watched-emails | **pause** |
| b9790b7525fb | Amazon delivery watch | **pause** |
| 778a3fc05bdd | Daily personal-care reminder | **pause** |

Pausing can be undone with `hermes cron resume <id>`. Paused jobs that the user doesn't resume can be
removed later.

Commands, run inside the container (`docker exec hermes hermes cron ...`). Use the documented verbs
`remove <id>` and `pause <id>`. Afterwards, show `hermes cron list` as a table.

Still open, and not to be applied:
- the runtime decision: keep the container, or move to the host;
- approval of the A2 backups.
