# D26 second review (`d26-jobs` @ `25a315e`): approved

**Approved. Fast-forward `master` to `25a315e398522e0cf4b89fe51b6b70c2685b3a28`.** Verified on a fresh worktree
at that commit: `762 passed, 3 skipped in 85.27s`, signing tests run with a real `ssh-keygen`; `ruff check` and
`ruff format --check` clean. The difference from `b9d4518` is 7 files, 315 lines added.

- **R1 to R4 are done as asked.** I broke 11 of the new guards by hand, one at a time; the tests caught 10:
  the job-writable folder back on `PATH`, the whole home writable again, the shared `HOME` kept, git reading
  the per-user config, prepared folders not refused, the outbox not sealed, reports read for a refused job,
  reports read from the unsealed outbox, a credential published, only one of the two marks checked. The one not
  caught (`seal` without its "target exists" check) cannot be reached: no job can make anything in `sealed/`,
  and a job whose sealed folder exists is refused before it runs.
- **Your extra, the sealed outbox, is right** and closes a gap I missed: job B rewriting job A's reports before
  the runner reads them. Private IPC and a private `/dev/shm`: agreed.

## One change to the setup notes (no code change)
**Step 7, `sealed`: make it `root:ubay`, mode `750`, not `root:root 755`.** A sealed folder keeps the job
user as its owner, so today only the unit's read-only file system stops a job writing into it. With `750` the
job user cannot enter `sealed/` at all, the runner still reads it through its group, and the launcher still
moves folders in as root. Add to the step 9 probe: `ls /var/lib/harness-jobs/sealed`, which must fail.

## Deploy (Ubay runs this; the board is idle and nothing is loaded)
```
harness-deploy 25a315e398522e0cf4b89fe51b6b70c2685b3a28
```
The previous version is `5b6c863`. The deploy alone switches nothing on: jobs and the proof runner wait for
the folders of step 7, signing for the file of step 6.

## After the deploy, read-only, before Ubay starts the setup
1. The usual: host and container copies identical, fresh-process imports, `--help` of every tool.
2. Two runner passes with no "jobs skipped" or "decisions skipped" line.
3. I will push a decision that must be refused (`D-20261127-13`, a load of a ticket already loaded). Its PR
   comment must now end with the commit, the time and `signature: present, not checked (no key list)`. Report
   the comment verbatim. After step 6 of the setup I send one more, which must say `by a listed key`.

## The first job
After Ubay reports the setup done and the step 9 checks, I write `jobs/J-<date>-1.md`: read three files and
write a report, nothing else. It is the proof that the CLI starts with an empty home and only the token. The
second job is a small kit change on a branch, with a proof-runner request. The standing session stays until
both have run to the end.

## Next change, not blocking (unchanged from the first review)
The id pattern in `run-job`; cleaning old proof requests and results; `BRANCH` fixed in the root-owned
`jobs.env`. New: if `seal` ever fails, the launcher stops at that job on every pass and starts no other; it
should record the job as `interrupted` with the reason and go on.
