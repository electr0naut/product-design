# Phase A5 follow-ups review

**Approved.** The SKILL.md strings are placeholders, `redact-config.py` is safe for today's config, and
option (c) for the reviewer is recorded.

## 1. The backup script edit: one more read-only check

The file is owned by `hermes`, the user inside the container. A process on the host running as `ubay`
would have left it owned by `ubay`. So the edit was most likely made from inside the container, by the
gateway's agent (a Telegram or Discord chat) or by a `docker exec -u hermes` shell.

Gateway chat history may live in the session database rather than in the files you searched. Count
mentions without printing any content:

```bash
for f in /srv/hermes/data/*.db /srv/hermes/data/**/state*.db; do [ -f "$f" ] && printf '%s %s\n' "$f" "$(strings "$f" | grep -c 'hermes-backup.sh')"; done 2>/dev/null
```

If a database has mentions, report which platform and session ID they belong to (via `hermes sessions` or
its equivalent; check `--help`) and the time. No message text. If nothing turns up, record "cause unknown,
user asked" and move on; this doesn't block Phase B.

## 2. Widen the redaction pattern (user decision, small change)

Today's config doesn't leak, but a future non-empty `session_key`, `*_key`, `auth*` or `credential*` value
would be pushed to the backup repo. I propose widening the secret-name match in
`/srv/hermes/data/scripts/redact-config.py` to cover `key|token|secret|password|auth|credential|session`
(case-insensitive, anywhere in the name).

To check the change:
1. Run it on a temporary copy of `config.yaml`, then delete the copy.
2. Confirm that every name that was redacted before is still redacted.
3. Report any new names it now redacts, by name only.

Apply this only with the user's go. It is independent of Phase B.

## Phase B

**Approved to start once the user gives the go in the VM session.** First steps, in order:

1. Run the verifies:
   - `hermes kanban --help`, and the `--help` of `list`, `create`, `claim`, `complete` and `block`;
   - whether `kanban.dispatch_profiles` is an allowlist;
   - how unattended workers approve commands.

   Record the results in `.harness/hermes-probe.md`.
2. Write `reports/B0-plan.md`. It holds:
   - the exact commands for B1 (six profiles) and B2 (board and dispatcher config);
   - the host reviewer runner design (a systemd user timer plus a script);
   - which BUILD_SPEC files are copied where (gates script, schemas, fixture).

   It changes nothing. Push it for review before B1.
