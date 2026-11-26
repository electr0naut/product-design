# D15: the runner owns decisions (instruction; branch, then my review, then `harness-deploy`)

**Why:** the practice comparison (`research/reports/Agent harness practice comparison.md`, problem 7) puts us
behind on one point. Every surveyed system has **one durable owner of workflow state that receives decisions as
typed events**. Ours relies on a chat session noticing markdown files. That cost hours, several times. The host
runner already owns the board's state, so make it the owner of decisions too.

## Build

1. **Decision files.** Machine-readable JSON in the product-design repo at `docs/agent-harness/decisions/` on the
   PR branch, one file per decision: `D-<yyyymmdd>-<n>.json`, with `{id, action, key, card?, head?, files?, reason}`.
   Allowed `action`s, and nothing else:
   - `unblock_once`: clear that card's runner attempt, then unblock it;
   - `approve_test_edit`: the D13 ledger entry; it needs `head`, `files` and `reason`;
   - `reset_attempt`: D11; it needs `reason`;
   - `hold`: a hold card before a given ticket's triage;
   - `release`: complete that hold card.

   Anything else, or a missing field, is rejected and logged.
2. **The runner applies them.** On every pass, the host runner fetches the branch into a **host-only** clone with
   `GIT_SAFE` (never checked out), and reads new files under `decisions/` with `git show`.
   - It applies each decision **once, in id order**, and records the applied ids in host-only state.
   - It writes one line per decision to the runner journal, and posts a PR comment (`applied D-…: <result>`, or
     `rejected D-…: <reason>`) through the same `gh` path the driver uses. If posting fails, only that is
     logged.
   - A decision that names a card in the wrong state (for example, unblocking a card that isn't blocked) is
     rejected, not forced.
3. **Rules stay the same.** The approval, reset and unblock code paths are the existing D11 and D13 functions, so
   nothing new decides what's allowed. Only the delivery changes.
4. **Tests:**
   - each action is applied once;
   - a replay changes nothing;
   - an unknown action is rejected;
   - a missing field is rejected;
   - a wrong-state card is rejected;
   - ids are applied in order;
   - the host-only state survives a restart;
   - a corrupt decision file is rejected without blocking the others.

## The trust question (say it in the report)

Anyone who can push to the product-design branch can write a decision file. That includes the VM agent itself.
**That isn't a new risk:** today the agent already runs `approve_test_edit` and the unblocks itself, on my
instructions. But it means decisions aren't separated from the agent yet. Write in the report what a real
separation would need, and don't build it now:
- commits signed with a key only the reviewing session holds; or
- a GitHub identity used only by the reviewer, checked by the runner.

## The agent's role after D15

The agent keeps writing evidence (the driver) and building harness changes. It no longer has to notice my
decisions for routine actions. I write decision files, and the runner applies them within a minute.

Report as `D15-decisions.md`, then `harness-deploy` between tickets.
