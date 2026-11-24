# Phase A5 follow-ups (read-only), 2026-11-24

User go received in the VM session, and option (c) chosen for the reviewer (host-side runner). Nothing was
changed except one temporary file, deleted afterwards. No secret values are recorded.

## 1. What rewrote `hermes-backup.sh`: not found

- `grep -rl "hermes-backup.sh"` over `/srv/hermes/data/sessions` and `~/.hermes/sessions` finds **no session
  file** modified between 15:30 and 15:59 on 2026-11-24. No agent session recorded the edit.
- The script is owned by `hermes` and was last modified 15:47:39. The first backup run with the new
  content, "Backup complete and pushed", was at 15:44:58 (before that mtime), so the script was touched at
  least twice.
- The only agent-like activity in the window comes from the spawn ledgers (no prompts or secrets read):
  - container: `hermes chat -q "Reply with exactly: cso-ok" --oneshot -Q`, profile `cso`, 15:42:43;
  - host: a `hermes -c ...` process, 15:33:42 (argv only `-c`).
  Neither mentions the script. The `cso` call is a smoke test.
- Files with mtimes in the window include `auth.json` (container and the `cso` profile) and
  `runtime/active_sessions.json`; they look like routine refreshes.

The cause is unknown. The edit may have come from a person or tool with shell access to the container
(or to `/srv/hermes/data` on the host), not from a Hermes session. **Ask the user** whether another session,
tool or person worked on the backup around 15:30 to 15:50, or whether it was another Claude session.
This was also the time of this session's own `hermes profile export` tests, which only read.

## 2. Key-shaped strings in `skills/mcp/native-mcp/SKILL.md`

| Line | Prefix | Length | Verdict |
|---|---|---|---|
| 279 | `ghp_` | 24 | placeholder: the tail is one repeated character, an `x` run |
| 292 | `sk-x` | 23 | placeholder: same |
| 314 | `ghp_` | 24 | placeholder: same |
| 319 | `sk-x` | 23 | placeholder: same |

All four are `x` runs shorter than a real key. Nothing to rotate. The user can still open the file to confirm.

## 3. What `redact-config.py` redacts

Run on a temporary copy of the container's `config.yaml` (deleted afterwards).

- Redacted: 4 `api_key` entries (the only ones with a non-empty value).
- Secret-like names left with a value, names only:
  - `access_token_env`: value has the shape of an environment-variable name, not a token (checked by pattern,
    not printed);
  - `record_key`: a key-binding value (`ctrl...`);
  - `show_token_analytics`, `redact_secrets`: booleans.
- Secret-like names present but empty (`''`), so nothing leaks: ~14 more `api_key`, `session_key`,
  `password_hash`, `password`, `secret`, `dm_role_auth_guild`.

The pattern covers `api_key`, `token`, `secret` and `password` (with prefixes). It does **not** cover names like
`session_key`, `*_key`, `auth` or `credential`. Today those are empty or harmless, but a future non-empty one
would be pushed. The script is safe for the current config; consider widening it.

## Option (c) for the reviewer: chosen

Host-side runner on a systemd user timer, `reviewer` left out of `kanban.dispatch_profiles`. Phase B starts
when the user gives the go. Verifies to do first: the exact flags of `kanban list`, `claim` and `complete`, and
that `dispatch_profiles` is an allowlist.
