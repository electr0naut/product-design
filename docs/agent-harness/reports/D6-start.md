# D6 start: deploy confirmed, lockdown verified, FIX Lens tickets loaded behind a hold

Kit `master` = `c6451f5`; the host kit and the container copy are both at that sha (read below).

## Who did what to `work/js-deps`
**The user moved `work/js-deps` to `deps/js` with `sudo`** (and made it root-owned), and also ran the lockdown `sudo` lines and brought the container copy to `master`. **I did not move it:** my own `mv` attempt was denied (`Permission denied`, because the user's lockdown had already made `deps/` root-owned). Evidence on disk now: `deps/js` is `root:root 755`, `deps/js/node_modules` is `root:root 555`, and `work/js-deps` no longer exists (0 entries). I only moved and changed things that stayed in my own folders (`work/`, my clone in `~/dev`).

## Deploy state
- Host kit: `~/.local/share/agent-harness/kit` is a clean checkout at `c6451f5`; `reviewed-sha` = `c6451f50cc985c100a6c5859507a42c6e1eb6a3a`; the runner's log line is `harness.reviewer: kit /home/ubay/.local/share/agent-harness/kit @ c6451f5…` then `idle; idle` (checked at 00:54 on the timer's own tick). The unit is unchanged since D5 (the redeploy was run twice by the user; it is idempotent).
- Container copy (`/srv/lab/agent-harness`): `src`, `schemas`, `eval`, `tools`, `tests`, `template` and the three toml files are **byte-identical to a fresh clone of `master`** (`diff -rq`, `__pycache__` ignored; an old stale `__pycache__` dir under `eval/fixture/hidden` is the only extra). Every top-level entry except `work/` is `root:root` (`find ... ! -name work ! -user root` = 0 entries).

## The lockdown, verified as `hermes` in the container
- `mv` of `src`, `.venv-container`, `deps`, `deps/js`, `deps/fix-lens`, `eval`, `tools`, `harness.toml` and `.git`: **each refused**. A write into `deps/js` and `src` and a new top-level folder: `Permission denied`. `work/` stays writable. `work/js-deps` is gone, so the one gap D5.1 named is closed.
- The kit's whole suite, run as `hermes` against the root-owned container copy with `-p no:cacheprovider`: **`283 passed`** (including the real mutmut and real Stryker tests, which only run there).
- **JS gates with mutation, the exact live command shape** (`harness.gates --config harness.toml --overlay eval/fixture-js/harness.js.toml ...`, deps at `deps/js`): `passed: true`, 4 valid tests, Stryker **11 killed, 5 survived, 0 unrun, 1.9 s**, identical to before the move. (I had to use a scratch clone with only JSN-1's branch and a config copy with `require_trusted_main` off: the live repo's other branches share JSN-1's commit, so the lineage check refused it, and the trusted-main check refused the old base; both refusals are the gates working.)
- **JS prover with deps at `deps/js`:** seeded bug `(True, 'AssertionError: assertion failed')`, clean code `(False, 'test passed')`.
- `deps/fix-lens/node_modules` works: `vitest 5.1.2`, `stryker 10.1.1`, `jsdom` present, root-owned.

## FIX Lens loaded, behind a hold (nothing started)
Loaded from the container copy's loader with `--repo /srv/lab/agent-harness/work/fix-lens --hold "FIX Lens: start after the lockdown is verified"` and the seven tickets copied unchanged. Board: hold card `t_e8d1c378` (`ready`, unassigned: nobody can work it), and for FXL-1 to FXL-7 all six stage cards each, all `todo`. FXL-1's triage waits for the hold card; every later ticket waits for the previous one's scribe plus its `blocked_by` scribes, as before. `work/runs/FXL-<n>/repo.txt` = `work/fix-lens`; `work/fix-lens/node_modules` is the gitignored link to `deps/fix-lens/node_modules` and `git status` in the repo is clean; `~/.local/state/agent-harness/trusted/fix-lens.git` was created by the loader (the trusted `main` is the operator's initial commit `544c8c5`); the label store records `FXL-7: security` (host-only).

## Next
I complete the hold card to start FXL-1. Every stage is live, nothing is played by hand, nothing in `work/fix-lens` is edited by hand. After each ticket completes I write `docs/agent-harness/fix-lens/runs/FXL-<n>.patch` and `FXL-<n>.md` and comment on PR #47. If a ticket blocks for a human, I write the reason and the run summary into its `FXL-<n>.md`, comment, and wait; I do not unblock it myself.
