# Phase A5: Codex load (report only) and A4 follow-up 2, 2026-11-24

Read-only. Nothing was changed. No secret values are recorded.

## Follow-up 1: who rewrote `hermes-backup.sh`

The user says it was not them. `/opt/data/scripts/hermes-backup.sh` is owned by the container user `hermes`,
last modified 2026-11-24 15:47:39 +0100. Its `.bak-20261124` copy is the old May 2026 version. Neither this
session nor the user edited it, so it was most likely Hermes itself (an agent turn). I did not find the session
that did it. Unconfirmed.

## Follow-up 2: what the nightly backup pushes

| Item | Result |
|---|---|
| Script | `rsync` of an allowlist (`config.yaml`, `SOUL.md`, `memories/*`, and skill files `SKILL.md`, `references`, `scripts`, `templates`, `assets`), then `redact-config.py` on `config.yaml`, then `git add -A`, commit, `git push origin HEAD:main` |
| Remote | `git@github.com:electr0naut/hermes-backup.git` (SSH, no token in the URL) |
| Private? | Yes: `gh repo view` says PRIVATE |
| Tracked | 577 files, 106 commits: `.gitignore`, `SOUL.md`, `config.yaml`, 2 under `memories/`, 572 under `skills/` |
| `.gitignore` | excludes `.env`, `auth.json`, `channel_directory.json`, `gateway_state.json`, `*.pid`, `*.lock`, `*.db*`, `*.log`, caches, `sessions/`, `cron/`, and others |
| Tracked, names matching `.env\|auth.json\|credentials\|token\|key` | 3 skill scripts: `skills/devops/telegram-user-management/scripts/extract-telegram-token.py`, `skills/software-development/github/scripts/git-credential-token.py`, `skills/trading/tax-aware-portfolio-planning/scripts/store_exchange_api_key.sh`. Names only; they are skill scripts, not credential files. Their contents were not read |
| In history (same name filter) | the same 3 files; no `.env`, `auth.json` or credentials file was ever tracked |
| Pattern scan of content (key-shaped strings, all commits) | one file matches: `skills/mcp/native-mcp/SKILL.md` (4 lines, `ghp_...` and `sk-x...` prefixes). They look like examples in a doc, but I did not confirm they are placeholders. **Please check that file** |

Conclusion: no credential files are in the remote's history. `config.yaml` is pushed redacted by
`redact-config.py`, and I did not verify what it redacts. The one open point is the pattern match above.
Rewriting history and rotating keys are your decisions; I did nothing.

## A5: Codex load

| Fact | Result |
|---|---|
| Profiles on `gpt-6-sol` (openai-codex) | all 21 role profiles, plus `default` |
| Profiles that ever ran | only `cso`: 6 sessions, the last on 2026-05-14. The other 20 have 0 sessions |
| Agent cron jobs now active | none. The 4 active jobs are all no-agent scripts. The 6 paused jobs include the agent briefings (AI News, Politics, news-push) |
| What used Codex until now | the 08:10 Markets briefing (removed in A4; its `request_dump` files appear daily) and the agent briefings, now paused |
| Kanban | nothing on the board (0 triage/todo/scheduled/ready) |
| Codex window | rate-limited until 2026-11-26 08:21 CET (from the doc); not re-checked, as it needs a live call |

So the load on Codex is about zero today. The risk is only that all 22 profiles are set to Codex, so any
future chat with a role profile or any resumed agent briefing would use it.

Proposal (not applied):
- The 21 role profiles are unused and will be replaced by the six Phase B profiles. Leave them alone
  rather than edit them.
- When the paused briefings are resumed, set each one's model to `qwen3.7-plus` (alibaba-token-plan).
- Keep `gpt-6-sol` only for the Phase B `planner`.

Next: wait for your decision on the three points above, and check the 03:00 backup run on 2026-11-25.
Phase B follows the review.
