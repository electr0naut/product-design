# Phase B0: plan (nothing is changed by this file), 2026-11-24

Verify results are in `.harness/hermes-probe.md` (local). Everything below needs the user's go before it runs.
Back up `/srv/hermes/data/config.yaml` and `profiles/` before B1 (rule 4); a fresh `cp -a` is enough.

## Where things run

- Everything that Hermes workers touch lives in `/srv/lab/agent-harness/` (mounted in the container at the same path,
  writable by `hermes`). Note: `/srv/lab` is mode 755, so other local users can read it. It holds no credentials.
- Credentials stay out of it. The Claude login stays in `~/.claude` on the host (option c).
- All Hermes commands run as `docker exec -u hermes hermes hermes ...` (the `-u hermes` matters: the default
  exec user is root and creates root-owned files).

## B0.1 Build the kit on the host

1. `mkdir -p /srv/lab/agent-harness/docs`; copy `DESIGN.md` and `BUILD_SPEC.md` there, copy the extractor by hand
   (BUILD_SPEC 0.2), then `python3 tools/extract_literals.py docs/BUILD_SPEC.md .` (BUILD_SPEC's own bootstrap).
2. Files used by this plan, from the extracted kit:

| Need | Source in the kit | Used by |
|---|---|---|
| gates script (M3) | `src/harness/gates.py` and its helpers, run as `python -m harness.gates` | `gatekeeper` |
| review schemas (M4) | `schemas/readiness.json`, `refutations.json`, `proof.json` and the finding schema | `triage`, host reviewer runner |
| fixture | `eval/fixture/{repo,tickets,hidden,reference}` | Phase B and C acceptance |
| MR template | `template/mr_description.md` | `scribe` |
| role text | `template/.claude/skills/{ticket-readiness,plan-ticket,implement-ticket,review-evidence,handoff}/SKILL.md` | `SOUL.md` per profile |

   Exact paths are checked after extraction (BUILD_SPEC 0.3 shows the layout, not every filename).
3. Python for the gates: the container has only the Hermes venv python (3.12?), not a system `python3`. Verify the
   gates run under it with the standard library only; if not, run the gates from the host runner instead.

## B1 profiles (container)

For each of `triage planner implementer gatekeeper reviewer scribe` (names are new: no clash with the 21 old roles):

```bash
docker exec -u hermes hermes hermes profile create <name> --description "<one line from HERMES_ORCHESTRATION B1>"
docker exec -u hermes hermes <name> config set model.default <model>        # alias form, per the doc; verify
docker exec -u hermes hermes <name> config set model.provider <provider>
```

| Profile | `model.default` / `model.provider` | `fallback_providers` (names as in `fallback list`) |
|---|---|---|
| triage | qwen3.7-plus / alibaba-token-plan | deepseek |
| planner | gpt-6-sol / openai-codex | alibaba-token-plan, deepseek |
| implementer | qwen3.7-plus / alibaba-token-plan | deepseek |
| gatekeeper | deepseek-flash / deepseek | alibaba-token-plan |
| reviewer | qwen3.7-plus / alibaba-token-plan | deepseek |
| scribe | deepseek-flash / deepseek | alibaba-token-plan |

- Each profile: `delegation.model: qwen3.7-plus`, `delegation.provider: alibaba-token-plan`,
  `delegation.fallback_providers: [deepseek]`, `max_spawn_depth: 1`, so children never reach Codex.
- Each profile gets a `SOUL.md` copied from its skill (table above).
- Verify with `profile list` and `<name> config get model --json` (doc B1). Never configure Anthropic or Ollama.
- Quirk to verify: these new profiles share the container's `config.yaml` defaults, so check that none inherits
  `gpt-6-sol` by mistake.

## B2 board, dispatcher, approvals (container config)

```yaml
kanban:
  dispatch_in_gateway: true          # already true
  max_in_progress: 1
  max_in_progress_per_profile: 1
  failure_limit: 2                   # already 2
  dispatch_profiles: [triage, planner, implementer, gatekeeper, scribe]   # reviewer left out on purpose
```

- `dispatch_profiles` is a fail-closed allowlist (verified), so listing the five makes `reviewer` cards wait for the
  host runner. This also stops the container from claiming cards for the 21 old roles or `default`.
- `hermes kanban init` (idempotent; the board DB `kanban.db` already exists).
- Approvals: container is `approvals.mode: manual`, `cron_mode: deny`. Workers are unattended. Do not use `--yolo`.
  Add only what a stage needs, as exact commands or globs under `command_allowlist`: the gates command,
  `git` on `harness/*`, and the project's test and lint commands. Needs a live test of how a kanban worker resolves a
  prompt before Phase C (not verified in the docs).
- **Existing `command_allowlist` already permits rule keys such as `recursive delete`, `delete in root path`,
  `script execution via -e/-c flag`, `overwrite system file via redirection` and `in-place edit of system config`**
  for every profile, unattended contexts included. Pipeline workers inherit those. Decide whether to remove them
  (the user's call; not changed here).

## B3 ticket loader

`/srv/lab/agent-harness/tools/load_tickets.py`, as specified in the doc. Uses `kanban create ... --body-file`, `--parent`,
`--assignee`, `--idempotency-key <KEY>:<stage>`, `--json`, and reads the id from the JSON. Dependency cycle: stop and name
the keys. `--workspace worktree --branch harness/<KEY>` for implementer cards, to be verified in a dry run.

## Host reviewer runner (option c)

- `~/.config/systemd/user/harness-reviewer.service` and `.timer` (every 60 s), plus
  `/srv/lab/agent-harness/tools/reviewer_runner.sh` (runs as `ubay`). Needs `loginctl enable-linger ubay` (sudo, user's OK).
- One pass, with a lock file so passes never overlap:
  1. `docker exec -u hermes hermes hermes kanban list --assignee reviewer --status ready --json`; stop if empty.
  2. `kanban claim <id> --ttl 1800` (atomic).
  3. Read the card with `kanban context <id>`; check out `harness/<KEY>` in a host worktree.
  4. Qwen finds defects via the Hermes `reviewer` profile? No: find with Qwen by calling the Alibaba API through a short
     `hermes chat -q` on the reviewer profile, then refute and prove each finding with
     `claude -p --model sonnet --max-turns 10 --output-format json --json-schema <schemas/refutations.json|proof.json>`
     (BUILD_SPEC 6.2 decision rules).
  5. `kanban complete <id> --summary ... --metadata '<findings/refutations/proofs JSON>'`, or
     `kanban block <id> --kind needs_input "<reason>"`; a proven or blocking-unproven finding creates an `implementer`
     fix card (max 2 loops).
- It sends no credentials into the container, and the runner prints no secrets. Heartbeat: `kanban heartbeat <id>`.
- Open questions: does a card claimed by a host process count against `max_in_progress: 1`? Does `claim` on a card
  assigned to a profile outside `dispatch_profiles` work? Test both on a dummy card before relying on it.

## Order and gates

1. User go on this plan. 2. Back up config and profiles. 3. B1. 4. B2 (config edit, restart gateway: that restarts the
Telegram and Discord bots; needs the user's OK at that moment). 5. B3 loader and the runner. 6. Smoke test with PRC-1,
then the bounce test with PRC-6 (Phase B acceptance). Report and wait for the review after each step.

## Done in this pass, besides this plan

- Open point 1: 0 mentions of `hermes-backup.sh` in any of the 9 container `.db` files, so the cause of the 15:44 rewrite stays unknown. Asked the user; nothing else found.
- Open point 2: `redact-config.py` widened to `key|token|secret|passw|auth|credential|session` (case-insensitive, anywhere in the name).
  Backup of the original: `/srv/hermes/data/scripts/redact-config.py.bak-20261124-a5`. Tested on a temporary copy of `config.yaml` (deleted):
  all 4 previously redacted `api_key` values are still redacted, the YAML still parses, and these names are newly
  redacted (names only): `access_token_env`, `group_sessions_per_user`, `record_key`, `record_sessions`,
  `redact_secrets`, `session_ttl_seconds`, `show_token_analytics`. Those are harmless settings, so the nightly backup's
  `config.yaml` loses a few non-secret values; to keep them, narrow the pattern later. The next real run is 03:00 on 2026-11-25.
