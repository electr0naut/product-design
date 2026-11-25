# Phase B6: review variants, with the two B5 security fixes

## Security fixes (agent-harness 28153d3)
- Prove step: Claude has Read/Write/Edit only (no Bash). The proving test runs in the container as `hermes` via `docker exec`, with `--junitxml`. Worktrees for proving live under `work/prove/` so the container can see them.
- Run-folder files are validated before any git command: `repo.txt` must be the fixture or variant repo, `branch.txt` must match `^(harness|variant)/[A-Z0-9-]+$`, `base.txt` must be a 40-hex commit in that repo. Otherwise the card blocks as `needs_input`. New tests cover hostile values (no git command runs). 83 tests pass on host and in container; ruff clean.

## Results (Claude review, one variant at a time)
| Variant | Kind | Result | Cost |
|---|---|---|---|
| B1 | bug | caught, proven in container | $0.350 |
| B2 | bug | caught | $0.325 |
| B3 | bug | caught | $0.308 |
| B4 | bug | caught | $0.320 |
| B5 | bug | caught | $0.322 |
| B6 | bug | caught | $0.317 |
| C1-C4 | clean | no false block | $0 (no findings, Claude not called) |

Proven by a failing test: B1, B2, B4, B6. B3 and B5 were blocking but unproven (the prover could not write a failing test), so they stand as "blocking_unproven".

Recall 6/6 (target >= 5/6). False blocks 0/4 (target 0/4). Total Claude spend about $1.94.
Caveat: the clean variants produced no Qwen findings, so the refute/prove path was only exercised by the bugged ones.
