# Hermes probe results (Phase A1, 2026-11-24)

| Item | Result |
|---|---|
| `hermes kanban --help` | OK. Subcommands include init, boards, create, list, show, assign, link, complete, block, unblock, runs, watch, stats, tail, log, context, notify-subscribe, diagnostics, repair. Dispatcher runs in the gateway (`daemon` is deprecated; use `hermes gateway start`). Has a `--board <slug>` option, so boards are multi-board. |
| `hermes gateway --help` | OK. Subcommands: run, ensure, start, stop, restart, status, install, uninstall, list, setup, migrate, migrate-legacy, enroll. `install` is documented as systemd/launchd. |
| `hermes backup --help` | `-o OUTPUT`, `-q/--quick` (critical state only), `-l LABEL`, `-k N`. Default output `~/hermes-backup-<timestamp>.zip`. Excludes the hermes-agent codebase. |
| `hermes profile export --help` | `hermes profile export [-o OUTPUT] <profile_name>`. One profile per call. |
| `hermes cron create --help` | Has --name, --deliver, --skill, --script, --no-agent, --repeat, --catch-up. Model/provider flags not yet checked (the first lines only). |
| `hermes --version` (host) | v0.23.3 (2026.9.24), git install, Python 3.14.9 |
| Host gateway | Running as PID 90439, started manually, NOT a system service |
| `claude -p` from a kanban worker | NOT yet verified (needs Phase B) |
| Approvals / allowlist setting | NOT yet verified (Phase B2) |
| `hermes fallback check --live` | NOT run: it would ping Codex (scarce). Awaiting OK. |
| Usage reporting location | NOT yet verified (Phase C) |

## Phase B verifies (2026-11-24)

| Item | Result |
|---|---|
| `kanban list` | `--assignee`, `--status {archived,blocked,done,ready,review,running,scheduled,todo,triage}`, `--json`, `--sort`. OK |
| `kanban create` | `title`, `--body/--body-file`, `--assignee`, `--parent` (repeatable), `--workspace scratch\|worktree[:path]\|dir:<path>`, `--branch`, `--idempotency-key`, `--max-runtime`, `--max-retries`, `--model`, `--provider`, `--skill`, `--json`. OK; `--body-file` is better than `--body` for ticket text |
| `kanban claim` | `claim [--ttl SEC] <task_id>` (default 900 s); prints the workspace path |
| `kanban complete` | `complete [--result] [--summary] [--metadata JSON] [--force] <ids...>` |
| `kanban block` | `block [--ids ...] [--kind capability\|dependency\|needs_input\|transient] <id> [reason]`; `--kind dependency` waits in `todo` and auto-promotes; `needs_input` goes to `blocked` for a human |
| `kanban.dispatch_profiles` | An allowlist, fail-closed: absent key = any profile claimable; present but empty/null = claims nothing; list or comma string = only those names. (Source: `hermes_cli/kanban_db_dispatch.py`.) |
| Approvals config | `approvals.mode` (container: `manual`), `approvals.cron_mode: deny`; `command_allowlist` entries are exact commands, globs or dangerous-pattern rule keys, honored even in unattended contexts |
| How kanban workers resolve approvals | NOT verified: docs name cron/`-q`/webhook contexts, not kanban workers. Needs a live test in B2 |
| `claude` in the container | missing; only `git` and the venv python. `/srv/lab` is mode 755 (world-readable) |
| `sessions` DB search for `hermes-backup.sh` | 0 mentions in all 9 `.db` files (strings count, no content) |

## B3 verifies (2026-11-24)

| Item | Result |
|---|---|
| `claude -p` flags (v2.1.331) | `--model`, `--max-budget-usd`, `--output-format json`, `--json-schema`, `--tools`, `--allowedTools`, `--permission-mode`, `--no-session-persistence` exist. **`--max-turns` does not exist** (the doc's command is wrong; use `--max-budget-usd`) |
| `claude -p --output-format json --json-schema` output | result object has `structured_output` (dict) and `total_cost_usd`; one tiny call cost $0.016 |
| Claim TTL | a claim with `--ttl 20` and no heartbeat returned to `ready` about 60 s later, no manual step |
| Card claimed by the host | counts against `max_in_progress: 1`; reviewer cards outside `dispatch_profiles` can be claimed and completed from outside |
| Worker approvals | kanban workers deny flagged commands (single-query behaviour); unflagged commands run |
