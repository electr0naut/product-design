# Phase B5: budget fix, short test ids, Telegram alerts, first review variant (B1), 2026-11-24

User approved the review's recommendations (short ids accepted only when unique; Hermes's own notifications; test Claude's review on the seeded-bug variants, starting with one bug).
Kit `electr0naut/agent-harness@3bec119` (private): 71 tests pass on the host and in the container, ruff clean. No secrets recorded (the Telegram chat id is masked).

## Must-fix from the B4 review: budget degradation can no longer approve a serious finding

A critical or high finding skipped for budget now goes to `blocking_unproven` (the card blocks for a human); skipped medium findings stay notes. Tests: a high finding past the cap blocks the card
and `main` does not move; a medium one past the cap is a note and the card completes.

## Decision 1: short test ids (gates)

`resolve_id`: a bare name, or `file::name` missing its directory, resolves only when **exactly one** collected id matches; each is reported under `resolved_ids`. Zero or several matches keep the strict behaviour.
Tests: bare name resolves, partial file form resolves, an ambiguous name and an unknown name both stay missing.

## Decision 2: Telegram alerts for blocked tickets (Hermes's own notifier, no model, no tokens)

`tools/load_tickets.py --notify-telegram` subscribes every stage card (`kanban notify-subscribe --platform telegram --delivery-mode notify`, passive: never `notify+wake`) to the Telegram home channel
(read from the container `.env`, group chat detected from the id). Terminal events (`completed`, `blocked`, `gave_up`, `crashed`, `timed_out`) each send one ping, and the subscription ends at `done`.
- Live test: I archived the old PRC-6 cards and reloaded PRC-6 with the flag. Triage blocked it again (about 64 s), and the notifier's checkpoint for the `blocked` event (`last_ping_event_id` = 220 = the blocked event)
  shows the ping was sent. **Please confirm that your Telegram group received a "PRC-6 · triage blocked" message**; I cannot see the chat.
- Noise: up to 6 pings per ticket on success (one per stage `completed`). If that is too much, subscribe only triage, gatekeeper and reviewer, or drop `completed` pings.

## Decision 3: Claude's review on the seeded bugs (variant B1 first)

New: `src/harness/variants.py` and `tools/review_variant.py` (`prepare`, `card`, `score`). Variants live in their own repo `work/variant-repo` (the pipeline's `fixture-repo` and its `main` are untouched):
base = baseline + reference modules of the tickets before the variant's; head = base + the variant ticket's reference module with the variant's edits; the diff has no tests. Runner changes: a
`branch.txt`/`repo.txt` in the run folder point it at the variant, the card key accepts `VAR-B1`, and **only branches named `harness/<KEY>` can advance `main`** (tested).

**B1** (PRC-4, tier break no longer inclusive; `pricing/tiers.py` line 26 `if qty > min_qty:`), reviewed on the real path:

| Step | Result |
|---|---|
| Find (Qwen, `reviewer` profile) | 1 finding: high, confidence 97, `pricing/tiers.py` line 27 ("uses strict greater-than instead of greater-than-or-equal") |
| Filter | kept (line 27 is within 3 of the changed line) |
| Refute (Claude sonnet) | **stands** |
| Prove (Claude sonnet, scratch worktree) | wrote `tests/test_tiers.py::test_unit_price_at_exact_break_min_qty_uses_that_break`; re-run in a clean worktree: **assertion failure, proven** |
| Decision | 1 proven, card blocked `needs_input`; `main` untouched |
| Score | **caught** (finding file matches, line within tolerance of bug line 26); cost **$0.378** of Claude |

So the Qwen-find, Claude-refute and Claude-prove path now works live, from a systemd timer pass, with the JUnit-based proof and the path checks in place.

### Two problems found on the way

1. The first B1 run failed with "No such file or directory: 'claude'": under systemd the PATH lacks `~/.local/bin`. The one-attempt guard worked as designed (card blocked `transient`, no retry, no spend).
   Fix: absolute `bin = "/home/ubay/.local/bin/claude"` in `harness.host.toml` and a `PATH` line in the unit (reinstalled, timer restarted). I archived the failed card and cleared its attempt counter by hand
   (`work/reviewer-attempts.json`), then created a fresh card. Lesson: the PRC-1 smoke test never called Claude, so this had never been exercised under systemd.
2. The attempt counter is cleared only when a review finishes; an infrastructure failure like this one needs a human to clear it. That is intended, but note it.

## Board

Archived: all PRC-1 cards, the old PRC-6 cards, both B1 cards. Live: the new PRC-6 set (triage blocked, five `todo`). `work/runs/` files are kept (PRC-1, PRC-1.attempt1, PRC-6.attempt1, VAR-B1).

## Not done yet

Variants B2 to B6 and C1 to C4 (recall over 6 bugs and false blocks over 4 clean variants), and Phase C (PRC-1 to PRC-6 together, scored against the hidden tests). Budget: B1 cost $0.38, so the other nine
should be about $3 to $4 of Claude in total, each card capped at $3. Say go and I run them one at a time.
