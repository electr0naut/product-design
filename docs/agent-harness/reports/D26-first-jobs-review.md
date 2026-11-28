# D26: the first two jobs ran. The unit holds. A third job tries a real kit change

## J-20261127-1 (17:59, 40 s): the path works, the probe did not run
Queued from my signed file, started by the launcher, CLI up with an empty home and only the token, files read
from the bundle, report published by the runner. It put the probe and three other commands into one Bash call;
that call was refused; **it stopped and said so**, as the prompt tells it to. Lesson for job files, not for the
kit: one command per call, and the list of allowed commands, in every job file.

## J-20261127-2 (18:01, about a minute): the probe ran, **every line as expected**
From inside the real unit (`reports/J-20261127-2.md`): the real home and `~/.ssh` are read-only; the job's own
`HOME` and outbox are writable; `/home/ubay`, `/srv` and `sealed/` are closed; the ledger, the queue, the
launcher's folder and `/usr/local/bin` are read-only; the Docker socket refuses; `sudo` is stopped by "no new
privileges"; `crontab -l` gets a permission error; git's name is `harness-job`; the clone has no remote; the
kit clone is at `6ff69fa`; CLI 2.1.332. `PATH` is `/usr/local/bin:/usr/bin:/bin`.

**One thing I did not expect, and it is good:** inside the Bash tool, `CLAUDE_CODE_OAUTH_TOKEN` is **not set**.
The CLI keeps its token out of the commands it runs. The token is then reachable by a job's command only
through the file (`/etc/harness-job/claude.env`, group-readable by the job user) or the parent process's
`/proc` entry.
- **For `D26-setup.md`, and for Ubay when he is next at a terminal (not urgent):** make the folder and the
  file root-only (`root:root`, `700` and `600`). systemd reads an `EnvironmentFile` as root before it drops to
  the job user, so the unit still gets the token, and a job's `cat` no longer does. Check on a scratch unit
  first that this holds on systemd 255, and tell me. The report guard for `sk-ant-` stays either way.

## J-20261127-3, pushed now: the first real kit change by a job
Four emoji in `tools/harness_notify.py` become plain words, on branch `j3-notify-plain-words`, with a proof
request. It is the first use of the deploy key and of the proof runner by a job. **Standing session: do not
touch that branch or that file until the job has ended;** `tools/harness_notify.py` is outside D27 part 1 as
far as I know. If it is not, say so before the job's branch is reviewed.

Two jobs have now run to the end. The standing session stays until J-3 has pushed a branch and had a proof,
and until D27 part 1, which it is building, is delivered.
