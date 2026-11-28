# Phase A1: inventory (read-only), 2026-11-24

No secret values are recorded here: variable names only, chat IDs masked.

## Two installs

| | Host | Container `hermes` (+ `hermes-dashboard`) |
|---|---|---|
| Version | v0.23.3 (2026.9.24), git install, Python 3.14.9 | image `hermes-lab:fcc26fbd`, up 7 h |
| Gateway | running (PID 90439), started manually, not a service | always on, restart policy `unless-stopped` |
| Compose project | none | `/srv/hermes` |
| Mounts | `~/.hermes` | `/srv/hermes/data` -> `/opt/data`, `/srv/lab` -> `/srv/lab` |
| Profiles | only `default` (`gpt-6-sol`) | 22 listed (`default` + 21 roles), all showing `gpt-6-sol`; no `-fable` twins |
| Cron jobs | none | 14 (below) |
| Fallback chain | `gpt-6-sol` (openai-codex) -> `qwen3.7-plus` (alibaba-token-plan) -> `deepseek-flash` (deepseek) | identical |
| Bot token variables set | none (commented template lines only) | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USERS`, `TELEGRAM_HOME_CHANNEL`, `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_HOME_CHANNEL` |

## Container cron jobs

| ID | Name | Schedule | Mode | Deliver | Status | Keep? |
|---|---|---|---|---|---|---|
| 6d1f41c29a21 | Health check 10 AM | `0 10 * * *` | no-agent script | origin | ok (5 min late) | ? |
| 412b87173203 | Health check 10 PM | `0 22 * * *` | no-agent script | origin | ok | ? |
| 50fbaafad58b | hermes-nightly-backup | `0 3 * * *` | no-agent script | local | ok; exit 128 at 03:00, recovered | ? |
| 23bf36de3892 | AI News Daily Briefing | `0 8 * * *` | agent, skill daily-news-briefings | telegram:<masked> | ok | ? |
| 437f83fb9805 | International Markets Daily Briefing | `10 8 * * *` | agent | telegram:<masked> | **failing, HTTP 401 (placeholder key), 26 in a row** | fix or drop |
| 0c7aed2555b3 | International Politics Daily Briefing | `20 8 * * *` | agent | telegram:<masked> | ok | ? |
| 525496d2acdd | news-push-to-iphone | `30 8 * * *` | agent | origin | ok | ? |
| 1b69780181bc | discord-gateway-watchdog | every 5m | no-agent script | local | ok | ? |
| 9246ce6dafc9 | monitor-watched-emails | every 15m | no-agent script | origin | ok | ? |
| b9790b7525fb | Amazon delivery watch | every 120m | no-agent script | origin | ok | ? |
| 76028a4a5646 | call-home-insurance | once, 2026-06-23 | no-agent script | origin | stale, date passed, never ran | probably drop |
| 778a3fc05bdd | Daily personal-care reminder | `0 12 * * *` | no-agent script | telegram | ok | ? |
| 7606fb1705ec | Agentic Stack setup progress | every 5m | script | telegram:<masked> | paused | probably drop |
| 21848fb9969c | OpenAI Codex <-> DeepSeek failover | every 30m | no-agent script | origin | paused | probably drop |

`hermes cron list` does not print per-job models, so that column is not filled.

## Differences from the orchestration doc

- Container has 22 profiles, not 21 (the 21 roles plus `default`); A2's "42 profiles" does not match.
- Container profiles show `gpt-6-sol`, not DeepSeek/Ollama Qwen.
- Host gateway is running manually; `--idle-exit` was not checked.
- Host has no `~/.hermes/profiles` directory yet.

## Verify results

See `.harness/hermes-probe.md`. Summary: `kanban` and `gateway` subcommands exist as the doc assumes;
`backup` takes `-o/-q/-l/-k`; `profile export` takes one name plus `-o`. `fallback check --live` was
deliberately not run (would ping rate-limited Codex).

## Open questions

1. Run `fallback check --live` now, or after 2026-11-26?
2. Which cron jobs to keep; Markets briefing: pin to Qwen or a real OpenAI provider?
3. Proceed to A2 (backups)?
