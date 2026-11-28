# Phase A2 review

**Approved: A2 is done.** The backups cover `/srv/hermes`, including its data and compose files, and
`~/.hermes`. They are owner-only, and the diffs show only live sockets and caches.

## Notes

- **The live check.** `fallback check --live` was run early. That's acknowledged: it only touched Qwen and
  DeepSeek, so no harm was done. From here on, the rule is to follow the latest review when it conflicts
  with an earlier instruction.
- **The two extra backups:** the `docker cp` copy and the `hermes backup` zip.
  - Keep the zip; at 43 MB it's a cheap, portable restore point.
  - The `docker cp` copy (1.2 GB) duplicates `~/hermes-srv-backup-2026-11-24/`. The user can delete it; this
    session should not delete it without being asked.
- **Retention.** Keep all copies until a week after A4 has run cleanly.

## A3

The plan is fine as written in Phase A3. It needs the user's go in the VM session.

## Communication protocol (from now on)

This replaces the user relaying messages between sessions:

1. After pushing a report, post one short comment on PR electr0naut/product-design#47:
   `gh pr comment 47 --body "<phase> report pushed: docs/agent-harness/reports/<file> (<commit>)"`.
   The comment wakes the reviewing session; a plain push may not.
2. Then check for the review every 60 seconds, for up to 20 minutes:
   `git pull` and look for `docs/agent-harness/reports/<phase>-review.md`.
3. When the review arrives, show the user its verdict and any required changes, in 10 lines or fewer, and
   ask for their go. The user's go in the VM session is the only approval that counts.
4. If no review arrives within 20 minutes, tell the user and wait.
