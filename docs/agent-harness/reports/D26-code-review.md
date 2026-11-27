# D26 code review (`agent-harness` branch `d26-jobs` @ `b9d4518`)

**Not approved yet: four changes first. The design is right and the code is careful; these are gaps between
jobs, and one way a secret could be published.** Nothing is to be merged, deployed or set up from `b9d4518`.

## What I verified
- Fresh worktree at `b9d4518`: `747 passed, 3 skipped in 92.71s` (with `ssh-keygen` present, so the signing
  tests ran, not skipped); `ruff check` and `ruff format --check` clean. Diff against `5b6c863`: 20 files,
  1,763 lines, all under `jobs/`, `proof/`, `systemd/`, the three new modules, and small hooks in
  `decisions.py`, `reviewer.py`, `harness.host.toml`, `tests/test_isolation.py`.
- **The signature check works on the real branch.** With the key line of setup step 6, `why_not_signed` passes
  all 13 decision files on this branch, and refuses `STATE.md`, `reports/D26-jobs.md` and `runs/FXL-18.md` (no
  SSH signature), as it should.
- **I broke 26 guards by hand, one at a time; `tests/test_d26.py` caught 22.** The four it did not catch are
  doubled guards, not gaps: the launcher's two ledger checks cover each other (with both off, a test fails);
  the two extra checks in `why_not_signed` (same content as the head; differs from every parent) follow from
  what `rev-list -1 -- <path>` returns, so nothing can reach them. Keep them; no test needed.
- Read in full: `signing.py`, `jobs.py`, `proofrun.py`, `dispatch.py`, `run-job`, the settings, the prompt and
  the units. The outbox reader (no link followed, one name, one owner, size and count caps, read only after the
  job ended), the ledger written before the run, and the proof container's flags (no network, read-only, no
  capabilities, no writable mount, sha taken from a file name) are as reported.

## Required before I approve
**R1. `~/.local/bin` must not be on the job's `PATH`.** The unit puts `/home/harness-job/.local/bin` first, and
the job can write there. `run-job` then finds `claude`, `git`, `sed` and `head` through it, so one job can
replace the program every later job runs. Use `/usr/local/bin:/usr/bin:/bin`.

**R2. Nothing a job writes may be run, or read as instructions, by a later job.** Today the whole home is
writable and shared: `~/.gitconfig` and `~/.config/git` (read by `run-job`'s own `git clone`), `~/.ssh/config`,
`~/.claude/` (a `CLAUDE.md` there may be read by the next session; `--setting-sources ""` is about settings),
shell start-up files, the `uv` cache. Make it so by construction, not by a list:
- the unit's `ReadWritePaths` names `/home/harness-job/jobs`, not the home;
- `run-job` sets `HOME` to a fresh folder inside this job's folder, so the CLI's state, caches and git's
  per-user config start empty each time;
- the git identity comes from a root-owned file (`GIT_CONFIG_GLOBAL`), and SSH keeps reading the real
  `~/.ssh`, which the job can then no longer write.
Test what can be tested with the stand-in `claude` (a file planted by "job 1" in the old home, in its own
`HOME` and on the old `PATH` is not seen by "job 2"). Whether the real CLI starts with an empty `HOME` and only
the token cannot be tried before Ubay's setup: say so, and make the first job the proof.

**R3. A job must not be able to prepare another job's folders.** The outbox is writable by every job, so job A
can make `outbox/<a later id>/` with files in it. Job B then fails at its first `mkdir`, and the runner
publishes A's files as B's reports, because it reads the outbox for every ended job. The same holds for
`~/jobs/<a later id>`. So: the launcher (root) refuses a job whose outbox folder or work folder already exists
and records `refused`; and the runner publishes no report for a job that was `refused` or never started.

**R4. A report that holds a credential is not published.** The job has the Claude token in its environment and
can read the deploy key; a report goes to GitHub. Refuse a report that contains `sk-ant-` or
`PRIVATE KEY-----`, and say which file, never the match. Add `Bash(env*)` and `Bash(printenv*)` to the deny
list as well (a guard against mistakes, like the rest of that list).

## In the setup notes
- Step 9's probe: add, inside the same `systemd-run` line, `crontab -l` and `echo true | at now`, which must
  both fail (with `NoNewPrivileges` they should), so a job cannot leave something that runs after it. After R2,
  add `touch /home/harness-job/.probe`, which must fail too.
- After R2, step 1 makes `/home/harness-job/jobs` owned by the job user; say so.

## Next change, not blocking
- `run-job` checks the id with the launcher's full pattern, not `J-????????-*`.
- Old proof results and requests are never removed, and a job can ask for any number of runs.
- `BRANCH` is fixed in the root-owned `jobs.env`: a new review branch needs Ubay. Say it in `HANDOFF.md`.

## Your open points
- Report names and the "For HANDOFF.md" section: agreed (`D26-cloud-review.md`). I apply that section myself
  when I review the job's report; the runner does not.
- The limits you list under "What this does not protect against" are accepted as stated. Items 2 and 6 are
  Ubay's to know; I will tell him in plain words when I send him the setup.

Send the new commit with the same proof-container run. I review only the difference from `b9d4518`.
