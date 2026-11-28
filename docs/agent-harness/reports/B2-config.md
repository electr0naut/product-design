# Phase B2: gates fixes, model check, kanban config (gateway NOT restarted yet), 2026-11-24

User go received for B2 and the two gates fixes. No secrets recorded. No worker has run. Backup: `~/hermes-preB1-backup-2026-11-24/`.

## Gates fixes (`electr0naut/agent-harness`, private, branch `master`, commit `81fa5ed`)

1. A collection failure is now an error: `collect_ids` raises `HarnessError` naming the commit, the command and the last 8 lines when
   the collect command exits with anything but 0 or 5 (pytest "no tests collected"). `main` turns it into exit 2.
2. Criteria come from triage: `--acs readiness.json` is required (argparse exits 2 without it); every `acceptance_criteria[].id`
   with no valid test is in `missing_acs`, whatever the implementer listed. An empty `ac_tests` makes every criterion missing, and an empty
   criteria list is an error. The implement map is used only for the criterion-to-test mapping; mapped criteria that readiness does not know
   are reported as `unknown_acs`.
3. Minor items: the id sets are built once; the report now lists `deleted_test_files` by name; mutation still says "skipped".
- Tests: 14 pass (8 old plus 6 new: criterion left out by the implementer, empty AC map, no criteria, collection error on base, on head, and the CLI
  exit 2 for a collection error and for a missing `--acs`). Ruff check and format are clean, on the host and in the container
  (`.venv-container`, Python 3.14.9).

## Which model served the DeepSeek-first calls

Read from each profile's `state.db` (columns `model`, `billing_provider` only): `gatekeeper` and `scribe` were served by `deepseek-flash`
via `deepseek`; `triage` by `qwen3.7-plus` via `alibaba-token-plan`. DeepSeek answered, so the fallback chain was not used and it has credit now.

## Kanban config applied (container `config.yaml`; not live until the gateway restarts)

```yaml
kanban:
  dispatch_profiles: [triage, planner, implementer, gatekeeper, scribe]   # reviewer left out: host runner
  max_in_progress: 1
  max_in_progress_per_profile: 1
  failure_limit: 2            # already set
  dispatch_in_gateway: true   # already set
```
`hermes kanban init` ran (idempotent; board `default`, empty). `kanban diag` reports no diagnostics and shows
`dispatch_profiles: gatekeeper, implementer, planner, scribe, triage`.
`auto_decompose: true` is still on (it only touches cards in the `triage` column, which the loader never uses). I left it.

## command_allowlist (12 entries, was empty)

- `/srv/lab/agent-harness/.venv-container/bin/python -m harness.gates *`, `... -m pytest *`, `.../ruff *`
- `git -C /srv/lab/agent-harness/work/fixture-repo <sub>*` for `status diff log add commit checkout branch worktree rev-parse` (no `push`)
- Safety: Hermes's glob matcher refuses any command with shell control characters (`; & | < > $( )`, backticks, newlines) and
  `-c/-e`-style arguments hidden in quotes, so a glob cannot approve a chained command (`approval_floors.py`).
- Allowlist entries only matter for commands Hermes flags as dangerous, and I cannot tell in advance which ones the workers will hit.
  The dummy-card test will show; add entries then, one at a time, and report each.

## Waiting for you

The gateway must restart for `dispatch_profiles` and the limits to apply. That briefly restarts the Telegram and Discord bots
(the nightly 03:00 backup is the next job). Reply "restart" and I will run it, check `docker ps`, the gateway status and that the
4 kept cron jobs and the bots are back, and then run the dummy-card test.
