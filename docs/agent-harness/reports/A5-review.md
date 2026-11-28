# Phase A5 review

**Approved: the report-only pass is complete.** Codex load today is about zero. The A5 proposal is accepted
as it stands:
- leave the 21 unused role profiles alone; they get replaced in Phase B;
- pin each briefing to `qwen3.7-plus` if the user resumes it;
- keep `gpt-6-sol` only for the Phase B `planner`.

Phase A is done, except for the 03:00 backup check on 2026-11-25.

## Open points before Phase B (read-only; report back, change nothing)

**1. Find what rewrote `hermes-backup.sh`.** Nobody here edited it, so an agent turn rewrote a scheduled
script without the user knowing. `/srv/hermes/data` is a host folder owned by `ubay`, so either install
could have done it: the container's Hermes or the host's. Search both installs' session data for the
script name, for 2026-11-24 between 15:30 and 15:50:

```bash
grep -rl "hermes-backup.sh" /srv/hermes/data/sessions ~/.hermes/sessions 2>/dev/null | xargs -r ls -l --time-style=+%F_%T | awk '$6 >= "2026-11-24_15:30" && $6 <= "2026-11-24_15:59"'
```

Report:
- the session file;
- the profile it belongs to;
- the user message that started that turn, summarised in one line with no secrets.

**2. Check the key-shaped strings in `skills/mcp/native-mcp/SKILL.md`.** Don't print or push them; this
repo's reports are on GitHub. For each of the 4 matching lines, report only its line number, its prefix
(for example `ghp_`) and whether the value looks like a placeholder: repeated characters, `x`/`X` runs,
`your`, `example`, `...`, or shorter than a real key. The user should also look at the file in their own
terminal. If any value is real, the user must revoke and rotate that key. Deleting it from git history
alone doesn't make it safe.

**3. Check what `redact-config.py` redacts.** Run it on a temporary copy of `config.yaml` and report which
key names come out redacted and which keys with secret-like names (`key`, `token`, `secret`, `password`)
are left unredacted. Report names only. Delete the temporary copy afterwards.

## Phase B design decision for the user: where the Claude Code reviewer runs

The container image has no `claude`. I recommend option **(c), a host-side reviewer runner**. It keeps the
user's Claude subscription login on the host, so no credentials go into the container. It uses only
documented Kanban commands:

- **Dispatcher.** Leave `reviewer` out of `kanban.dispatch_profiles`, so the container's dispatcher never
  spawns reviewer workers.
- **The runner.** A host systemd user timer runs every minute. Each run:
  1. lists ready reviewer cards with `docker exec hermes hermes kanban list --status ready --json`, filtered
     to assignee `reviewer`;
  2. claims one with `kanban claim <id>`;
  3. runs the BUILD_SPEC 6.2 review with `claude -p` on the host checkout of branch `harness/<KEY>`;
  4. ends the card with `kanban complete <id> --summary ...` (plus the metadata JSON), or
     `kanban block <id> "<reason>"`.
- **Verify:** the exact flags of `kanban list`, `claim` and `complete` (`--help`), and that
  `dispatch_profiles` is an allowlist.

The other options were (a) installing `claude` and its login under `/srv/lab`, which puts the subscription
credentials inside the agent's reach, and (b) a host HTTP service, which adds a network surface. Phase B
starts only after the user chooses.
