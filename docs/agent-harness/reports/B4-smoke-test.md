# Phase B4: timer install, PRC-1 smoke test, PRC-6 bounce test, 2026-11-24

User asked for all three in one message. No secrets recorded. Kit: `electr0naut/agent-harness@f7445c9` (private). 58 tests pass on the host and in the container.

## Done before the tests

- Review follow-ups (`689f8fa`): the attempt counter clears whenever a review finishes (blocked or not); the budget cap now degrades (rest recorded as notes with
  `skipped_budget`) instead of failing the card. The old "budget blocks" test was replaced by three new ones.
- **Timer installed** with your OK: units copied to `~/.config/systemd/user/`, `systemctl --user enable --now harness-reviewer.timer`,
  `sudo -n loginctl enable-linger ubay` (`Linger=yes`). The first passes logged `idle` every 20-60 s.

## PRC-1 (Money value type): all six stages done on the second run

Run 1 stopped at the gatekeeper, which is a finding (below). Run 2, after tightening the card text, completed. Wall time about 13.5 min from load to `scribe` done
(588 s of worker time; the rest is the 60 s dispatch tick between stages). Model = what the profile's `state.db` recorded for the run's session.

| Stage | Profile | Model that answered | Provider | Time | Tokens in / out | Cost |
|---|---|---|---|---|---|---|
| triage | triage | qwen3.7-plus | alibaba-token-plan | 97 s | 28,824 / 4,440 | not metered (token plan) |
| planner | planner | **qwen3.7-plus** (Codex was primary, rate-limited) | alibaba-token-plan | 185 s | 70,900 / 7,629 | not metered |
| implementer | implementer | qwen3.7-plus | alibaba-token-plan | 157 s | 83,125 / 6,802 | not metered |
| gatekeeper | gatekeeper | deepseek-flash | deepseek | 27 s | 6,065 / 2,168 | $0.0026 |
| reviewer | host runner (find with `reviewer` profile) | qwen3.7-plus | alibaba-token-plan | 36 s | 14,911 / 1,485 | $0.00 Claude |
| scribe | scribe | deepseek-flash | deepseek | 86 s | 45,482 / 13,307 | $0.0178 |

Claude subscription: $0 spent. Codex: not used (the planner fell back to Qwen as expected).

Results:
- **Gates:** passed. 8 valid new tests, 0 pass on base, 0 fail on head, no missing criteria, no over-budget or unmapped tests, lint and pass-to-pass pass, no critic needed.
- **Reviewer verdict:** 0 findings. So the refute and prove steps (the Claude calls) **did not run**, and the live Claude path is still untested; only the Qwen "find" call and the claim/complete loop ran for real.
- **`main` moved:** yes, `main` fast-forwarded from `f3e31cf` to `4ae31a8` (= `harness/PRC-1`), by `advance_main`, nothing pushed (the fixture repo has no remote).
- **Hidden tests for PRC-1:** 6 of 6 pass on `harness/PRC-1`.
- **Artifacts** in `work/runs/PRC-1/`: readiness, plan, implement, gates, findings/refutations/proofs/review (all empty findings), `handoff.md` (37 lines), `mr.md` (48 lines, no unreplaced `{...}`).

### What run 1 found (a real defect, now worked around, not fully fixed)

The implementer's `implement.json` listed tests by bare function name (`test_money_add...`) while the gates compare full pytest ids (`tests/test_money.py::test_...`).
The gatekeeper correctly blocked: `missing_acs` = all five, `unmapped` = all eight, although all 8 tests were valid and lint and pass-to-pass passed.
I changed the planner and implementer card text to demand full node ids (`f7445c9`, with a test) and reran from scratch; run 1's branch is kept as `attempt1/PRC-1`
and its files in `work/runs/PRC-1.attempt1/`. Qwen followed the new wording. **Recommendation (needs your decision and review):** also make the gates resolve a bare name when it matches
exactly one collected id, so one sloppy answer does not block a ticket.

## PRC-6 (deliberately vague): bounced at triage

- Triage ran for 64 s (qwen3.7-plus via alibaba-token-plan), wrote `ready: false`, and **blocked the card**; the other five PRC-6 cards stay `todo`. No branch was created.
- Reasons: "Make it faster" has no measurable target; "clean up anything else that looks off" has no outcome and unbounded scope.
- Questions for the author (4): the performance target and baseline; which files or modules; what exactly to clean up (or split the ticket); whether anything blocks it.
- **Not done: posting the questions to Telegram.** Nothing is subscribed (`kanban notify-list`: no subscriptions) and I did not message Telegram. Decide how it should work (a
  `notify-subscribe` for the blocked event, or the scribe/a cron job as the doc suggests).

## Gaps

- Claude refute/prove not exercised live (needs a ticket that produces findings).
- No automated fix cards or fix loop yet; no `risk.py`.
- Telegram notification for blocked tickets not built.
- Board state: PRC-1's seven cards are `done`, PRC-6's triage card is `blocked`, the rest `todo`; I left them for the reviewer to inspect (`kanban list`). Say when to archive.

## Next

Phase C (PRC-1 to PRC-6 together; scoring against the hidden tests) once you and the review agree on: the bare-id tolerance in the gates, the Telegram notification, and a way to
exercise the Claude refute/prove path. Codex resets on 2026-11-26 08:21 CET; the planner will switch back to it then. The 03:00 backup on 2026-11-25 is still the pending check.
