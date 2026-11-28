# Phase A4 review

**Approved: A4 is done.** The result is 4 jobs active, 6 paused and 4 removed, as decided. The diagnosis
of the exit 128 is clear, and so is the decision on how to chat: the host is on `caafe5389ae5` and the
image on `fcc26fbd9f16`, so chatting stays on `docker exec -it hermes hermes`.

## Two follow-ups, report only, no changes

**1. Who rewrote `hermes-backup.sh` at about 15:44?** This session changed nothing before A4, so either the
user or Hermes itself did. Ask the user to confirm the rewrite was intended.

**2. What does the nightly backup push, and where?** "Backup complete and pushed" means it commits Hermes
data to a git remote. That data includes credentials (`.env`, `auth.json`, profile auth). Report the
following, as names and paths only, never contents:

```bash
docker exec hermes sh -c 'cd "$(dirname "$(readlink -f /opt/data/scripts/hermes-backup.sh)")" && grep -n -E "git (remote|push|add)|rsync|tar|exclude" hermes-backup.sh'
```

Then report:
- the backup repo's remote URL, with any token in it masked;
- whether that repo is private;
- the repo's `.gitignore`;
- whether any tracked file is a credential file. List tracked files that match
  `.env|auth.json|credentials|token|key`, by name only.

If credentials are already in that remote's history, stop and tell the user; don't try to clean it
yourself. Rewriting history and rotating keys are the user's decisions.

Also check the 03:00 run on 2026-11-25 in `cron/output/50fbaafad58b/` when it's available, and note it in a
later report.

## A5

Approved as written: report the Codex load and which profiles and agent jobs actually run. It's
report-only. Do follow-up 2 in the same pass. It needs the user's go.
