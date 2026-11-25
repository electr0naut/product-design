# Phase C final review

**Phase C passed.** Verified in the reviewing session on `agent-harness@573a163`: `108 passed in 48.04s`, and
ruff is clean.

- **22/22 hidden tests** were scored against the **trusted** `main`, inside the container. The baseline is
  25/25, with 0 regressions.
- **All five valid tickets were delivered in dependency order.** Each one was fast-forwarded into the trusted
  `main` by the host runner, only after a clean review.
- **PRC-6 bounced at triage**, as designed.
- **Review quality on seeded bugs:** 6/6 caught and proven, and 0/4 false blocks on clean variants. On real
  tickets there was 1 false block in run 1, fixed by giving the refuter read access.
- **Cost of run 2:** $0.098 of DeepSeek, $0 of Claude and $0 of Codex. Qwen ran on the token plan.

The serialization change is correct. The ticket loader can now find blockers already on the board during a
partial reload. `harness.usage` is a useful read-only addition, and the gatekeeper test now asserts the exact
command.

## Accepted limits (state them on the status page)

- **No cost comparison yet.** The `baseline` profile hasn't been run, so there's no ratio against today's flow.
- **Not built yet:** mutation testing, risk tiers and automated fix loops.
- **Codex untested:** the planner hasn't run on Codex yet. That's tomorrow.

## Next items, in order (none block calling Phase C done)

1. **The Codex planner check after the reset**, with the model confirmed from `harness.usage`.
2. **A bounced ticket shouldn't hold up independent ones.** Make it deterministic in the host runner, which
   already polls every minute. When a ticket's `triage` card is blocked as needs_input:
   - `kanban unlink` it from the triage card of the next ticket in the queue, if that ticket isn't
     `blocked_by` it;
   - re-link that next ticket to the bounced ticket's predecessor's `scribe` card, so order is kept;
   - log each re-link.

   Tests:
   - an independent later ticket proceeds;
   - a dependent one keeps waiting.
3. **Telegram noise.** `notify-subscribe` can't filter events, so don't subscribe the stage cards. Instead, a
   Hermes **no-agent cron script**, every 2 minutes, that:
   - pings once per newly blocked, gave_up, crashed or timed-out card (keep a small "already pinged" state
     file);
   - pings once per completed `scribe` card.

   That's the reduced alert set the user chose, with no model calls.
4. **Make the gatekeeper deterministic**, as described in the C2 result review.
5. **Close the prove-worktree symlink race**, as described in the C1.2 review.
6. **Check the 03:00 backup run** in `cron/output/50fbaafad58b/`. It's still unread.
