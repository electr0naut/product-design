# The 4-hour stall: a lower-case ticket key took the review service down

**Cause (from the user's journal):** every runner pass since FXL-1b's gatekeeper card became ready exits 2 with
`cannot read the ticket key from card title 'FXL-1b · gatekeeper'`. The runner's key patterns
(`gatekeeper._STAGE_RE`, `reviewer.py` line 876, and the `_BRANCH` patterns in `reviewer.py` and `trusted.py`) accept
only `[A-Z0-9]` after the dash. I named the follow-up tickets with a lower-case `b`. The loader accepted them, so
the Hermes-dispatched stages ran, and the first host-run stage stopped the whole runner, once a minute, with no
alert.

## Decision (as the user's delegate)

Rename the keys to `FXL-1B`, `FXL-2B` and `FXL-3B`. The ticket files are already renamed in this repo, and FXL-4 to
FXL-7 are unchanged apart from references. Nothing is in flight after that, so **D10 deploys first**, and every
remaining ticket runs with the spec pass and the hidden suite.

1. **You, now:** archive every card of `FXL-1b`, `FXL-2b` and `FXL-3b`, done ones included, and the unstarted cards
   of FXL-4 to FXL-7, plus the hold card `t_01fb15de`. Check the runner's next pass prints `idle; idle`. Don't
   reload anything yet. Log the commands in `D6-morning.md`. FXL-1b's branch and run folder: move the run folder
   to `work/old/`. The branch is reset by the new implementer.
2. **The user:** deploys D10 (`386315c`). I give them the lines.
3. **You, after the deploy:** copy `FXL-1B.md`, `FXL-2B.md`, `FXL-3B.md` and `FXL-4.md` to `FXL-7.md` byte for
   byte, and reload them in one loader call. The loader now records the ticket text host-only, so `record_tickets`
   isn't needed. Check:
   - `~/.local/state/agent-harness/tickets/FXL-1B.md` exists;
   - the hidden suite and the design copy are in place.

   Then the first pass with the spec pass on runs on FXL-1B.

## D11 (next harness change; build after the queue is moving, branch only)

1. **One bad card must not stop the runner.** An unparseable card title or run file blocks **that card**
   (`needs_input`, with the reason), and the pass carries on. A test: a card titled `FXL-1b · gatekeeper` is
   blocked, and the next valid card is still processed.
2. **The loader rejects a key the runner can't read,** using the same pattern, defined once in one module, which
   the runner, gatekeeper, branch check and specs all import. A test: loading `FXL-1b` fails with a message
   naming the allowed form.
3. **A stall alert.** The Telegram no-agent cron also pings when no card has changed state for 45 minutes while
   cards are `ready` or `running`, and when the runner service has failed 5 times in a row (`systemctl --user
   is-failed`, or the journal's exit codes).
