# D26 setup: Ubay ran it. One probe failed. Read-only checks for you, no `sudo`

Ubay ran `D26-setup.md` on 2026-11-27 and pasted the step 9 output. **Eleven results are right. One is wrong:
inside the probe unit, `touch /home/harness-job/.probe` printed no error, so it succeeded.** The same probe made
the outbox read-only (`touch: cannot touch '/var/lib/harness-jobs/outbox/probe': Read-only file system`), so
`ProtectSystem=strict` works in general and not for that home. I told him not to start the timer. I do not know
whether he had already started it. **I queue no job until the home is shown read-only inside the unit.**

His output, for the record: `id` gives `harness-job` and `users` only; `ls /home/ubay`, `ls /srv` and
`ls /var/lib/harness-jobs/sealed` denied; no Docker version printed; `crontab -l`: `crontabs/harness-job/: fopen:
Permission denied`; `at`: not found.

## Find out, without `sudo` and without changing anything
1. **Why the home stayed writable.** `findmnt -T /home/harness-job` and `findmnt -T /var/lib/harness-jobs`
   (is `/home` a mount of its own, and of what kind?), `systemctl --version`, `systemd-detect-virt`, and whether
   this machine is a container. Then say what you think the cause is and how sure you are. If a fix is a
   change to the unit (for example `ProtectHome=read-only` or `ReadOnlyPaths=/home/harness-job` beside the
   `ReadWritePaths` line), propose it with the one probe line Ubay would run to prove it; build nothing yet.
2. **What is switched on:** `systemctl is-enabled` and `is-active` for `harness-job-dispatch.timer`, and for
   your own user's `harness-proof.timer`; whether any `harness-job@` unit has ever run.
3. **What was installed, against the deployed kit:** owners, modes and checksums of the files in
   `/usr/local/lib/harness-jobs/` and of the three units in `/etc/systemd/system/`, compared with `25a315e`;
   owners and modes of every folder of step 7 (`stat` only; do not list `sealed` or the job's home).
4. **Signing:** whether `signing.toml` and `allowed_signers` exist and what `signing.required()` returns. I
   have pushed `D-20261127-14`, a load that must be refused; report its comment verbatim.
5. Anything the runner logged since his setup began: "jobs skipped", "decisions skipped", an alert.

Do not read `/etc/harness-job/claude.env`, the job's `~/.ssh`, or anything else that holds a secret, and do
not run a job or a probe as the job user. Report in `D26-setup-check.md`.
