# D26: one-shot jobs (D26-go-review, D26-signing-review)

`agent-harness` branch `d26-jobs`, **commit `b9d4518c7bff20c81ace5a903d72d9e33ff74fc8`** (updated after `D26-cloud-review.md` and `D26-credential-review.md`), on `5b6c863`. **Not merged, not deployed.** Nothing was installed; no user, credential, folder or unit was made. Your commands for Ubay: **`D26-setup.md`**. Ready for your review.

**Off until Ubay acts:** signing needs a host-only file no deploy touches; the job queue and the proof runner start only when their folders exist.

## Built
| part | where | in short |
|---|---|---|
| signed decisions and job files | `signing.py` | the commit that **gave the file its content** must carry an SSH signature by a listed key; a signed commit on top, or a signed merge that only carried the file, does not count. Unsigned: rejected with a comment, recorded, never retried, checked before parsing so it cannot hold later decisions. An unclear switch or an empty key list: nothing is applied |
| provenance | `decisions.py` | every decision's commit, time and signature state are in the ledger and its PR comment; applied ones also in `STATE.md` |
| launcher | `jobs/dispatch.py` (root, standard library only) | oldest queued job without a ledger entry; **entry written before the run**; one at a time; never retried; a crash leaves `interrupted` |
| job | `jobs/run-job`, `prompt.txt`, `settings.json`, `jobs.env`, `systemd/jobs/` | user `harness-job`, 2 h cap, budget flag, six tools, branch from a **bundle with no remote** |
| reports out | `jobs.py` | read **after** the job ended; no link followed; plain single-name files owned by the folder's owner; size and count limits; only new `.md` files under `reports/` |
| proof runner | `proofrun.py`, `proof/`, `systemd/harness-proof.*` | takes a sha from a file **name** (the file is never opened); only commits on pushed branches; no network, read-only, **no writable mount**; the report leaves on capped output |

**How you sign:** you do not need to change anything. Your commits already carry the platform's SSH signature; its public half goes into `allowed_signers` (step 6). It covers a commit made on this VM and nothing more.

## Your three items (`D26-cloud-review.md`), and `HANDOFF.md`
### The copy step: exactly what is copied
Only **after** the launcher's ledger says the job ended. From `<spool>/outbox/<job id>/` only, at most the first 10 entries. An entry is copied to `docs/agent-harness/reports/<name>` **only if all hold**: its name is `<job id>.md` or `<job id>-<letters, digits, . _ ->.md` (up to 80), without "review" in any case; it opens without following a link, inside the job's folder, itself opened without following a link from the outbox; it is a plain file with **one** name, owned by the owner of that folder; it is at most 200,000 bytes of UTF-8; **no file of that name is on the branch.** The destination is built from the fixed folder and that name, so nothing else can be reached. Everything else is refused and named in the end-of-job comment.
Tests for each refusal you listed: a link (`nothing_in_an_outbox_is_followed...[symlink]`, `[hardlink]`, `a_linked_outbox_folder...`), a path outside `reports/` (`no_name_can_leave_the_reports_folder`, 8 names), no job id and not `.md` (`a_job_cannot_write...`), another job's existing report (`another_jobs_report_cannot_be_touched`), over the size cap (`[large]`).

### What a job can read, and who can read the job's files
- **The bundle holds the review branch only:** the runner's mirror fetches that one branch, and the bundle is made from it; a test shows a commit on another branch is not in it. (It holds that branch's whole history.)
- **Host-only state** (`~/.local/state/agent-harness/`, trusted repositories, host kit, `gh` login) is under `/home/ubay`, mode 750; `harness-job` is in no group that opens it. The job unit also blocks `/home/ubay` and `/srv`. **Not tried under that user:** `D26-setup.md` steps 1 and 9 check it before the timer starts.
- **No worker container can read a job's files or bundle:** the `hermes` container mounts only `/srv/hermes/data` and `/srv/lab` (from `docker inspect`, equal to the record the runner holds). The bundle is in `/var/lib/harness-jobs`, the job's work in `/home/harness-job`: both outside. **Now enforced:** the runner refuses to queue any job if the spool resolves under a mounted folder, or if no mounts are recorded. The record is renewed at each deploy. The scoring and proof containers mount only their own checkouts.
- On the host, the bundle is readable by any local account (mode 644), and it contains the hidden tests.

