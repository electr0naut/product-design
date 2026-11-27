# D26 is shown end to end (four jobs, 2026-11-27)

| step | shown by |
|---|---|
| a signed job file is queued, an unsigned one would be refused | J-1 to J-4 queued; decisions `D-…-14` "by a listed key" |
| the launcher starts it as `harness-job`, once | J-1 to J-4, each started and ended once |
| the CLI runs with an empty home and only the token | J-1 |
| the unit's limits hold from inside | J-2, "Differences: none" on 19 probe lines |
| the token is refused a cloud session and answers model requests | Ubay's step 4b, real run |
| a job changes the kit on a branch and pushes it with the deploy key | J-3, `j3-notify-plain-words` @ `dc3b60c` |
| the proof runner tests that commit in its container | requested 18:05, run 18:05:59 to 18:07:24, `763 passed, 3 skipped`, no live path touched |
| a job reads the result | J-4, first call of `wait-proof.py` |
| reports leave only through the sealed outbox and the runner | four reports published by the runner |

The proof runner's `763 passed` is the same count I got on my own worktree for `dc3b60c`.

## What remains open (none blocks using jobs)
- The token file is group-readable by the job user; root-only is better (`D26-first-jobs-review.md`).
- `sleep` in the settings, the wait helper and "one command per call" belong in the kit's root-owned job files.
- A deploy key can move `agent-harness` `master`; only a commit I name in chat is ever deployed.

## The standing session
Its closing condition (two jobs to the end) is met. It stays until it has delivered D27 part 1 (R1 and R2 of
`D27-code-review.md`) and fast-forwarded `master` to `dc3b60c`. After that, kit work goes through job files.
Closing the session is Ubay's to do; I will tell him when.
