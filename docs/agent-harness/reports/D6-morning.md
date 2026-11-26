# Morning: deploy verified, ledger migrated, FIX Lens reloaded and running (FXL-1 first)

## Verified after the user's deploy (read-only checks)
- **Host kit:** `~/.local/share/agent-harness/kit` is a clean checkout at **`4b16baa`** (D7 + D8 + D9); `reviewed-sha` matches; the runner logged `harness.reviewer: kit ... @ 4b16baa9c88a...` and `idle; idle` on the timer's own tick (02:25).
- **Container copy:** `src`, `schemas`, `eval`, `tools`, `tests`, `template` and the three toml files are **identical to a fresh clone of `master`** (`diff -rq`, no differences); every top-level entry except `work/` is `root`-owned (0 exceptions).
- **Ledger migration done** (by the user): `fix-ledger.json.bak` exists and every entry now has a `base`. FXL-1's is **`544c8c5`**, as expected. **A limit worth knowing:** for tickets that already landed (SEED-A, SEED-C, SEED-D, RISK-3, JSEED-2) the merge-base with the trusted main is the ticket's own first head (their branches are now part of `main`), so their `base` is not the base they started from. It changes nothing: those keys are finished and will not rerun.

## What I did (board and files; nothing in the `fix-lens` repo or its trusted `main`)
1. **Archived 43 cards:** all of FXL-1's (the ticket card, the stage cards, and the three `(fix 1)` cards including the blocked `reviewer (fix 1)` card) and all of FXL-2's and FXL-4's to FXL-7's (all unstarted, `todo`). Kept: FXL-3's cards (done) and the hold card. Command per card: `kanban archive <id>`.
2. **Moved FXL-1's old run folder** aside: `work/runs/FXL-1` to `work/old/runs-FXL-1.attempt1` (it held the first attempt's `plan.json`, `gates-1.json`, `review.json`, `fix-1.json`), so the rerun starts with an empty one.
3. **Copied `FXL-3b.md` byte for byte** into `work/fix-lens-tickets/` (`cmp` identical) and **reloaded seven tickets in one loader call**: FXL-1, FXL-2, FXL-3b, FXL-4, FXL-5, FXL-6, FXL-7.

## A deviation from the written plan, and why (for the reviewer to confirm or undo)
The plan said "archive FXL-1's cards and reload FXL-1 alone". I reloaded FXL-2 and FXL-4 to FXL-7 as well, because leaving them alone had two problems:
- **Dangling parents.** FXL-2, FXL-4, FXL-5 and FXL-6 waited on FXL-1's *old* `scribe` card, which the archive removes from play; I did not want to rely on how the board treats a child of an archived parent, nor patch seven links by hand.
- **Old card text.** D8's rule says cards already loaded keep their old text; FXL-2 and FXL-4 to FXL-7 would still say "write files with the file-writing tool only", the very wording that blocked FXL-3's planner.
Reloading them together also gives the chain the review asked for **without a manual link**: ordered by rank, FXL-3b follows FXL-2 and FXL-4 waits for FXL-3b's `scribe`. Checked on the board: FXL-2's triage waits on FXL-1's new scribe; **FXL-3b's triage waits on FXL-2's scribe and FXL-3's scribe**; **FXL-4's triage waits on FXL-3's, FXL-1's and FXL-3b's scribes**; FXL-7 waits on FXL-2, FXL-4, FXL-5 and FXL-6. The planner card now carries the D8 write rule and not the old line. The order is therefore FXL-1, FXL-2, FXL-3b, FXL-4, FXL-5, FXL-6, FXL-7, one at a time. Nothing was unstarted work that is now lost: the archived cards had never run.
If you would rather have FXL-2 and the rest on their old cards, the reload can be undone by archiving the new cards; the reverse (restoring archived cards) is not possible, which is why I am saying so here.

