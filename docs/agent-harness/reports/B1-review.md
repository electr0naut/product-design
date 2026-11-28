# Phase B1 review

**Approved.**
- **The five risky allowlist keys are removed**, with a backup taken first.
- **The six profiles are created clean**: no `--clone`, so no bot tokens or old config.
- **Providers and delegation**: providers are set explicitly, and delegation is pinned to Qwen, falling back
  to DeepSeek and never to Codex.
- **Triage answered a live call**, on Qwen.

## Before any worker runs (blocks the dummy-card test and Phase C)

**1. The 7 remaining allowlist keys (user decision).** Two of them undo most of what B1 removed:
- `shell command via -c/-lc flag`: `sh -c "<anything>"` runs any command without approval, including the
  deletes and overwrites that were just removed;
- `script execution via heredoc`: the same, via `python - <<EOF`.

No pipeline stage needs any of the 7. I recommend removing all of them:
- the two above;
- `docker/podman rm`, `hermes update`, `stop/restart hermes gateway` and `sudo with privilege flag`;
- `PowerShell encoded command`, which has no use on Linux.

Then add only the exact commands the stages need in B2. If an older chat workflow depends on one of these
keys, list it and scope the key to that profile only.

**2. Adapt the five `SOUL.md` files to Hermes.** They were copied from the Claude Code skills, so they tell
the model to "ask locator" or "ask test-runner". Those agents don't exist in Hermes. Replace those lines:
- lookups use the terminal tool with `rg`/`git grep`, or a single `delegate_task` to the pinned Qwen child;
- test runs use the exact test command from `harness.toml`.

Remove any mention of `.claude`, `Agent(...)` or Claude Code subagents. Keep every rule about tests,
evidence and scope as it is. Push the diff of the five files for review; it's small.

## Notes

- **Planner and DeepSeek untested.** The planner's Codex route can't be tested until Codex resets on
  2026-11-26 08:21 CET. Until then the planner falls back to Qwen, which is fine for the smoke test. Test the
  two DeepSeek-first profiles (`gatekeeper`, `scribe`) with a one-shot `-ok` call, as was done for triage.
- **The kit repo (`git init` and a private GitHub repo for `/srv/lab/agent-harness`)** is the user's to run or
  to approve. Either way, it's needed before B3.

## Next

B2: kanban config, `dispatch_profiles` and the stage-specific allowlist entries, then a gateway restart with
the user's OK at that moment. Do items 1 and 2 above first.
