# Phase A1 review

Reviewer: cloud Claude session. Input: `A1-inventory.md` (commit 8f18e55). I re-ran nothing; this review
reads the report only.

## Verdict

The inventory is clear and complete for a read-only pass, and it changes the plan. **Do not start A3 to A5
(moving everything to the host gateway) until the user decides on the runtime question below.** A2 backups
are fine to do now, with the narrowed scope in "Answers".

## What the report shows

1. **The container is the real system, not a side copy.**
   - It is a deliberate deployment, a compose project at `/srv/hermes`, with data on the host at
     `/srv/hermes/data` and `/srv/lab` mounted in.
   - It is the only install with bot tokens (Telegram and Discord).
   - It runs 14 cron jobs: health checks, a nightly backup, a Discord watchdog, email and delivery
     monitors, and the news briefings.
   - The host install has one profile, no cron jobs and no bot tokens.
2. **Moving all of that to the host is a large migration with little gain.** Many jobs are no-agent
   scripts that probably live under the container's data or `/srv/lab` paths. Each one would need moving
   and re-testing, plus the bot tokens, and it puts a working setup at risk.
3. **The chains are already fixed.** The container's fallback chain now matches the host's, and the
   `-fable` profiles are gone.
4. **New risk: every container profile now has `gpt-6-sol` (Codex) as its primary model.** Codex has a
   7-day usage window and is already exhausted until 2026-11-26. With all 22 profiles plus agent cron jobs
   on it, it will run out again quickly, and everything then falls back to Qwen. That's acceptable only
   if it's intended.
5. **The host gateway (PID 90439) runs manually with no bot tokens and no cron jobs.** It does nothing
   useful at the moment.

## Recommended change of direction (user decision)

**Keep the container as the single always-on Hermes, and stop the host gateway.** It is already the
docs-supported Docker deployment, with a restart policy, a compose file and data on a host path.

- **Chatting from the terminal.** Point the host CLI at the same data, with
  `HERMES_HOME=/srv/hermes/data hermes`, instead of keeping a second, separate setup. **Verify first** that
  the host Hermes version (v0.23.3) matches the image's, so both read the same config format. Never run a
  host gateway against that folder: the docs say one gateway per data folder.
- **Phase B** (pipeline profiles and Kanban) then gets built inside the container's data, through
  `docker exec hermes hermes ...`.
- **Open issue for Phase B: the cross-lab reviewer step calls `claude -p`, and `claude` isn't in the
  container image.** The docs say the image is immutable and APT installs aren't possible. Possible
  approaches:
  - install the Claude Code native binary into the mounted `/srv/lab`, with its login stored there too;
  - have the reviewer card call a small host-side service;
  - run that one stage from the host on a timer.

  I'd pick the first only if `/srv/lab` is private to this user. Decide this before B4.

If the user still prefers the host as the runtime, the original A3 to A5 stay valid. They need a per-job
migration plan for the 14 jobs first.

## Answers to the open questions

1. **`fallback check --live`.** Wait until after Codex resets (2026-11-26 08:21 CET). Running it now only
   confirms the known rate limit and uses quota.
2. **Cron jobs (the user decides; my suggestions):**
   - Keep the health checks, nightly backup, Discord watchdog, email, Amazon and personal-care jobs, and
     the AI-news, politics and news-push briefings.
   - **Markets briefing:** pin it to `qwen3.7-plus` on `alibaba-token-plan` (working now) and remove the
     placeholder-key provider. Today it has failed 26 times in a row.
   - **Remove** `call-home-insurance` (its one-time date has passed) and the paused
     `OpenAI Codex <-> DeepSeek failover` script, which the built-in fallback chain replaces.
   - **`Agentic Stack setup progress`:** ask the user; it's paused and runs every 5 minutes when active.
   - **`hermes-nightly-backup`** exited with code 128 at 03:00. Exit 128 usually comes from git (for
     example a failed push or a bad path). Check its log before trusting the backups. "Recovered" isn't
     enough.
3. **A2 backups.** Approved in scope, but change the commands:
   - Back up `/srv/hermes/data` and `/srv/hermes` (the compose files) directly on the host:
     `sudo cp -a /srv/hermes ~/hermes-srv-backup-$(date +%F)`.
   - Back up `~/.hermes` the same way.
   - There's no need for `docker cp`.
   - The data contains credentials, so keep the copies owner-only: `chmod 700` on the backup folders.

## Corrections to the orchestration doc (pending the runtime decision)

- A2's "42 container profiles" is now "22 profiles (`default` plus 21 roles)".
- Phase A will be rewritten once the user chooses between keeping the container (recommended) and moving
  to the host.

## Next step

The VM session waits. The user answers: (a) which runtime, (b) which cron jobs to keep, (c) approval for
A2 with the commands above.
