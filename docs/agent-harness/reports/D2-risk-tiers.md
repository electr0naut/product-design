# D2: risk tiers (`agent-harness@eb42595`, off by default)

Kit `master` = `eb42595` (`git ls-remote` confirmed). Fresh clone of that commit: `186 passed`, `ruff check` clean, `ruff format --check` clean. Container: `186 passed`.

## First commit of D2: the two D1.1 fixes (`12598e8`)
1. **Stored proofs are written without following symlinks.** New `write_nofollow(root, rel, text)` (the same component-by-component `O_NOFOLLOW` walk as `copy_nofollow`) is what `recheck_stored_proofs` uses; an `OSError` becomes `StillBroken` ("could not write it safely"), a `needs_input` block. Tests: a branch whose `tests` is a symlink out of the worktree (with the path check patched to pass, i.e. the swap happens after the check) blocks and the outside folder stays empty; `write_nofollow` refuses a symlinked directory and a symlinked file name.
2. **Validate before the ledger.** `request_fix` now runs `check_proofs` (every proven finding has file, id and source; at least one proven finding) **before** the ledger entry; a refusal logs, returns False and the card blocks as today. Test: a missing source writes no ledger entry and creates no cards, and an empty `proven` list is refused too.
3. **Cleanup:** the 27 SEED-A, SEED-C and SEED-D cards are archived (0 seed cards left on the board).

## D2: how the tier is chosen (`src/harness/risk.py`)
Inputs the container cannot influence: the paths the branch changed (read from the host-only trusted repo) and the ticket's labels (recorded by the loader in `~/.local/state/agent-harness/labels.json`, merged across loads, never read from `work/runs`).
- **high:** any changed path matches a high-risk glob, or the ticket has a high-risk label. Always the full review. Defaults, in every project and not droppable by config: `package.json`, `package-lock.json`, `vitest.config.*`, `conftest.py`, `pyproject.toml`; `[risk] high_risk_globs` extends them. A pattern without `/` matches the file name at any depth; one with `/` matches the whole path.
- **low:** no high-risk path, and either every changed path is in `[risk] low_risk_globs` (default `docs/*`, `*.md`) or the ticket has a low-risk label. The Claude refuter is skipped, **only when the finder's kept findings contain nothing at critical or high**; any critical or high finding gets the full path (refuter, prover).
- **standard:** everything else. Full review, as today.
- Missing labels never lower a tier (`low` needs positive evidence); an empty diff is standard; a low label never beats a high-risk path; a corrupt label store fails closed (the card blocks `transient`).
- `review.json` now has `risk: {tier, reason, refuter_skipped}`.

**Off by default:** `[risk] enabled = false` in `harness.host.toml` and `harness.toml`. While off, the tier is still reported but nothing is skipped, so a deployed kit reviews exactly as before. Config also sets `high_risk_labels = ["security","payments","migration"]` and `low_risk_labels = ["docs","chore"]`. Note that `decide` already files every medium finding as a note whatever the refuter says, so the only thing the low tier saves is the refuter's Claude calls on medium-only reviews.

## Tests (`tests/test_risk.py`, 24)
Each tier: the five default config files are high (including nested `web/package.json`, `tests/conftest.py`); project globs extend and cannot drop the defaults; slash patterns match whole paths; a high label makes docs high; low needs docs-only paths or a low label; a low label never beats a high path. Through the real `review()` with a counting fake Claude: **low + medium-only finding: 0 refuter calls, 0 prover calls, finding is a note**; low + a high finding: refuter and prover run, finding blocks; standard + medium: refuter runs; high glob (also matching a low glob): full review; high label from host state forces the full review; low label from host state lowers it; **a label in the run folder is ignored**; tiers off by default: a low change is still fully reviewed. Label store merges across loads and lives outside the kit; corrupt store fails closed.

## Not exercised
No live review ran with `enabled = true`. The fixture repos have no docs-only tickets.

## Questions for the reviewer
1. **Switch-on (live, reversible, one flag):** set `[risk] enabled = true` in `harness.host.toml` (undo: `false`; the timer re-reads it, no restart). OK to turn it on and run one docs-only fixture ticket plus one touching `package.json`?
2. Should `tests/*` count as low-risk by default? I left it out (a test change can change what "pass" means); it only matters for tickets that change tests alone.

## Next
D3 (mutation testing on changed lines, report-only), after this is approved.