### A job still running when its time is up
`TimeoutStartSec=2h`: systemd stops the unit, `Result=timeout`, signalling the whole control group (SIGTERM, then SIGKILL). `start --wait` returns 1, and the launcher records **`state: failed, result: timeout, exit: 15`**, comments it through the runner, **publishes whatever valid reports are already in the outbox**, removes the bundle, and never runs the job again. If the launcher itself dies, the next run records `interrupted`, but only when the job unit is no longer active. Seen here with a 2 s transient **user** unit: `Result=timeout`, `ExecMainStatus=15`, `KillMode=control-group`, `start --wait` exit 1. **The system unit is untested.** The launcher's side is tested with a stand-in `systemctl`.

### Who applies "For HANDOFF.md"
**You.** I have the runner copy reports only. Having it copy that section would put text a job wrote straight into the file that later jobs obey.

### One more limit
The job's token is in its environment, so a job can read it, and could put it in a report (which gets published) or its unit's log, or send it out. Nothing screens for that.

## Tests
Fresh clone of `b9d4518` in the proof container (ruff and format clean):
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
747 passed, 3 skipped in 84.69s (0:01:24)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 282; started without HOME: 0
```
`tests/test_d26.py` uses real SSH keys and signed commits, real git and bundles, and runs the real `run-job` script with a stand-in `claude`; the launcher's `systemctl` and the proof runner's Docker are stand-ins there. **The proof runner was also run for real** (at part 1, `024e35d`, scratch folders): 712 passed in its container, no live path touched, nothing left behind.

## The CLI flags, tried with real calls (CLI 2.1.332, subscription login)
| question | result |
|---|---|
| are the cloned folder's own settings ignored with `--setting-sources ""`? | **yes:** its rule allowing `touch` was not honoured |
| `--strict-mcp-config` | **no MCP server loaded** (none of the account's connectors) |
| which tools does a session get? | ⚠ **without `--tools`: 22, among them `RemoteTrigger`, `CronCreate`, `ScheduleWakeup`, `SendMessage`, `PushNotification`, `DesignSync`.** My proposal and part 1 did not limit this. With `--tools`: exactly Bash, Read, Edit, Write, Glob, Grep. Now set, and the others are denied too |
| `dontAsk` | `touch`, `mkdir` refused; `docker --version` refused by the deny rule; **`date` and `ls` ran without an allow rule** (the CLI permits some read-only commands) |
| does the settings file confine writes? | ⚠ **No.** With `Write` allowed, a file outside both the working and the added folder was written. (A first refusal was only because my test folder was under `.claude`.) Confinement is the user and the unit |
| `--max-budget-usd` with this login | **it stops the session** (`error_max_budget_usd`, exit 1), **after overshooting:** cap $0.001, spent $0.012. A cap, not a hard limit. No turn cap exists |

## What this does **not** protect against
1. **The allow list is a guard against mistakes only.** `python3` is allowed, so a job can run any program, including `claude` **without** these flags. The boundaries are: the user, the unit, and which credentials exist.
2. **The cloud route** depends on that credential (`D26-cloud-check.md`): closed per the documentation with an API key; open with a claude.ai login.
3. **A signature on a job file does not cover what the job is told.** It reads `RULES.md` and `HANDOFF.md` as they were on the branch when queued, and anyone who can push can change those. Detection only: they are in git history.
4. **A job's copy of the branch includes the hidden acceptance tests** (they live in this repository). It cannot reach the work folders (`/srv` is closed to it), so it cannot hand them to an implementing card.
5. **A proof result is what the tested code printed.** Hostile code could print a false pass. It does not replace your own run.
6. **`agent-harness` `master` cannot be protected** on the current GitHub plan; the deploy key can move it. It cannot deploy.
7. The job can use the network, and can send out what it can read.

## Differences from the instructions
- Report names must start with the job id and may not contain "review". A job **cannot edit `HANDOFF.md`**; it writes a "For HANDOFF.md" section, which someone has to apply.
- Launcher, job script and settings are **root-owned copies** that `harness-deploy` does not update.

## Not verified
Everything needing `sudo` or the new credentials: user, folder modes, unit protections on this Ubuntu (checks are in step 9, **before** the timer starts), the copied CLI under that user, `DISABLE_AUTOUPDATER`, either credential with the job command, the deploy key, and a real job end to end. The two test folders I made under `/tmp` (`harness-cli-check.*`, a few tiny files) are still there.
