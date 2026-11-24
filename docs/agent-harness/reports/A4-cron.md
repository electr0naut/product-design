# Phase A4: cron decisions applied, 2026-11-24

User go received in the VM session. Commands: `docker exec hermes hermes cron remove|pause <id>`.

## Result

| ID | Name | Action | State now | Next run |
|---|---|---|---|---|
| 6d1f41c29a21 | Health check 10 AM | keep | active | 2026-11-25 10:00 |
| 412b87173203 | Health check 10 PM | keep | active | 2026-11-24 22:00 |
| 50fbaafad58b | hermes-nightly-backup | keep | active | 2026-11-25 03:00 |
| 1b69780181bc | discord-gateway-watchdog | keep | active | every 5m |
| 23bf36de3892 | AI News Daily Briefing | pause | paused | (resumes on request) |
| 0c7aed2555b3 | International Politics Daily Briefing | pause | paused | |
| 525496d2acdd | news-push-to-iphone | pause | paused | |
| 9246ce6dafc9 | monitor-watched-emails | pause | paused | |
| b9790b7525fb | Amazon delivery watch | pause | paused | |
| 778a3fc05bdd | Daily personal-care reminder | pause | paused | |
| 437f83fb9805 | International Markets Daily Briefing | remove | removed | |
| 76028a4a5646 | call-home-insurance | remove | removed | |
| 7606fb1705ec | Agentic Stack setup progress | remove | removed | |
| 21848fb9969c | OpenAI Codex <-> DeepSeek failover | remove | removed | |

Result: 4 active, 6 paused, 4 removed. Resume a paused job with `docker exec hermes hermes cron resume <id>`.
Note: the removed jobs' scripts are still in `/opt/data/scripts/` (not deleted).

## Nightly backup exit 128: cause

- The old `hermes-backup.sh` used `HOME=$HOME/.hermes-backup`. Cron runs scripts with an isolated HOME
  (`/opt/data/home`), so the backup repo was not found there and git failed with
  "Not a git repository", exit 128.
- It failed on **4 nights in a row** (11-21, 11-22, 11-23, 11-24 at 03:00), not just once. The 11-19 and
  11-20 runs show as silent (empty output).
- The script was rewritten at about 15:44 on 11-24 (backup: `scripts/hermes-backup.sh.bak-20261124`). It now
  derives paths from its own location, sets `GIT_CONFIG_GLOBAL` to the Hermes home's `.gitconfig` and checks the
  repo exists. The runs at 15:45 ("Backup complete and pushed") and 15:48 ("No changes") succeeded.
- The real test is the 03:00 run on 2026-11-25; check its output file in `cron/output/50fbaafad58b/`.
  Until then, "recovered" only means the manual runs worked.

## Cron doctor

One finding, harmless: the 10 AM health check fired 5 minutes late on 11-24. It clears at the next on-time run.

## Chat path

`git -C /srv/hermes/hermes-agent rev-parse --short=12 HEAD` prints `fcc26fbd9f16`. The host runs
`caafe5389ae5`, so the versions differ. Keep `docker exec -it hermes hermes`; do not switch to
`HERMES_HOME=/srv/hermes/data hermes`.

Next: A5 (Codex load, report only).
