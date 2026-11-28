# Phase B4 review: first full pipeline run

**Approved.** This is the milestone. Hermes ran PRC-1 through all six stages on its own:
- **Model routing behaved as planned:** the planner fell back to Qwen while Codex is limited, and the
  deterministic gates passed.
- **Reviewer runner:** it claimed and completed a card for real.
- **`main` advanced:** `main` fast-forwarded by deterministic code.
- **Hidden acceptance tests:** **6 of 6** pass.
- **PRC-6 bounced at triage**, with sensible questions for the author.

The run cost about $0.02 in DeepSeek and $0 in Claude, and took 13.5 minutes of wall time. Most of that time
was the 60 s dispatch tick between stages.

The gatekeeper blocking run 1 was the gates doing their job: they refused because the test ids didn't match.

Kit verified: `agent-harness@f7445c9`, `58 passed`, ruff clean.

## Must fix before Phase C

**Budget degradation must not approve unreviewed findings** (`reviewer.py`, the `skipped` handling).

A critical or high finding that is skipped for budget currently becomes a *note*. The card then completes and
`main` advances, with a possibly real defect nobody refuted or proved. Degrading is right for medium findings,
but not for the others.
- **Fix:** add skipped `critical`/`high` findings to `blocking_unproven`, with the reason `budget`. The card
  then blocks for a human. Skipped `medium` findings stay notes.
- **Test:** one critical finding past the cap blocks the card, and `main` doesn't move.

## Decisions (my recommendations)

1. **Bare test ids in the gates: accept, deterministically.** When an id in `implement.json` has no `::`, or
   has a file part plus a name, resolve it to the matching collected id only if **exactly one** matches.
   Report each one under `resolved_ids`. If none or several match, keep today's strict behaviour. This costs
   nothing in safety and stops one sloppy answer from blocking a ticket.
2. **Telegram for blocked tickets: use Hermes's own notifications.** Use `kanban notify-subscribe` for the
   `blocked` event, sent to the Telegram home channel, rather than an LLM stage or a new cron job. It's
   deterministic, costs no tokens and is documented. Check its flags with `--help` and report the
   subscription.
3. **Test the Claude refute/prove path on purpose, with the seeded-bug variants.** Add a small
   `tools/review_variant.py` that does three things for each fixture variant (B1-B6 bugs, C1-C4 clean):
   - builds a branch `variant/<ID>` from the PRC-1-based `main`, adding the reference module(s) and the
     variant's edits;
   - writes the run files the runner needs: `base.txt`, and `readiness.json` copied from the matching
     fixture ticket's criteria;
   - creates one `reviewer` card only.

   That exercises Qwen finding, then Claude refuting and proving, on known bugs. It measures review recall
   and false blocks (DESIGN section 12), and costs at most $3 per card under the cap.
   - **Order:** run B1 first, alone.
   - **Advancing `main`:** variant branches must never advance `main`. Add a guard: only branches named
     `harness/<KEY>` may advance it.

## Board

Archive PRC-1's done cards and PRC-6's cards once you've read this. Keep the `work/runs/` files: they're the
evidence.

## Pending

- The 03:00 backup check on 2026-11-25.
- After Codex resets (2026-11-26 08:21 CET), one planner run to confirm that the Codex route works.
