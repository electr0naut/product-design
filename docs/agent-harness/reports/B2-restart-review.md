# Phase B2 part 2 review

**Approved.** The restart was clean: bots connected, dispatcher limits live, `diag` clean, cron state as decided.
The dummy-card test answered both open questions, and the board was left empty.

## What the test established

- **One ticket at a time holds for host-claimed cards.** A card claimed by the host runner counts against
  `max_in_progress: 1`, so the reviewer stage blocks the board just like any worker.
- **The host can work reviewer cards.** It can claim and complete them, and the dispatcher leaves them alone.
- **Unattended workers deny dangerous commands instead of hanging.** `-c` and shell `-c` were denied with no
  prompt. That's the behaviour we want.
  - Leave `approvals.single_query_mode` unset.
  - When the implementer or gatekeeper hits a denial on a command it really needs, add that exact command to the
    allowlist, one at a time, and report it.

## Notes for B3

- **Workspace paths.** `kanban claim` returns paths inside the container (`/opt/data/...`). Inside the
  container, `/opt/data` is `/srv/hermes/data` on the host. The runner must map the prefix, and only read there:
  - its own work happens in a host git worktree under `/srv/lab/agent-harness/work/`;
  - it never writes into `/srv/hermes/data` except through `kanban` commands.
- **Locking and identity.** The runner takes a lock (`flock`), heartbeats while it reviews, and leaves its
  claim to expire on its own if it crashes. Check how the claim's time-to-live behaves when the runner dies
  mid-review: the card must return to `ready`, not stay `running` forever.
- **`claude -p` from the runner.** It needs these flags: `--model sonnet`, `--max-turns`, `--max-budget-usd`,
  `--output-format json`, and `--json-schema` with the kit's schemas. Log only results and costs, never prompts
  that contain code from secrets-bearing paths.
- **Cleanup, low priority.** The 21 stale s6 service folders of removed `-fable` profiles are harmless while
  down. Remove them only with the user's go.

## User check

Please send the Telegram bot a message and confirm it answers. That's the last open Phase A acceptance item.

## Next

**B3 is approved on the user's go.** It covers the loader, the host reviewer runner, `harness.toml` pointing at
the container venv and `work/`, and the small `run_gates` change. Push the kit changes to `agent-harness` and
post both commits; I'll review the code before the PRC-1 smoke test.
