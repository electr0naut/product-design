# D7 ready for the morning: master = `666cb30`, the exact lines for the user

Both D7 review changes are in and tested. Kit `master` was fast-forwarded from `c6451f5` to **`666cb3029b740cfa07760454fe05cf002628b165`** (`git ls-remote` confirmed; also pushed on branch `d7-fix-budget`). Fresh clone of `master`: `294 passed, 3 skipped`, `ruff check` and `ruff format --check` clean.

## The two changes
1. **`base` is a required keyword argument of `request_fix`** (no default; a caller that forgets it raises `TypeError` instead of matching no base). A test checks the signature and the error. Both real callers (the gatekeeper and the reviewer) already pass it.
2. **One-off migration of pre-D7 ledger entries** (`tools/migrate_fix_ledger.py`, `fixloop.migrate_legacy_bases`): for every entry without `base` it sets `base = merge-base(entry.head, trusted main)`, computed in the host-only trusted repo with the hardened git flags; the repository is found from the run folder's `repo.txt` only through the runner's own validation (an allowed repository); an entry it cannot resolve (unknown head, no trusted repo, bad `repo.txt`) is left as it is and keeps counting against every base; the new ledger is written atomically after a copy is saved as `~/.local/state/agent-harness/fix-ledger.json.bak`; a corrupt ledger stops it untouched; a second run changes nothing. 5 tests: right base plus the backup and idempotence; unresolvable entries left alone with no backup; already-migrated entries untouched and `--dry-run` writes nothing; a corrupt ledger; and a migrated entry stops counting against a newer base (while the original attempt still counts). For FXL-1 the expected base is `544c8c5` (its merge-base with the trusted `main`).

## The lines for the user, in this order (nothing is deployed yet)
1. **Host kit** (same shape as last night; undo: the same line with `c6451f50cc985c100a6c5859507a42c6e1eb6a3a`):
```
! cd ~/dev/agent-harness && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/deploy_host_kit.py 666cb3029b740cfa07760454fe05cf002628b165
```
2. **The container's copy** (bundle-and-fetch; the plain fetch worked last night; if root cannot reach GitHub, make a bundle first with `git -C ~/dev/agent-harness-d7 bundle create /tmp/kit.bundle c6451f5..666cb30` and replace `origin` below by `/tmp/kit.bundle` with the refspec `master:refs/remotes/origin/master`). Undo: `sudo git -C /srv/lab/agent-harness reset --hard c6451f5`:
```
sudo git -C /srv/lab/agent-harness fetch -q origin && sudo git -C /srv/lab/agent-harness merge --ff-only origin/master
```
3. **The migration** (look first, then do it; run from the host kit after step 1; undo: copy `fix-ledger.json.bak` back):
```
! cd ~/.local/share/agent-harness/kit && PYTHONPATH=src .venv/bin/python tools/migrate_fix_ledger.py --dry-run
! cd ~/.local/share/agent-harness/kit && PYTHONPATH=src .venv/bin/python tools/migrate_fix_ledger.py
```
Then, as `FXL-1-review.md` says: I archive FXL-1's cards and reload FXL-1 alone (the loader finds its blockers on the board), with the FXL-3 situation decided first (see `FXL-3-investigation.md`: the planner block is a card-text/write-root problem, not a ticket problem, and FXL-1's rerun needs the same fix or it can hit the same wall).
