# D1: bounded automatic fix loop (`agent-harness@60bb2f3`, off by default)

Kit `master` = `60bb2f3` (`git ls-remote` confirmed). From a fresh clone of that commit: `153 passed`, `ruff check` clean, `ruff format --check` clean. In the container: `153 passed`.

## First commit of D1: the D0 review's two items
- **Prover symlink** (`3892b3b`): `deps_dir` is linked only into the **clean** worktree, never the scratch one the Claude prover can write in. Test: `test_dependencies_are_linked_only_into_the_clean_worktree` (scratch has no `node_modules`, clean has one).
- **Read-only shared dependencies:** `chmod -R a-w` on `work/js-deps/node_modules` and `.venv-container`. After it the gates (JS fixture), the prover (seeded bug J1 proven, clean code not), scoring (`9/9`, baseline `7/7`) and the container test suite (142 then) all still ran. **This is a speed bump, not a boundary:** `hermes` in the container and `ubay` on the host are both uid 1000 and `hermes` owns the files, so a worker can `chmod u+w` and write (I checked: the write is denied, and `chmod u+w` by `hermes` succeeds). A real boundary needs root to own the folders (or a read-only bind mount), and `sudo` is not available to me. **Stop for the user:** `sudo chown -R root:root /srv/lab/agent-harness/.venv-container /srv/lab/agent-harness/work/js-deps/node_modules` (undo: `chown -R ubay:ubay`). Meanwhile D1 and the rest carry on.

## D1: how it works (`src/harness/fixloop.py`)
Trigger, only when `[fixloop] enabled = true` **and** `[gatekeeper] host = true` (the retry's gates must run without a model):
- the gatekeeper's gates exit 1 (a real failure; exit 2 / transient errors never retry), or
- the reviewer's decision has **proven** findings (`decision.blocking`). `blocking_unproven` alone never triggers; budget-skipped findings never trigger.

Then, once per ticket:
1. A ledger entry is written **first** to `~/.local/state/agent-harness/fix-ledger.json` (host-only, next to the trusted repos, the container cannot write it; written by the runner, not by hand). A crash while creating cards therefore still uses up the pass.
2. The first run's `gates.json` / `review.json` are kept as `gates-1.json` / `review-1.json`; `fix-1.json` holds the feedback: the failing gate fields, or each proven finding with its failing proof test (id, file and the **source** of the test; the prover now keeps `test_source`, clipped to 20 000 chars; the whole feedback is clipped to 12 000 chars).
3. Three cards are created: `<KEY> · implementer (fix 1)` (parent: the first implementer card), `· gatekeeper (fix 1)`, `· reviewer (fix 1)`, chained. The implementer card says: same branch `harness/<KEY>`, never change `main` or `base.txt`, commit, `checkout --detach`, rewrite `implement.json`, else `kanban_block`.
4. `scribe` is moved: `unlink` old reviewer, `link` new reviewer. The failed card is blocked then archived; for a gate failure the never-run first reviewer card is archived too. A first-pass `done` gatekeeper stays as the record.
5. The retry then runs the normal path: host gates on the new head (base unchanged, so it must still equal the trusted main), then a fresh review. If that fails, `request_fix` finds `passes_used >= max_retries` and the card **blocks exactly as today**. There is no code path for a third attempt.

Config (committed **off**): `[fixloop] enabled = false`, `max_retries = 1` in `harness.host.toml`.

## Board checks I made on the live board (throwaway unassigned cards, all archived afterwards)
`link` / `unlink` / `archive` behave as assumed; the dispatcher promotes a child when its new parent completes. **`block` fails on a card that is not claimed** ("cannot block"); in the real flow the card is always claimed by the runner, and `request_fix` tolerates that failure anyway so it cannot leave a half-created pass. 0 probe cards remain.

## Tests (`tests/test_fixloop.py`, 11, fake board that remembers cards, links and statuses)
- gate failure creates the three cards with the right parents, relinks scribe, archives obsolete cards, writes `fix-1.json`, keeps `gates-1.json`, writes one ledger entry;
- **a second gate failure blocks, creates no cards; asking again 3 times still leaves one ledger entry (never a third pass)**;
- disabled, or a model-run gatekeeper (`host = false`): blocks as today, no ledger;
- ledger path is outside the kit (container-writable) tree;
- a crash while creating cards still uses up the pass;
- proven finding triggers one pass; `fix-1.json` carries the finding and the failing test's source; the first gates result stays;
- **unproven findings (the proof test errors) block with no retry**, no ledger entry, no new cards;
- **a pass after the retry completes the ticket**;
- a second proven finding blocks as today; a card that cannot be blocked does not undo the pass.

## Not exercised
- No live ticket ran with D1 on. The implementer-fix card text has never been followed by a real model.
- Gate failures that the implementer cannot fix by editing only the branch (for example a stale base) simply fail the retry and block.

## Questions for the reviewer
1. **Switch-on (live, reversible):** set `[fixloop] enabled = true` in `harness.host.toml` (no restart, the timer re-reads it). Undo: set it to `false`. OK to turn on and run one fixture ticket seeded to fail? 
2. Do you want the retry's fix attempt to be allowed when `blocking` has both proven and unproven findings (current: yes, only the proven ones are sent; unproven remain blocking in the fresh review)?
3. The `sudo chown` above: please confirm it goes to the user.
