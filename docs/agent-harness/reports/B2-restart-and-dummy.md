# Phase B2 (part 2): gateway restart and dummy-card tests, 2026-11-24

User said "restart". No secrets recorded. The board is empty again (the three dummy cards are archived).

## Restart

- The container's gateway is the s6 service `gateway-default`; I restarted it with `s6-svc -t /run/service/gateway-default` (as root, once).
  New PID 27210. The other 52 per-profile services (including the six new ones) are down; the one multiplexed gateway serves all profiles.
- After: `docker ps` shows `hermes` and `hermes-dashboard` up; the log says `✓ telegram connected`, `✓ discord connected`, `✓ api_server connected`;
  the kanban dispatcher holds its lock with `max_in_progress=1`, `max_in_progress_per_profile=1`; `kanban diag` is clean and lists the five
  `dispatch_profiles`. The 4 kept cron jobs are active and the 6 paused ones are paused (`cron list`).
  I did not send a Telegram message; please confirm the bot answers (Phase A acceptance).
- Note: the gateway reports "Running manually, not as a system service" even though s6 supervises it; the s6 `/run/service` list still has
  the old `-fable` service folders for 21 removed profiles. They are down; I left them.

## The two open questions from B0

1. **Does a card claimed by the host count against `max_in_progress: 1`? Yes.** I claimed a `reviewer` card from outside the dispatcher
   (`kanban claim`, status `running`), then created a `triage` card. It stayed `ready` for 4 checks (about 2 minutes, two dispatch ticks).
   When I completed the reviewer card, the triage card was dispatched within the next tick.
2. **Does `claim` work for a card assigned to `reviewer` (outside `dispatch_profiles`)? Yes.** `kanban claim t_4f789793` returned the
   workspace path (`/opt/data/.hermes/kanban/workspaces/<id>`, inside the container) and the dispatcher left the card alone.
   `kanban complete <id> --summary ... --metadata '<json>'` worked from the host-side call too.

## Worker run and approvals

| Card | Profile | Result |
|---|---|---|
| DUMMY-T (call `kanban_complete` only) | triage (Qwen) | completed in 11 s, rc 0, summary "dummy ok" |
| DUMMY-G (run three commands, report each) | gatekeeper (DeepSeek) | completed in 14 s, rc 0 |

DUMMY-G findings, by command:
- `cd /srv/lab/agent-harness && .venv-container/bin/python -m pytest --collect-only -q tests`: **ran**, exit 0, 14 tests collected.
- `python3 -c "print(1)"`: **denied** ("script execution via `-c` flag"); no user to answer.
- `sh -c 'echo hi'`: **denied** ("shell command via `-c`/`-lc` flag"), same reason.

So kanban workers resolve dangerous-command prompts like single-query sessions: deny, with a hint to set `approvals.single_query_mode: approve`
(not set; do not). No approval prompt hung a worker. I added no allowlist entries; the three entries tested did not trigger a prompt at all.

## Not tested

The planner's Codex route (until 2026-11-26), `implementer` and `reviewer` workers, and git commands (the fixture repo does not exist yet).

## Next (B3, with the user's go)

`/srv/lab/agent-harness/tools/load_tickets.py` and the host reviewer runner, then `harness.toml` pointing at the container venv and `work/`.
Also in the kit: move the empty-criteria check to the top of `run_gates` (non-blocking note from the review).
