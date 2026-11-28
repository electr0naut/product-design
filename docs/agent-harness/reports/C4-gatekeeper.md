# C4: deterministic gatekeeper and host-only queue file

Kit commit `agent-harness@530d803` (pushed, `git ls-remote` confirmed). 119 tests pass on host and in container; ruff clean.

## Queue file (C3-review hardening)
`queue.json` now lives in `~/.local/state/agent-harness/` next to the trusted repos (not in `/srv/lab`), written by the loader and read by the host runner. Tests point it at a temp folder, so they never touch the real one.

## Deterministic gatekeeper (C3-review design answer)
New `harness.gatekeeper`, called from the host runner pass in this order: relink, gatekeeper, reviewer.
- Takes one ready `gatekeeper` card; one attempt per card (same attempts file).
- Validates the run files first (`read_run_files`, branch fetched into the trusted repo, base exists there, base == trusted main); an invalid card is blocked `needs_input` and never claimed.
- Runs `harness.gates` in the container through `gates.gates_cmd` in `harness.host.toml` (docker exec as `hermes`; unset means fail closed). I ran the real command shape once against PRC-5's run folder: exit 2 with the stale-base message, as expected.
- Exit 0 completes the card with the report as metadata; exit 1 blocks `needs_input` with the failing fields; exit 2, a timeout or an unreadable report blocks `transient`.
- Tests (stub in place of `harness.gates`): pass/fail/error map correctly; missing `gates_cmd` fails closed; invalid run files never claim the card; a stale base is refused; an attempt is not repeated; the pass only runs when `gatekeeper.host = true`.

## Not switched on yet (needs the user)
`[gatekeeper] host = false` in `harness.host.toml`. Turning it on needs `gatekeeper` removed from `kanban.dispatch_profiles` in the Hermes config (otherwise a model and the runner would both work the card) and a gateway restart, which the builder rules put behind the user's go. Same for the Telegram cron script. I will ask the user for both together.
