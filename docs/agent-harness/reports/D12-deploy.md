# D12: one-line deploy (branch `d12-deploy` @ `743819c`, on `master` `0ae59d0`; NOT merged, NOT deployed)

Pushed as a branch only (a fast-forward of `0ae59d0`, checked). From a fresh clone of the branch: `363 passed, 3 skipped`
(`356` before, 7 new tests in `tests/test_deploy.py`), `ruff check` and `ruff format --check` clean. Nothing was run
against the host kit, the container copy or the board; I only ran `--dry-run` once on this machine (it ran no command).

## What `tools/deploy.py` does (`harness-deploy SHA [--dry-run] [--clone PATH] [--install-unit] [--install-wrapper]`)
1. The sha must be 40 lowercase hex characters, or it is refused before any command runs. Then `sudo -v`, once.
2. `git fetch` in the dev clone (default `~/dev/agent-harness`); `cat-file -e` checks the sha exists there.
3. **The container's copy is checked first.** The sha is put on a temporary ref, bundled, and the bundle is fetched into
   `/srv/lab/agent-harness` (`sudo git -c core.hooksPath=/dev/null -c core.fsmonitor=false`). That only adds objects.
   `merge-base --is-ancestor <old HEAD> <sha>` must hold, otherwise the deploy is refused with *"not a fast-forward ...
   nothing was changed (no reset is ever done by this tool)"*. This is one step earlier than your list (the order is 3
   before 4), so a refusal can never leave the host kit moved and the container copy not.
4. The host kit: the existing `deploy_host_kit.deploy` at that sha (the unit only with `--install-unit`; I moved its
   unit writing into `install_unit()` so both tools share it).
5. The container copy: `merge --ff-only <sha>`, then `HEAD` must equal the sha.
6. The alert script: only if `git diff --name-only <old HEAD> <sha> -- tools/harness_notify.py` is non-empty: timestamped
   backup in the container (`harness_notify.py.bak-<time>`), `docker cp` of the host kit's copy, `chown hermes:hermes`.
7. One summary line, then the undo: `harness-deploy <previous host sha>` and the exact
   `sudo git -C /srv/lab/agent-harness reset --hard <previous container sha>` (needs sudo; the tool never runs it).
- `--dry-run` prints every command it would run and runs none (not even `sudo -v` or `git fetch`).
- `--install-wrapper` writes `~/.local/bin/harness-deploy`: `PYTHONPATH=<host kit>/src:<host kit>/tools`, then
  `<host kit>/.venv/bin/python -P <host kit>/tools/deploy.py "$@"`. It refuses a path under `/srv/lab/agent-harness`, and
  keeps an older wrapper as `.bak`. The wrapper always runs the **host kit's** copy.

## Tests (real git repositories in a temp folder, fake `sudo` and `docker` commands passed in as arguments)
- a bad sha (a branch name, upper case, 39 characters, empty, trailing newline) is refused with no command run, not even `sudo -v`;
- a fast-forward moves the host kit, the container copy and `reviewed-sha`, runs `sudo -v` first, and prints both undo lines;
- a non-fast-forward (a commit on another line of history) is refused: container HEAD, host kit HEAD and `reviewed-sha`
  are unchanged, no `reset` is ever called, the file is not in the container's tree;
- a sha the clone doesn't have is refused;
- the alert script is copied only when it changed (and then exactly: backup, `docker cp`, `chown`);
- `--dry-run` runs no `sudo` or `docker`, moves nothing, writes no wrapper, and prints every step;
- the wrapper runs the host kit's file, is executable, is never written under `/srv/lab/agent-harness`.

## Things to know
- If the host kit step fails after the container's objects were fetched, the container's HEAD is still the old one
  (objects only), and so is the rest; running the same command again is safe.
- The first deploy needs the container copy to be a fast-forward of the new sha; that holds for `master` ahead of `0ae59d0`.
- `sudo -v` asks for the password once; the later `sudo` calls in the same run reuse it.

## The first D12 deploy (the last multi-line paste; after your review, between tickets, once `master` is at the reviewed sha)
```
cd ~/dev/agent-harness-d12 && PYTHONPATH=src:tools /srv/lab/agent-harness/.venv/bin/python tools/deploy.py <reviewed sha> --install-wrapper
```
That is one line. After it, every deploy is `harness-deploy <40-hex sha>`.
