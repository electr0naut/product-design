# D27 part 1 review (`d27-claude-limit` @ `f326802`): two things before I approve

**Not approved yet.** The design is what I asked for and the code reads right. What is missing is proof of the
one thing the whole change stands on, and a safe ending if that thing fails.

## Verified
- Fresh worktree at `f326802`: `820 passed, 3 skipped in 88.74s`; `ruff check` and `ruff format --check` clean.
  The difference from `6ff69fa` is `claude_wait.py`, the hooks in `reviewer.py` and `statefile.py`, one
  `pyproject.toml` line and the tests.
- Read in full. `ClaudeLimit` and `ClaudeFault` are caught before the general handler; nothing inside
  `review()` swallows them (the one inner `except HarnessError` is around `validate`); a time-out never counts
  as a success; our own budget and turn caps are never a limit; `overageStatus` is ignored, rightly; a wait is
  recorded before the card is parked; the attempt is given back; the heartbeat is stopped on both new paths.
- Your three points to judge: a retry that runs the whole review again is accepted for now (a later change can
  keep finished steps); a deploy during a wait is fine; the quiet notifier during a wait is fine, and I will
  read a "waiting" line in `STATE.md` as expected.
- That no refused-for-limit result has been seen for real is accepted as stated: an unmatched form gets one
  retry and then today's block.

## R1. Show `schedule` and `unblock` on the real board program
Every test uses a stand-in board that **assumes**: `kanban schedule <id> <text>` exists with that shape, works
on a card this runner has claimed, sets a status that `list --json` reports as `scheduled`, and
`kanban unblock <id>` turns a scheduled card `ready`. If any of that is different, the first real limit ends
in R2's problem. Show it with the real `hermes kanban` program on a **scratch board in a throwaway
container** (the image the workers run; nothing live): create a card for the reviewer profile, `claim` it,
`schedule` it with a text, `list --json` (the status string), `schedule` a card that is `ready`, `unblock` a
scheduled one, `unblock` one that is not scheduled, and whatever a dispatcher tick does with a scheduled card
if that can be run there. Paste the commands and their output. If the real verbs or status names differ,
change the code to match and say what changed.

## R2. A park that cannot be done must end as the old block, not as a pass that fails for ever
Today: if `schedule` raises, the pass raises; the wait is already recorded; the next pass tries to park again,
raises again, and so on every minute. While that lasts, `main_pass` never completes, so no gate runs and the
runner reports itself failing. That is worse than the block this change replaces. Make it: a failed park (in
`_park` or in `tend_waits`) is tried again on the next two passes; after the third failure the wait is
forgotten and the card gets the old `transient` block with the reason "could not park the card: ...". Nothing
lands in any of these cases. Tests for: fails once then parks; fails three times then blocks; a failing
`unblock` when a wait is due (the card must not stay scheduled for ever without anyone being told: one alert).

Send the new commit with the proof-container run. I review the difference from `f326802`.
