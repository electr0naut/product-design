# D11: silent truncation in test collection, plus runner robustness (instruction)

**The bug (found in FXL-1B by the agent's check).** `gates.run_cmd` keeps only the last 4,000 characters of a
command's output. `collect_ids` parses that output. So once a project has enough tests, the gates see only
part of the collected ids, and three things go wrong:
- `new_ids` and `removed_ids` are wrong;
- criteria map to tests the gates can't see;
- fail-to-pass runs only on the visible part.

Nothing reports the cut. This is the third silent truncation the pilot has found, after the review diff and
the shared checksum misreading. `collect_ids` is the only place where `run_cmd`'s output is parsed (checked:
the other callers use exit codes or JUnit files).

**Impact on landed tickets:** FXL-1, FXL-2 and FXL-3 may have been gated on partial test lists. Their code
also passed the review. The hidden acceptance suite, which runs after every ticket now, checks behaviour
independently.

## Build (branch only; reviewed; the user deploys)

1. **Collect with full output.** Use a full-output runner for `collect` (like `mutation.run_full`). Fail closed if
   the output is larger than a set limit (`[gates] max_collect_bytes`, default 5 MB), and never parse a clipped
   output.
   - Tests:
     - 500 collected ids are all seen;
     - an output over the limit is a harness error (exit 2), not a short list.
   - Search the kit for any other parse of clipped output, and list what you found in the report.
2. **One bad card never stops the runner.** An unparseable card title, run file or key blocks **that card**
   (`needs_input`, with the reason), and the pass goes on to the next card. Test: a card titled
   `FXL-1b · gatekeeper` is blocked, and a valid card in the same pass is processed.
3. **One key pattern, enforced at load.** Define the ticket-key pattern once, and import it in the loader, the
   runner, the gatekeeper, the branch checks and `specs`. The loader rejects a key the runner can't read, with a
   message naming the allowed form. Test: loading `FXL-1b` fails.
4. **Stall alerts** in the Telegram no-agent cron:
   - one ping when no card has changed state for 45 minutes while any card is `ready` or `running`;
   - one ping when `harness-reviewer.service` has failed 5 times in a row.

   This is a change to the cron script, which is reversible: approved here.
5. **A recorded attempt reset:** `tools/reset_attempt.py KEY --reason "..."`, run by the operator after a review
   file approves it. It writes a `reset` entry (key, base, reason, time) to the fix ledger, and passes are
   counted only after the latest reset for that key and base. A reset without a reason is refused. Tests:
   - passes before a reset don't count;
   - passes after it do;
   - a reset needs a reason.

## After the deploy

**FXL-1B is approved for a reset now, with the reason "gates saw truncated test list (D11 item 1)".** After the
user deploys D11:
1. run the reset;
2. archive FXL-1B's cards and move its run folder aside;
3. reload FXL-1B, FXL-2B, FXL-3B and FXL-4 to FXL-7 in one call (the unstarted cards are archived and reloaded
   too, as before);
4. the queue goes on.

On the base-test edits in FXL-1B (`offset` renamed to `position` in FXL-1's tests): that's required by FXL-1B's
AC0. On a first pass it makes the ticket high-risk, which is correct. On a fix pass it blocks for a person, which
is also correct as designed.

Report as `D11-robustness.md`, with the user's deploy lines in the usual shape.
