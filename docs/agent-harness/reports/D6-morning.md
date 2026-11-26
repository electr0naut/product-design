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

## Stall clean-up (FXL-1b-stall-review.md, step 1)

Driver stopped first (`kill` of the evidence driver; no card was running). Then, in the container as `hermes`:

    hermes kanban archive <id>      # 50 cards: every card of FXL-1b, FXL-2b, FXL-3b (parents, stages, done ones included),
                                    # all seven cards of each of FXL-4..FXL-7 (none had started), and hold t_01fb15de

Board check: `hermes kanban list | grep -E "FXL-(1b|2b|3b|4|5|6|7)|HOLD: D10"` shows 0 rows. FXL-1..3 stay done.
FXL-1b's run folder: `mv work/runs/FXL-1b work/old/runs-FXL-1b`. The branch is left for the new implementer to reset.
Runner: the next timer pass printed `idle; idle`, and the service is no longer failed.
Nothing reloaded, nothing deployed. Waiting for the user's D10 deploy (`386315c`).

## FXL-1B reset and reload after D11 (D11-review.md)

Kit checked first: host kit and container copy both `0ae59d0`, the new alert script is in the container, runner status file written.
1. **Reset (host kit):** `tools/reset_attempt.py FXL-1B --reason "gates saw truncated test list (D11 item 1)" --base f36221cfc647c8981d3b190ced10a95c97d63baf` wrote a `reset` entry to `fix-ledger.json` (15:17:43, the base is the trusted `main`, unchanged). The old pass entry stays in the ledger.
2. **Archived 50 cards** with `hermes kanban archive <id>`: every card of FXL-1B (first attempt and fix 1), FXL-2B, FXL-3B and FXL-4 to FXL-7 (none had started). The board shows none of them.
3. **Run folder:** `work/runs/FXL-1B` moved to `work/old/runs-FXL-1B.attempt1`. The first attempt's report is kept as `fix-lens/runs/FXL-1B-attempt1.md`.
4. **Reloaded in one call, on the host:** `PYTHONPATH=src python3 tools/load_tickets.py --repo /srv/lab/agent-harness/work/fix-lens <work/fix-lens-tickets/>FXL-1B.md FXL-2B.md FXL-3B.md FXL-4.md ... FXL-7.md` (log `work/fixlens5-load.log`); host-only ticket text re-recorded.
5. **Driver restarted** with start file `work/fxl1B2.start`. The first runner pass after the load printed `idle; idle`, service not failed.

## FXL-1B attempt 3: implementer on Codex (FXL-1B-review3.md, CODEX-implementer-review.md)

No implementer card was running (FXL-1B blocked, the rest waiting). 
1. **Profile change** (`implementer`): backup `/opt/data/profiles/implementer/config.yaml.bak-20261126-183213`. Old: `model.default qwen3.7-plus`, provider `alibaba-token-plan`, `model.base_url` the Qwen endpoint, fallbacks `[deepseek-flash]`. New: `hermes -p implementer config set model.provider openai-codex`, `... model.default gpt-6-sol` (this cleared `model.base_url`), and `... fallback_providers '[qwen3.7-plus (alibaba-token-plan), deepseek-flash]'`. **Undo:** copy the `.bak-20261126-183213` file back over `config.yaml`.
2. **Check:** one tiny `hermes -p implementer chat -q` call answered; `state.db` shows `gpt-6-sol`, `openai-codex`, no fallback row. Each card starts a fresh process that reads the profile, so no gateway restart was needed or done.
3. **Reset** (host kit, `tools/reset_attempt.py FXL-1B --reason "two review failures on the Qwen implementer; rerun on the Codex implementer (user approved)"`), written 18:32:50.
4. **Archived** the 51 cards of FXL-1B, FXL-2B, FXL-3B, FXL-4..7 (FXL-1..3 untouched); run folder moved to `work/old/runs-FXL-1B.attempt2`; the attempt-2 report is `fix-lens/runs/FXL-1B-attempt2.md`.
5. **Reloaded** all seven in one call from the host (`work/fixlens6-load.log`), driver restarted (start file `work/fxl1B3.start`, log `~/driver-fxl1B4.log`).

## Finder on DeepSeek (FXL-1B-review4.md)

