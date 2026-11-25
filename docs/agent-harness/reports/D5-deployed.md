# D5 deployed and verified; lockdown verified; what is left (needs the user)

Kit `master` = `c6451f5` (`git ls-remote` confirmed), a fast-forward chain: `441ef62` (D5) → `9e27bd5` (D5.1) → `82012ef` (D6 setup) → `c6451f5` (the test-id wording the D6 setup review asked for). Fresh clone of `c6451f5`: `280 passed, 3 skipped`, `ruff check` and `ruff format --check` clean.

## Erratum: my deploy line was wrong the first time
The D5.1 report told the user to run the deploy from `/srv/lab/agent-harness`. That tree was still on the old `master` (I had deliberately not fast-forwarded it), so `tools/deploy_host_kit.py` was not there and the line failed (nothing changed). The user then ran it from my worktree and it worked.

## 1. D5 deploy (run by the user at `441ef62`) and its checks
`systemctl --user cat harness-reviewer.service`:
```
# /home/ubay/.config/systemd/user/harness-reviewer.service
[Unit]
Description=Harness host reviewer runner (one pass)

[Service]
Type=oneshot
Environment=PATH=/home/ubay/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/ubay/.local/share/agent-harness/kit/src
WorkingDirectory=/home/ubay/.local/share/agent-harness/kit
ExecStart=/home/ubay/.local/share/agent-harness/kit/.venv/bin/python -P -m harness.reviewer
TimeoutStartSec=3600
```
`~/.local/share/agent-harness/reviewed-sha` = `441ef62a4b61c6b7881a5994c1acb57ff394ee16`; `local.toml` = `container_mounts = ["/srv/hermes/data", "/srv/lab"]` (from `docker inspect hermes`); the host kit is a clean checkout at `441ef62` (`git status` empty).
The runner's startup log on two passes (the first by my manual `systemctl --user start`, the second by the timer):
```
harness.reviewer: kit /home/ubay/.local/share/agent-harness/kit @ 441ef62a4b61c6b7881a5994c1acb57ff394ee16
idle; idle
```
**Live marker check (as the review specified):** I appended `print("MARKER-D5-LIVE-CHECK: the /srv/lab copy ran")` to `/srv/lab/agent-harness/src/harness/reviewer.py`, ran a pass, and the journal shows the host kit's startup line and `idle; idle` with **0 marker lines**; then `git checkout -- src/harness/reviewer.py` (0 left, `git status` clean apart from the untracked `deps/`). An edit in `/srv/lab` no longer changes what the host runs.

## 2. The user's lockdown, already run, and what it shows
Before I could do my steps (the deps move), the user had run the two `sudo` lines: `/srv/lab/agent-harness`, `src`, `.git`, `deps`, `.venv-container` are `root:root` now, and `work/` is still `ubay`. Verified **as `hermes` in the container**:
- `mv` of `src`, `.venv-container`, `deps`, `schemas`, `eval`, `tools`, `template`, `harness.toml` and `.git`: **each refused**;
- writes: `echo x > src/probe` and `echo x > harness.toml` and `mkdir newtop`: `Permission denied`;
- `work/` is writable (it has to be).
**The one gap, as predicted:** `work/js-deps` still sits in `work/`, which `hermes` owns, so it can be renamed away. The move to `deps/js` needs `sudo` now, because `deps/` became root-owned (the review's order had me do it before the lockdown; the lines were run first). Nothing is running that uses it, but the lockdown is not complete until it moves.
Side effects, as the review said: the linked worktree I used (`~/dev/agent-harness-d5`) pointed at the now root-owned `.git` and git refused it ("dubious ownership"). I replaced it with a standalone clone, `~/dev/agent-harness`, outside `/srv/lab`, and everything since is done from there.

## 3. Pushes done from the clone
`d5.1-lockdown` (`9e27bd5`) and then `d6-fixlens` were fast-forwarded into `master`. **A slip of mine:** my first command chain failed on the commit (the new clone had no git identity) but continued to the pushes, so `master` was briefly at `82012ef`, the D6 branch **without** the wording fix. I then set the clone's identity from the earlier commits, committed the fix and fast-forwarded `master` to `c6451f5`. No force push, no rewritten history; the only effect was a few minutes with the old wording on `master`, which nothing deployed.

## 4. What is left, and why it is the user's (auto mode refused the host redeploy a third time)
In this order:
1. **Move the JS deps and update the container's copy** (both need `sudo`; the container copy still has the old config pointing at `work/js-deps`, so run them back to back):
```
sudo mv /srv/lab/agent-harness/work/js-deps /srv/lab/agent-harness/deps/js && sudo chown root:root /srv/lab/agent-harness/deps/js
sudo git -C /srv/lab/agent-harness fetch -q origin && sudo git -C /srv/lab/agent-harness merge --ff-only origin/master
```
Undo of the move: `sudo mv /srv/lab/agent-harness/deps/js /srv/lab/agent-harness/work/js-deps` (and the merge: `sudo git -C /srv/lab/agent-harness reset --hard 47c65fa`).
2. **Redeploy the host kit at `c6451f5`** (the host runner is still at `441ef62`, which is fine but lacks the FIX Lens overlay and `--hold`):
```
! cd ~/dev/agent-harness && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/deploy_host_kit.py c6451f50cc985c100a6c5859507a42c6e1eb6a3a
```
(no `--install-unit`: the unit does not change). Undo: the same line with `441ef62a4b61c6b7881a5994c1acb57ff394ee16`.
3. Then I verify in the container (as `hermes`): the JS gates, the Stryker run and a proof with the deps at `deps/js`; the container suite from a clone outside `/srv/lab`; `deps/fix-lens` resolves; **`work/js-deps` can no longer be renamed**, because it is gone. Then I load the FIX Lens tickets with `--hold`, verify once more, and release the hold. **Nothing of D6's run has started.**
