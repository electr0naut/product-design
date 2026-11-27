# D25 review (`d25-runner-actions` @ `264c8e4`), the deploy of `b20b702`, and D26

## The deploy of `b20b702`: it went in while FXL-15's scribe was running
Ubay ran the deploy line. The runner's state file names the kit `b20b702` at 15:23:31, with `FXL-15 · scribe`
running. The commit is the approved one. The moment was not the one `D24-code-review.md` asked for.

**Confirm now, read-only, and report on the PR:**
1. the exact time the host and the container switched, and which cards were running or started within a minute
   either side;
2. the deployed kit as before (fresh-process imports with both interpreters, the tools' `--help`);
3. that the runner pass which spanned the switch ended without an error line, and that FXL-15's scribe finished
   normally;
4. that FXL-15's acceptance run, when it comes, shows the D24 line for `acc-order-story.test.js`. FXL-15 is in
   the new table, so D24 judges it. That is a gain, as long as the run itself is sound.

If anything in 1 to 3 is off, say so first and I will hold the queue before FXL-16.

## D25: approved as built, with one addition
Verified on a fresh worktree at `264c8e4`, in my own container: `663 passed, 3 skipped in 92.32s`; `ruff check`
and `ruff format --check` are clean. I read the decisions, the loader change, `rerun.py`, the evidence section
and the config.

Your four choices:
- **Diffs from the host-only trusted repository:** right, and better than my spec. The host runs no git in a
  work repository.
- **`load_tickets` is not held back while a card runs:** accepted. The sync only acts when the work `main` and
  the trusted one differ, and a deferred decision would hold an unblock behind it.
- **A dropped registry entry does not block a reload:** accepted; a reset needs it.
- **`key` need not be a listed ticket:** accepted.

Also good: every refusal happens before a card is made; a part-way failure is reported as such and not
retried; the diff's code fence cannot be closed by the diff.

**Add to this branch, as a second commit:** `harness-deploy` refuses while a worker card of any repository is
running, and names the card. No flag overrides it. A deploy has now gone in twice at a moment nobody chose;
the first time it fell into a 24-second gap by luck. The rule should not depend on anyone's timing. Test: it
refuses with a running card, and goes through with none.

Then report the new commit; I review it and write one deploy line for D25.

**After that deploy,** before the first real use: apply a `load_tickets` decision that must be refused (FXL-16,
which is already loaded) and report the comment. That runs the new path against the real board without
loading anything.

## D26: nothing is built until Ubay has chosen
`D26-proposal.md` is the most useful report of the day. Three facts in it change the picture, and I am passing
them to Ubay as they stand: the standing session has no allowlist and runs as a user with passwordless `sudo`
and Docker; so the spec's limits cannot be enforced for a job running as that user; and a job that can push can
write a decision file and approve its own work, which the standing session can do today too.

My recommendation to him is A, with signed decisions built together with it, and a time cap plus the budget
flag in place of a turn cap. All three are his: `sudo`, a new user, a new GitHub credential and a Claude login
are in section 3 of `RULES.md`. **Do not start D26 until his answer is quoted in a review file.**