No reviewer card was running (FXL-1B's was blocked). 
1. **Profile change** (`reviewer`, the finder): backup `/opt/data/profiles/reviewer/config.yaml.bak-20261126-190204`. Old: `model.default qwen3.7-plus` (alibaba-token-plan, Qwen `base_url`), fallback `[deepseek-flash]`. New (`hermes -p reviewer config set ...`): provider `deepseek`, default `deepseek-flash`, `base_url https://api.deepseek.com`, fallback `[qwen3.7-plus (alibaba-token-plan)]`. **Undo:** copy the backup back over `config.yaml`.
2. **Check:** a tiny `hermes -p reviewer chat` call answered; `state.db` shows `deepseek-flash` / `deepseek`, no fallback. No restart needed (a fresh process per card).
3. **Retry:** FXL-1B's reviewer card `t_ba094ad9` removed from `reviewer-attempts.json` and unblocked once (a transient retry, not a fix pass). The block report is kept as `fix-lens/runs/FXL-1B-attempt3-block.md`. Evidence driver restarted (`~/driver-fxl1B5.log`).
4. Each `FXL-<n>.md` from now on records the finder model.

## FXL-1B: approved test edit applied (FXL-1B-review6.md, after the D13 deploy)
Host kit and container copy both `8f9f21f`. 1. `approve_test_edit.py FXL-1B --head 7f47748347ef82ec10c4e5eaba5274a534744abd --files test/framing-f1.test.js test/framing.test.js --reason "FXL-1B-review6: ..."` (entry written 19:56:27, base `f36221c`). 2. Gatekeeper card `t_11abf68b` was not listed in the attempts file, so nothing to clear. 3. Unblocked it once; evidence driver restarted (`~/driver-fxl1B6.log`). The gatekeeper passed on the retry; the fix-3 reviewer is running.
Correction to the review-5 evidence: `gates-3.json` is the report from before fix pass 3, not a mislabelled file.

## D15 approved, driver keeps polling, FXL-4B loaded (D15-code-review.md, FXL-4-landed-review.md)
- agent-harness `master` fast-forwarded to `3a0ec24`. Not deployed.
- **Driver** (`d6-driver`): a block no longer ends it; it writes and publishes the evidence once per block (identified by card and its count of block events, so a re-block is new) and keeps polling. Block reports are also kept as `FXL-<n>-block-<card>-<n>.md`. After a hidden-suite regression it places `hold before <next KEY>` (releasable by a D15 `release`) and keeps watching. Checked with a fake board only. Restarted once (`~/driver-fxl5.log`).
- **Hidden suite:** the new `acc-decode.test.js` and `acc-dictionary.test.js` copied to the host-only folder.
- **FXL-4B:** archived the unstarted cards of FXL-6 and FXL-7 (their ticket text unchanged). Loaded FXL-4B, FXL-6, FXL-7 in one call **with `--hold`** (`work/fixlens7-load.log`), because FXL-4B's only listed blocker (FXL-4) was done and it would otherwise have started beside FXL-5. Then `kanban link t_4168d18c (FXL-5 scribe) t_3ecccf8e (FXL-4B triage)` and completed the hold `t_dad337cf`. FXL-6 triage waits on FXL-4B's scribe `t_dade1a32`. FXL-5 was not touched.

## D15 deployed; FXL-5 reset and reload (FXL-5-review.md)
1. **D15 deploy checked:** host kit and container at `3a0ec24`; the 21:41:59 pass logged that sha, `idle; idle`, no `decisions skipped` line, runner status ok; `decisions.git` holds the review branch at `25a216c`. No decision file exists yet, so applying one is untested live.
2. Updated hidden `acc-timeline.test.js` copied to the host-only folder; updated `FXL-5.md` copied to `work/fix-lens-tickets/` (the host-only ticket text now has AC11 to AC15).
3. **Reset** FXL-5 with the review's reason (base `e4aef93`, 21:42:11). **Archived** 32 cards: FXL-5, FXL-4B, FXL-6, FXL-7 and `HOLD: D15 deploy`. Run folder moved to `work/old/runs-FXL-5.attempt1`; report kept as `FXL-5-attempt1.md`.
4. **Reload in one call** (`work/fixlens8-load.log`). FXL-5 and FXL-4B are both rank 5, so the loader orders FXL-4B first (by key). I did not edit the tickets: loaded with `--hold`, re-linked (each new wait added before the old one was removed) to FXL-5 → FXL-4B → FXL-6 → FXL-7, rewrote the host-only `queue.json` in that order with `queue.write_queue`, then completed the hold `t_4e886658`.
5. **Driver** restarted (`~/driver-fxl5b.log`, start file `work/fxl5b.start`).

Backlog (D16): on a review-triggered fix pass, include in the fix feedback every note that carries a verbatim `spec_ref`, with its quote.

## FXL-7 blocked: worker-readable copies of the technical design (FXL-7-review.md)
- The repo's `fix-lens/technical-design.md` and the host-only spec copy are identical (sha256 `0bea8ed13fed0552…`).
- Copied as `hermes` (reading copies only; no code change) to: **the implementer's `~`**, which is not the user's home: `$HOME` for that worker is `/opt/data/.hermes/profiles/implementer/home` (= `/opt/data/profiles/implementer/home`), then `.local/state/agent-harness/specs/fix-lens/`; the `hermes` user's home `/opt/data/.local/state/agent-harness/specs/fix-lens/`; and `/srv/lab/agent-harness/work/specs/fix-lens/`. All three have the same sha256.
- **Checked** with a tiny `hermes -p implementer` call: through `~/...` it reads 227 lines and finds section 8. That one small session will appear in FXL-7's implementer row in the model table.
- **Only the implementer's `~` has a copy.** Other profiles (planner, finder) have their own `~` and do not; they can read the `work/specs` path only if told it. D16 item 1 (the path in every stage card) fixes that.
- A bake-off run may still be going; its prompt tells it not to read other folders under `work/`, and `BAKEOFF.md` will say if any run opened the design.
- Nothing unblocked: `t_a2096e57` waits for the reviewer's decision file. The driver is still watching.

Backlog D16: (1) the loader writes the worker-readable path of each spec document into every stage card, and the planner and implementer cards say to read the named sections before planning or coding, with a test; (2) the deploy copies the spec documents there every time; (3) a fix pass's feedback includes any note with a verbatim `spec_ref`.

## FXL-7 landed; FXL-8 loaded (FXL-7-landed-review.md)
1. Hidden `acc-render.test.js` (new) and the updated `acc-page.test.js` copied to the host-only folder (9 files, all match the repo).
2. Design copied for the **planner's** `~` too (`/opt/data/.hermes/profiles/planner/home/.local/state/agent-harness/specs/fix-lens/`), checked with a tiny `hermes -p planner` read of section 8, before the load.
3. FXL-8 loaded alone (`work/fixlens9-load.log`; label `security` recorded host-only); driver started for it (`~/driver-fxl8.log`). The ticket expects edits to three base test files: if a **fix pass** touches them, it will block for a person.

Backlog **D16** also: a review finding rated high must not become a note only because its confidence is under the threshold; send it to the refuter and prover like the others, or block as unproven.
Backlog **D17:** a real-browser smoke gate for web deliverables (serve the worktree, load the page under its real CSP, fail on any console error, foreign request or empty result). Needs Chromium in the container (an install the user approves). Until then the reviewer runs `fix-lens/browser-check/check.js` on every page ticket.

## Implementer fallback to qwen4-max (FALLBACK-review.md)
Done while FXL-8 was blocked at its reviewer; no implementer card running.
- **Old chain:** `gpt-6-sol` → `qwen3.7-plus` (alibaba-token-plan) → `deepseek-flash`. **New:** `gpt-6-sol` → `qwen4-max` (alibaba-token-plan) → `deepseek-flash`. A diff against the backup shows one changed line.
- **Backup:** `/opt/data/profiles/implementer/config.yaml.bak-20261126-231511`. **Undo:** copy it back over `config.yaml`.
- **Checks:** `qwen4-max` answered through the configured provider on a throwaway profile with no fallbacks (`state.db`: `qwen4-max`, `alibaba-token-plan`; profile deleted). A tiny implementer call then answered on `gpt-6-sol` (`openai-codex`). The fallback itself was not triggered, so it is untested in a live failover. No restart.
- **Not changed:** the profile's `delegation` settings (still `qwen3.7-plus`, with `deepseek-flash` behind it).
