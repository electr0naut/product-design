# Phase B1: allowlist cleanup and six profiles, 2026-11-24

User go received: remove the risky allowlist keys; profiles approved. Backup before the changes:
`~/hermes-preB1-backup-2026-11-24/`. No secret values recorded. No worker has run.

## command_allowlist (container `config.yaml`)

Removed the five keys: `delete in root path`, `in-place edit of system config`, `overwrite system file via redirection`,
`recursive delete`, `script execution via -e/-c flag`.

Still allowed (7), for the user to review: `PowerShell encoded command execution`, `docker/podman rm (container destruction)`,
`hermes update (restarts gateway, kills running agents)`, `script execution via heredoc`, `shell command via -c/-lc flag`,
`stop/restart hermes gateway (kills running agents)`, `sudo with privilege flag (stdin/askpass/shell/list)`.
`script execution via heredoc` and `shell command via -c/-lc flag` are the ones an unattended worker is most likely to
trip over; `docker rm`, `hermes update` and the gateway stop/restart are not needed by any stage. I did not touch them.

## Profiles (created with `hermes profile create`, no `--clone`, so no bot tokens or old config)

| Profile | Primary | Fallbacks | SOUL.md source |
|---|---|---|---|
| triage | qwen3.7-plus (alibaba-token-plan) | deepseek-flash | skill `ticket-readiness` |
| planner | gpt-6-sol (openai-codex) | qwen3.7-plus, deepseek-flash | `plan-ticket` |
| implementer | qwen3.7-plus | deepseek-flash | `implement-ticket` |
| gatekeeper | deepseek-flash (deepseek) | qwen3.7-plus | 3-line role text, no skill |
| reviewer | qwen3.7-plus | deepseek-flash | `review-evidence` |
| scribe | deepseek-flash | qwen3.7-plus | `handoff` |

- Each profile: `delegation.model/provider/base_url` = qwen3.7-plus on alibaba-token-plan,
  `delegation.fallback_providers` = deepseek-flash only (children never fall back to Codex), `max_spawn_depth: 1`.
- Verified with `-p <name> config get model --json` and `config get delegation --json`; nothing mentions Anthropic or Ollama.
- A fresh profile defaulted to `provider: openai-codex`, so the provider was set explicitly on all six (the plan's quirk).
- Live check: `hermes -p triage chat -q "Reply with exactly: triage-ok" --oneshot -Q` answered `triage-ok` (Qwen, no Codex).
  The other five were not called, so the planner's Codex route and the DeepSeek profiles are untested.
- `profile create` also created a command alias per profile and reported that the running gateway serves them (no bot token, so
  they do not connect to Telegram or Discord).
- The skills' text still mentions Claude Code concepts (agents, `.claude`) in places; I copied them as written. Check the
  five SOUL.md files before B4.

## Not done

B2 (kanban config, `dispatch_profiles`, gateway restart) is next and needs your OK for the restart.
The dummy-card test and the gates `harness.toml` change come after B2. The git steps for `/srv/lab/agent-harness` are for you to run.
