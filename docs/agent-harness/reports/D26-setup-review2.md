# D26 setup: the cause of the writable home, and the fix to build

**Cause, from Ubay's diagnostic run (systemd 255.4):** inside a unit with `ProtectSystem=strict` and
`ReadWritePaths=/home/harness-job/jobs`, `findmnt` shows `/` as `ro,nosuid` and **`/home` as its own mount,
`rw,nosuid`**; `touch /home/harness-job/.probe2` succeeded. `ProtectSystem=strict` leaves `/home`, `/root` and
`/run/user` writable on purpose: those three belong to `ProtectHome=`. My instruction in R2 ("the unit's
`ReadWritePaths` names the jobs folder, not the home") assumed `strict` covered the home. It does not. The
step 9 probe caught it before any job ran.

## Build (a small commit on `master`'s head, for my review)
1. `harness-job@.service`: add `ProtectHome=read-only`. Keep `ReadWritePaths=/home/harness-job/jobs ...` and
   `InaccessiblePaths=-/home/ubay ...` as they are. Correct the comment above them: `strict` does not cover the
   home; `ProtectHome=read-only` does.
2. `tests/test_d26.py`: the unit text must hold `ProtectHome=read-only` (and break it by hand to see the test
   fail).
3. `D26-setup.md`, step 9: add `-p ProtectHome=read-only` to the probe line, and one command that must
   **succeed**: `touch /home/harness-job/jobs/.probe && rm /home/harness-job/jobs/.probe`. Say that after this
   commit is deployed Ubay repeats the unit install line and `daemon-reload`, then the probe.
4. In the same notes, the clean-up Ubay still has to do in the job's home, as one line: the two cloud-check
   folders of step 4b (they are still there), `.probe`, `.probe2`, `.probe3`, and `.claude`, `.claude.json`,
   `.claude.json.lock`, which the login check of step 3 left in the real home.

I have asked Ubay to try the fixed probe line now, without installing anything, so we know it holds on this
machine before he deploys. I have also asked him what step 4b printed: the folders show he ran it, and I do not
have the result yet.

`D-20261127-14` came back `signature: by a listed key`, so step 6 is active. The rest of
`D26-setup-review.md` (what is switched on, what was installed) still stands.
