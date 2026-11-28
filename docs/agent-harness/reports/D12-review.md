# D12: one-line deploy (instruction; build between tickets, branch only)

The user approved a single command for future deploys. Goal: each harness deploy is one line,
`harness-deploy <40-hex sha>`, with one `sudo` prompt, and nothing else to paste.

## Build `tools/deploy.py`, plus a wrapper

`harness-deploy SHA [--dry-run]` does, in order, stopping at the first failure with a clear message:
1. **Check the sha.** Refuse anything that isn't 40 lowercase hex characters. Run `sudo -v` once, up front, so
   there's one password prompt.
2. **Fetch.** `git fetch` in the dev clone (`~/dev/agent-harness`, or `--clone PATH`). The sha must exist there.
3. **The host kit:** the existing `deploy_host_kit` logic at that sha. The unit is unchanged unless
   `--install-unit` is given.
4. **The container's copy.** Bundle the sha from the clone, then `sudo git -C /srv/lab/agent-harness` with
   `core.hooksPath=/dev/null` and `core.fsmonitor=false`. Fetch the bundle, `merge --ff-only`, then check `HEAD`
   equals the sha. Not a fast-forward means refuse, with no reset.
5. **The alert script:** only if `tools/harness_notify.py` differs between the old and the new container `HEAD`.
   Make a timestamped backup in the container, `docker cp`, and `chown` it to `hermes`.
6. **Print one summary line:** host kit sha, container sha, and whether the alert script changed. Also print
   the undo command: the same command with the previous sha. Fast-forward only means the undo is a recorded
   reset, so print the exact `reset --hard` line for the container copy and say it needs `sudo`.

`--dry-run` prints every step and runs none of them.

**The wrapper:** `~/.local/bin/harness-deploy`, which runs the **host kit's** `tools/deploy.py`. It's installed
once, by the first deploy that includes D12 (`--install-wrapper`). Never run it from `/srv/lab`.

## Tests
- A bad sha is refused before any command runs.
- A non-fast-forward is refused, and the container copy is untouched.
- The alert script is copied only when it changed.
- `--dry-run` runs nothing.

Use fake `git`, `sudo` and `docker` commands injected as arguments, not by patching code we own.

## Timing
Build it now, on a branch. Deploy it **between tickets**, after one of them lands. The first D12 deploy is the
last multi-line paste: I'll give the user one line that runs `tools/deploy.py` from the dev clone with
`--install-wrapper`. After that, every deploy is `harness-deploy <sha>`.

Report as `D12-deploy.md`.
