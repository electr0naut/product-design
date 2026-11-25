# D5: the host runner runs from a host-only kit (branch `d5-host-kit` @ `441ef62`, NOT merged, NOT deployed)

**Push only, as the D4 review asked.** Branch `d5-host-kit` on `agent-harness` = `441ef62a4b61c6b7881a5994c1acb57ff394ee16` (`git ls-remote` confirmed); `master` is untouched at `47c65fa`. Nothing was deployed, the systemd unit was not touched, no sudo was run. From a fresh clone of the branch: `275 passed, 3 skipped`, `ruff check` and `ruff format --check` clean. The branch is rebased on `master`; its first commit message still says "not pushed, not deployed" (written before the push), which is no longer true of the push but is still true of the deploy.

## The problem (D3.1 review), restated
The host runner imports `src/harness/*.py`, `harness.host.toml` and the schemas from `/srv/lab/agent-harness`, which the container mounts and workers can edit. An implementer could change `reviewer.py` or `gates_cmd` and have it run on the host as `ubay` within a minute. My own failed tick at 23:43 (D5 edits in the live tree) showed the same coupling from the other side.

## What the branch changes
- **`hostkit.py` (new):** `code_root()` is the folder the package was loaded from; `mounts_from_inspect()` reads the bind-mount sources from `docker inspect` output; `check_not_mounted()` refuses any path equal to, or under, a mounted folder (symlinks resolved); `guard()` fails closed: with no recorded mounts the runner does not start; `read_local()`/`reviewed_sha()` read the host-only `~/.local/share/agent-harness/local.toml` and `reviewed-sha`.
- **`reviewer.py`:** `KIT` stays the work folder (`work/`), `CODE_ROOT` is where the code lives. Schemas and per-repo overlays are read from `CODE_ROOT`, never from the work folder; `--config` defaults to `CODE_ROOT/harness.host.toml`. On every start `main()` loads the host-only `local.toml`, runs the guard on the package folder and the config file, **exits 2 with "refuses to start" otherwise**, and prints `harness.reviewer: kit <path> @ <reviewed sha>` on every pass.
- **`tools/deploy_host_kit.py` (new)** and the unit template (below).

## What the deploy tool does, step by step (`python tools/deploy_host_kit.py <40-hex sha> [--install-unit]`)
1. Refuses anything that is not a 40-character lowercase hex sha.
2. Runs `docker inspect hermes` and records the bind-mount sources; **refuses if the destination is under any of them** (before writing anything).
3. First deploy: `git clone <origin> ~/.local/share/agent-harness/kit`; later: `git fetch origin` there. Origin defaults to the `origin` of the kit it runs from.
4. **Refuses a dirty tree** (the host kit must be exactly a reviewed commit).
5. `git checkout --detach <sha>` and verifies `HEAD == sha`.
6. Creates `.venv` there with `uv venv --python 3.14` if missing (the runner is stdlib only).
7. Writes `~/.local/share/agent-harness/local.toml` (`[host] container_mounts = [...]`) and `~/.local/share/agent-harness/reviewed-sha`.
8. With `--install-unit` only: copies the existing user unit to `harness-reviewer.service.bak`, writes the unit below, runs `systemctl --user daemon-reload`. The timer is not touched.
Deploying later reviewed commits is the same command with the new sha. Rolling back is the same command with the old sha, or restoring the `.bak` unit.

## The exact unit it would install (`unit_text()`, identical in meaning to `systemd/harness-reviewer.service`, which uses `%h`)
```
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
`-P` stops Python from putting the working directory on `sys.path`; `PYTHONPATH` names the host kit's `src` only. The current unit (unchanged, still live) runs `/srv/lab/agent-harness/.venv/bin/python -m harness.reviewer` from `/srv/lab/agent-harness`.

## Tests (`tests/test_hostkit.py`, 13 new; branch total 275 passed, 3 skipped)
Mounts are read from `docker inspect` output; a path under a mounted folder (and the mount itself, and a symlink into it) is refused while a host-only path starts; the guard fails closed without recorded mounts and checks the package folder and every config file; **`reviewer.main` returns 2 ("refuses to start") when the kit is under a mounted path or when there is no local config**; schemas come from the code root; an unreadable local config is an error and a missing one is empty; the deploy tool checks out exactly the sha and records it, refuses a bad sha, a dirty tree, a head mismatch and a mounted destination (writing nothing on a refusal); the unit contains no `/srv/lab`. **Marker-edit property test** (asked for): two copies of `src` are built, the "lab" copy gets a marker line appended to `reviewer.py`; run with `python -P` and `PYTHONPATH=<tree>/src` the host copy prints its own root and no marker, and only the edited copy shows `edited-by-a-worker`: the code a runner imports is the tree its `PYTHONPATH` names, so an edit in `/srv/lab` cannot reach a runner started from the host kit. **What I could not do:** the live version of that marker check and the runner's real startup log with the kit path and sha, because they need the deploy; I will add both outputs here once the deploy is approved. `systemctl --user cat harness-reviewer.service` today still shows the old unit.

## The container's copy of the kit (needs sudo: the user's step)
After the deploy, the container's copy (`/srv/lab/agent-harness`) is only used by the gates in the container (the host runner no longer reads it). Make the code read-only to workers, `work/` stays writable:
```
sudo chown -R root:root /srv/lab/agent-harness/src /srv/lab/agent-harness/schemas /srv/lab/agent-harness/eval /srv/lab/agent-harness/tools /srv/lab/agent-harness/template /srv/lab/agent-harness/harness.toml
```
Undo: the same line with `ubay:ubay` instead of `root:root`.
Consequences: (1) I can no longer edit these folders in place; development moves to a clone or worktree outside `/srv/lab` (I already used `~/dev/agent-harness-d5` for the last commit) and every deploy into the container needs `sudo` (for example `sudo git -C /srv/lab/agent-harness checkout --detach <sha>` once `.git` is root-owned too; `.git` is not in the line above, so a worker could still rewrite the container copy's history; say if you want it added). (2) `work/` has the `tools`/`eval` data the loader writes to? No: the loader and the seed tools write only under `work/`, but they import their code from the kit, which stays readable.

## Not done, on purpose
No push to `master`; no deploy; no unit change; no sudo; the loader, score and variant tools still import from `/srv/lab` (operator-run, not host-runner code).

## Questions for the reviewer
1. Is it fine that the host kit's `harness.host.toml` comes from the reviewed commit (not edited in place)? Local per-machine values live only in `local.toml` (mounts), which the deploy rewrites.
2. Should `.git` of the container's kit also be root-owned in the sudo line?
