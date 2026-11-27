# D20: the runner does the evidence driver's job (D20-review.md and HIDDEN-suite-review.md section 2)

Branch `d20-runner-evidence` in agent-harness, **on top of D19** (`76b094f`, itself not yet reviewed), at **`0458287e25d122daf91ab74845a6cbe392e8195f`**. Not merged, not deployed. No ticket loaded; nothing new written to live host state; nothing published by the new code.

## Test output (fresh clone)
```
522 passed, 3 skipped in 33.76s
ruff check: All checks passed!      ruff format --check: 93 files already formatted
tests/test_d20.py: 43 passed in 1.86s
```

## How the order is guaranteed
The dispatcher claims a ready card within seconds, so a once-a-minute pass cannot win a race. The order is built into the board:
- The loader (with `[pipeline] enabled`) adds an unassigned **gate card `accept <KEY>`** after each ticket's `scribe`. The next ticket, and any ticket `blocked_by` this one, waits on **the gate**.
- Only the runner completes it, after the hidden suite has run with no regression. So **a ticket whose acceptance run has not happened holds the queue by itself**, with the runner stopped, broken or not deployed. The test uses the real loader on a fake board that keeps the "ready only when all parents are done" rule, and checks that the next triage is still `todo` while the suite runs.
- A new load's first ticket also waits on the repository's last open gate. This removes the loading trap in `HANDOFF.md` (a first ticket starting beside a running one). A ticket bounced at triage is skipped, and `relink_bounced` moves waits between gates.
- What was loaded and what is finished is in host-only `pipeline.json`.

**One difference from your wording.** On a regression you asked for the `hold` mechanism. Here **the ticket's own gate stays open and is the hold**: it already covers every current and later dependent, with no card to create and no window. A `release` decision for **that ticket's key** completes it. It can release a gate only after the runner has held it, never one whose suite has not run. A `hold before` card is created only if someone else has already completed the gate. "Held" is recorded before any evidence is queued (tested).

## Where the hidden tests are scored (HIDDEN-suite-review, "Where")
**A separate throwaway container,** not a second user: that needs no `sudo` and no new account, and it is how the bake-offs were scored. `harness/isolated.py`:
- a `git archive` of the trusted `main` into a mode-0700 folder under host-only `scoring/`, refused if any worker-container mount contains it;
- `docker run --network none --cap-drop ALL --security-opt no-new-privileges` with memory and process limits, mounting **only** that checkout and the dependency folder read-only; same image as the `hermes` container;
- the folder is removed afterwards, also on failure; a crashed run's folder and container are removed on the next run;
- no `[score] isolated_cmd` means **no run at all**, never a fallback to `work/`;
- `harness.score`, the old scorer, now **refuses** any folder under the host-only state, so it cannot be pointed at the hidden suite by hand.

**Checked live** (real trusted `main` `e721f31`, the real host suite, scratch under `/tmp`, no history written): **59 of 59**; while it ran the host saw the hidden files, and `docker exec --user hermes hermes ls <that folder>` failed with "No such file or directory"; nothing was left behind and no `acc-*.test.js` was under `work/`.

**No worker card while it runs:** the run waits if any assigned card is `running`. The gate stops pipeline tickets from starting during it. **It does not stop an unrelated Hermes card from starting mid-run**; if one is running afterwards, the evidence says so.

