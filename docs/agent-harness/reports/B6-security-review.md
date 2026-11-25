# Security fix review: `agent-harness@28153d3`

**Approved, with one fail-closed change.** Verified in the reviewing session: `83 passed in 41.13s`, and ruff is
clean.

## What's right

- **Running proofs:** the proving test runs in the container as `hermes`, through `review.prove_cmd` in
  `harness.host.toml` (`docker exec --user hermes --workdir {cwd} hermes .../.venv-container/bin/python -m
  pytest ...`). Worktrees live under `work/prove/`, so the container sees the same paths.
- **Writing proofs:** Claude writes the test with Read, Write and Edit only, and no Bash, so the host never
  executes repository code.
- **Run-folder files:** `read_run_files` validates every file a worker could have written, before any git
  command runs.
  - `repo.txt` must resolve to an allowed repository.
  - The branch must match `(harness|variant)/[A-Z0-9-]+`, which excludes dots and slashes.
  - `base.txt` must be a 40-character hex commit that exists in that repo.
  - A failure raises `RunFileError`, and the card blocks as `needs_input`. There are tests for hostile values.

## Must change (small)

**1. `proof_command` fails open.** If `review.prove_cmd` is missing (another config file, a typo, a future
edit), it falls back to `test_one`, which runs pytest **on the host**. That's exactly what the fix removed.
- **Fix:** raise `HarnessError("review.prove_cmd is not set; refusing to run a proof on the host")` when it's
  missing.
- **Test:** a config without `prove_cmd` makes `prove` fail and runs no command.

## Hardening (do with the change above)

**2. Symlinked repositories.** `work/` is writable from the container. A worker could replace
`work/fixture-repo` with a symlink to a host repository. Because `read_run_files` resolves the allowed paths
too, the symlink's target would then count as "allowed".
- **Fix:** in `read_run_files`, refuse if `kit/work/fixture-repo`, `kit/work/variant-repo` or `default_repo`
  is a symlink: check `Path.is_symlink()` on the unresolved path, before resolving.
- **Test:** a symlinked `fixture-repo` blocks the card.

**3. Known, acceptable residual.** The container can see `work/prove/` while Claude writes the test on the host,
so a worker could tamper with a proof test before it runs. The worst case is a wrong proof *result*, which
blocks a card for a human. It can't execute anything on the host. No change needed; noted.

## Clearance

After items 1 and 2:
- the runner is cleared for the fixture runs and Phase C;
- for any real repository, also review its secrets exposure (diffs go to Qwen and Claude) before the first
  ticket.

## Still open

- The reasons Claude gave for not proving VAR-B3 and VAR-B5 (`could_not_prove_because`), as the B6 review asks.
- The 03:00 backup result from last night.
- Telegram confirmation and the alert-noise choice.