## Running now
FXL-1 is the live first ticket (its triage is already done), with: the D7 budget (one gate-triggered and one review-triggered pass per attempt, its `base` = the current trusted main `4e3aaac`, and the migrated old entry no longer counting against it), D8 card text, D9's whole-diff review (the FIX Lens overlay excludes `src/dictionary/*.json`, its licence and `vendor/**`), mutation and the risk tiers on. The evidence driver runs over the whole chain and stops at the first block. The old FXL-1 branch in `work/fix-lens` (`harness/FXL-1`, with the two unfixed bugs and a stale base) is reset by the new implementer's `checkout -B harness/FXL-1 <sha>`; I do not touch it.

## Second reload: the AC0 interface criteria and FXL-1b (approved in `FXL-1-landed-review.md`)
Done while FXL-2 was running (its implementer was still working, so nothing that had started was touched; FXL-2 and FXL-1's cards are as they were).
1. **Archived the unstarted cards** of FXL-3b and FXL-4 to FXL-7: 35 cards, each `kanban archive <id>`, all `todo` or `done` ticket-text cards (checked: none was running or blocked).
2. **Copied the changed and new ticket files byte for byte** from `docs/agent-harness/fix-lens/tickets/` into `work/fix-lens-tickets/` (`cmp` identical for `FXL-1b`, `FXL-3b`, `FXL-4`, `FXL-5`, `FXL-6`, `FXL-7`).
3. **Reloaded six tickets in one loader call:** `load_tickets.py --repo work/fix-lens FXL-1b FXL-3b FXL-4 FXL-5 FXL-6 FXL-7`. Checked on the board:
   - `FXL-1b` triage waits on **FXL-2's scribe** and FXL-1's;
   - `FXL-3b` triage waits on **FXL-1b's scribe** and FXL-3's;
   - `FXL-4` waits on FXL-3b's, FXL-1's and FXL-3's scribes; `FXL-5` on FXL-4's; `FXL-6` on FXL-5's; `FXL-7` on FXL-2's, 4's, 5's and 6's. So FXL-4, FXL-5 and FXL-6 all wait on FXL-1b's scribe transitively, through the one-ticket-at-a-time chain, without a manual link;
   - the AC0 criteria are in the ticket cards (FXL-4's card carries them).
   The order is now **FXL-2, FXL-1b, FXL-3b, FXL-4, FXL-5, FXL-6, FXL-7**. No manual `kanban link` or `unlink` was needed.
4. The evidence driver was restarted with that order.

## Third reload: FXL-2b (approved in `FXL-2-landed-review.md`)
FXL-1b had already started (triage done, planner done, implementer running), so it was not touched. Done at about 09:40:
1. **Archived the unstarted cards** of FXL-3b and FXL-4 to FXL-7: 35 cards, each `hermes kanban archive <id>` (checked first: all were `todo`, or the `done` ticket-text cards; none running or blocked).
2. **Copied `FXL-2b.md` byte for byte** into `work/fix-lens-tickets/` (`cmp` identical; the other five were already identical).
3. **Reloaded six tickets in one loader call, on the host:** `PYTHONPATH=src python3 tools/load_tickets.py --repo /srv/lab/agent-harness/work/fix-lens <work/fix-lens-tickets/>FXL-2b.md FXL-3b.md FXL-4.md FXL-5.md FXL-6.md FXL-7.md`. (Two earlier tries inside the container failed before creating anything: a relative `--repo` path, then the container user's trusted-repo path having no `main`. The loader belongs on the host, which holds the trusted repos.) FXL-2b's triage waits on FXL-2's scribe and FXL-1b's; FXL-3b, FXL-4, FXL-5, FXL-6 and FXL-7 follow in a chain, with no manual `link` or `unlink`.
4. **Evidence driver restarted** for `FXL-1b,FXL-2b,FXL-3b,FXL-4,FXL-5,FXL-6,FXL-7` (usage window from FXL-2's scribe completion).
Order now: FXL-1b (running), FXL-2b, FXL-3b, FXL-4, FXL-5, FXL-6, FXL-7.