## The rest of the instruction
- **Once, and caught up:** one finishing step per ticket, resumable after a crash at any point; a ticket that finished while the runner was down is handled on the next pass. If the suite cannot run (docker away, a copy that fails verification), the gate stays shut and one alert goes out after the third try.
- **Blocks:** one report per block event (card id plus its count of block events), again on a re-block: card, reason, kind, the full head the host runner last gated, and the findings of the latest review.
- **Nothing from a work folder:** at the moment the runner acts on a gate report, a review or an approval, it keeps a **host-only record**; finishing, evidence and block reports read only those, the trusted repository, host state and the board. Tested by filling the run folder with false files and making it unreadable. Two honest limits: the gate decision itself still reads `gates.json` from the run folder, as before D20; and your "run files" in a block report are the **host records** (counts), not a listing of the work folder.
- **Publishing:** a host-only outbox. Commits are built with git plumbing in a host-only **bare** repository, so nothing is checked out and a link planted on the branch cannot redirect a host write (tested). A failure keeps the item, never repeats the commit, holds nothing, and alerts once after three tries. Commits are authored `harness runner`.
- **State:** `state.json` (host-only) when something changed; `docs/agent-harness/STATE.md` only on events (finished, block, a hold placed or released, a decision applied, kit commit changed). "Instructions without a report" means: a `*review*.md` that says ``Report as `X.md` `` where no `X.md` exists.
- **Alert:** `OnFailure=harness-reviewer-alert.service` runs host code (`harness.alert`), sends the last journal lines (credential-like strings removed) with `hermes send`, once per run of failures; a good pass re-arms it. A pipeline-finish failure now fails the pass, so it alerts.

## Before and during deploy
1. Order: D19 review, then this; `harness-deploy <sha> --install-unit` (**both** units are installed; installing services is Ubay's).
2. Then the D19 order: `refresh_copies`, then `retire_hidden`. **Until the copies are recorded, the hidden suite cannot run and a gate would stay shut.**
3. **Tickets must be loaded with the D20 loader.** A ticket loaded by an older clone has no gate, and the runner does not see it. The old tickets (FXL-1 to FXL-8) are therefore left alone; FXL-9 `blocked_by` FXL-8 falls back to FXL-8's scribe.
4. **Do not start the old driver** once D20 is deployed. Deleting it and `d6-driver` is step 6 of your instruction, **after** one ticket has gone through D20: not done.

## Limits, and what was not run
- **A worker with Kanban tools could complete a gate card.** That is detected (the evidence warns, and on a regression the not-yet-started dependents get `hold before` cards), **not prevented**; a dependent already running is not stopped. Real prevention needs a board permission or a separate owner.
- Isolation keeps the tests away from the worker's container. **The code under test runs beside the tests,** so it can see them while it runs, and could fake a result.
- The model table still comes from the profiles' `state.db`, which workers can write.
- **Alerts go through the `hermes` container:** if it is down, nothing is sent until a later failure. `[alerts] target = "telegram"` is the **home channel**, which may not be the chat the kanban notifier posts to; say if it should be that one. The notifier's own "5 failed passes" ping (D11) is still there, so a long outage can produce that second message.
- The finishing step runs inside the timer pass (the live suite took seconds).
- **Not run live:** a real `hermes send`; `OnFailure=` firing (the two unit files only passed `systemd-analyze verify` with no complaint about them); a publish to the real repository; the loader creating gate cards on the real board; a full runner pass with the pipeline on.
- **Run live, read-only:** the isolated scoring above; the state builder on the real board with all six profiles' models read; the model-table query.

## Tests (`tests/test_d20.py`)
Order: next ticket cannot start before acceptance, including during it; once per ticket; catch-up; a new load waits; blockers use gates, old tickets their scribe; running card defers; a failing suite keeps the gate shut with one alert. Regression: held and recorded before publishing, later loads held, released by decision; release cannot open an un-run gate; a gate completed by someone else; a reset; relink after a bounce. Evidence and blocks with a poisoned, unreadable run folder; once per block event and again for a re-block. Publishing: commit once, planted link, three failures with one alert while the pipeline carries on, unreachable remote, bad paths. State: matches a seeded board with models; published only on events, including a hand-placed hold. Scoring: no network, only the two mounts, private mode, mounted scratch refused, no command means no run, cleanup after failure and crash, repository link and committed look-alike cannot divert or replace hidden tests, old scorer refuses. Alerts: once per streak, retried if unsendable, redaction. Units and reviewed config. The real runner `_pass` finishes and reports, also when gate work fails. `tests/test_acceptance.py` now stubs the scorer (it tests the history rules).

## Created and deleted in this job
Deleted: scratch `/tmp/d20-live` (including the live scoring folder).
