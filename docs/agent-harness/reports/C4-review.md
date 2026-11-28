# C4 review (`agent-harness@530d803`)

**Approved, with two small changes before it's switched on.** Verified in the reviewing session: `119 passed in
49.11s`, and ruff is clean.

- **The queue file** now lives in the host-only state folder. Good.
- **`harness.gatekeeper` follows the reviewer runner's shape:**
  - it validates against the trusted repo before claiming, and an invalid card is blocked without a claim;
  - `gates_cmd` fails closed;
  - gates run in the container;
  - exit code 0, 1 or 2 maps to complete, `needs_input` or `transient`;
  - one attempt per card.
- **It ships switched off:** `host = false` stays until `dispatch_profiles` drops `gatekeeper`. That's the right
  default.

## Before switching it on

1. **Gate the exact commit that was validated.** `gates_cmd` gets `--head harness/<KEY>`, a branch name in the
   container-writable work repo. A worker could move the branch between the host's validation fetch and the
   gate run. Pass the fetched sha (`runner.sha`) as `{head}` instead. The work repo has that commit, because it
   was fetched from there. `check_lineage` already works on shas.
2. **Never read an old report.** Delete `run/gates.json` before running the gates. Otherwise, if a gate run
   crashes before writing its report, the host could read the report from an earlier attempt.
3. **Tests:**
   - `{head}` is a 40-hex sha;
   - a stale `gates.json` from an earlier run is never used.

## Switching on (the user's go; one approval can cover all of it)

1. Remove `gatekeeper` from `kanban.dispatch_profiles`.
2. Set `[gatekeeper] host = true`.
3. Install the Telegram no-agent cron script (C2 final review item 3) and unsubscribe the stage cards.
4. One gateway restart, which briefly restarts the bots.
5. **Smoke test:** load one fixture ticket on a fresh fixture repo and a fresh trusted repo. Expected:
   - the gatekeeper card completes with **no** gatekeeper model session (check with `harness.usage`);
   - exactly one Telegram message, when the ticket finishes.
