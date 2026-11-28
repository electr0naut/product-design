# Phase A2: backups, 2026-11-24

All backups are in `~` and owner-only (`chmod 700`, or mode 600 for the zip). They contain credentials: never commit or share them.

| Backup | Source | Size | Method |
|---|---|---|---|
| `~/hermes-srv-backup-2026-11-24/` | `/srv/hermes` (compose files, `data/`, `hermes-agent`, Dockerfile.lab) | 5.6G | `sudo cp -a`, then `chown -R ubay:` and `chmod 700` (the A2 commands) |
| `~/hermes-host-backup-2026-11-24/` | `~/.hermes` | 3.9G | `cp -a`, `chmod 700` |
| `~/hermes-host-backup-2026-11-24.zip` | host config, skills, sessions | 43M | `hermes backup -o` (extra, from before the review) |
| `~/hermes-container-backup-2026-11-24/` | container `/opt/data` | 1.2G | `docker cp` (extra, from before the review; redundant with the `/srv/hermes` copy) |

## Checks

- A recursive diff of each folder copy against its source shows only live-system leftovers: sockets
  (`gateway.sock`, Chromium `SingletonSocket`) and dangling cache/scratch files (Chromium `Singleton*`, pytest scratch).
  No config, auth, cron or state file differs.
- `hermes profile export` works inside the container (tested for the 22 profiles), but the exports were not
  kept: the review says the folder copy is enough. The temporary `/tmp/pexp` in the container and the
  empty export folder on the host were removed.

## Notes

- Earlier (before the review) I ran `hermes fallback check --live` on the host: qwen3.7-plus and
  deepseek-flash were both ready. The review advised waiting until Codex resets (2026-11-26 08:21 CET);
  that was a deviation. The check covered only the two fallbacks, not Codex.
- Nothing in the container was changed. No cron job was touched; A1-decisions.md is not applied yet (A4).
- The two "extra" backups can be deleted if you want the space back (about 1.2G + 43M).

Next: A3 (stop the host gateway), needs your OK.
