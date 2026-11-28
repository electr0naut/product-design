# D26 setup: the read-only checks (D26-setup-review). No `sudo`, nothing changed.

## ⚠ Four things for you and Ubay first
1. **The job timer is on.** `systemctl enable --now harness-job-dispatch.timer` ran at **17:40:07**; it is `enabled` and `active`. **Nothing has run:** the queue is empty, the branch has no job file, no `harness-job@` unit appears in systemd or its journal, and the ledger holds only its lock file. To stop it (Ubay): `sudo systemctl disable --now harness-job-dispatch.timer`. I recommend that until the fix is deployed and probed.
2. **At 17:33 the CLI apparently saw no token.** The step-3 check that loads the file (`systemd-run ... EnvironmentFile=/etc/harness-job/claude.env ... claude auth status`, unit `run-u636`) **exited 1.** Tried here with CLI 2.1.332, an empty home and a clean environment: **with no credential** it prints `loggedIn: false`, `authMethod: none` and **exits 1**; **with any value in `CLAUDE_CODE_OAUTH_TOKEN`, even an obviously fake one,** it prints `loggedIn: true`, `oauth_token` and **exits 0.** So the likeliest reading is that the file did not set that variable (empty, another name, or a malformed line). No editor command on the file is logged after 17:32:28. (I have not seen what it printed, and I have not read the file. Note too: **exit 0 does not show that a token is valid.**)
3. **So step 4b very probably proved nothing.** `claude --cloud` ran at 17:36:38 (`run-u637`) and **ended with success after 31 s.** If it had no token, whatever it showed says nothing about what a `setup-token` can do. The journal does not hold its screen output, so **I cannot tell whether it refused, showed a sign-in screen, or created a session.** Ubay should say what he saw, and look at claude.ai/code for a session from that time. **4b has to be repeated after step 3's check shows `oauth_token`.**
4. **There may be a stray file next to the token.** The first edit was logged as `sudo ... /usr/bin/editor -- /etc/harness-job/claude.env5~` (17:32:04), then `.../claude.env` (17:32:28). A file `claude.env5~` may exist. It could hold the token, and a file made that way is likely mode 644 in a folder the job user can enter. I cannot and did not look.

**For Ubay, to check 2 and 4 without showing any value:** `sudo ls -la /etc/harness-job` (names and modes only) and `sudo grep -o '^[A-Z_]*=' /etc/harness-job/claude.env` (**prints only the variable's name**; it should print exactly `CLAUDE_CODE_OAUTH_TOKEN=`). A stray file should be removed, and if it held the token, revoke that token and make a new one.

## 1. Why the home stayed writable
Accepted as settled by `D26-setup-review2.md` (Ubay's runs): inside the unit `/home` is its own mount and stays `rw` under `ProtectSystem=strict`; `ProtectHome=read-only` makes it read-only. What I could see: on the host `/home` is **not** a separate mount (all of `/home`, `/var/lib/harness-jobs` and `/` are the one ext4 volume), so that mount is made by systemd for the unit. systemd 255.4-1ubuntu8.18, Hyper-V virtual machine (`microsoft`), not a container. **This machine's `systemd.exec` manual reads as if `strict` covered it** ("the entire file system hierarchy is mounted read-only, except for ... /dev/, /proc/ and /sys/"). I designed the unit on that reading and listed the unit's protections as untested; the probe caught it.
The unit systemd has loaded now: `ProtectSystem=strict`, `ProtectHome=no`, `ReadOnlyPaths=` empty, `ReadWritePaths=/home/harness-job/jobs` and the two spool folders.

## 2. What is switched on
| | enabled | active |
|---|---|---|
| `harness-job-dispatch.timer` | yes | **yes** |
| `harness-proof.timer` (user `ubay`) | yes | yes |
No `harness-job@` unit has ever run. The proof runner has had **no request** and has no result; its `pytest` folder is there. (So setup's "one that must succeed" proof request has not been made.)

## 3. Installed files against `25a315e`
All **identical** to the deployed kit: `dispatch.py` and `run-job` (755 `root:root`); `settings.json`, `prompt.txt`, `jobs.env`, `gitconfig` (644 `root:root`); no other file in `/usr/local/lib/harness-jobs/` (755 root). The three units in `/etc/systemd/system/` (644 `root:root`): identical, no drop-ins. The two proof user units: identical. `/usr/local/bin/claude` and `uv` (755 root) equal the tested 2.1.332 and `ubay`'s `uv`.
(One install line first ran with `KIT` unset and was rerun with full paths.)

| folder | mode, owner (`stat`) | as in the notes |
|---|---|---|
| `/var/lib/harness-jobs`, `proof`, `ledger` | 755 `root:root` | yes |
| `queue`, `proof/results` | 755 `ubay:ubay` | yes |
| `outbox` | 1770 `ubay:harness-job` | yes |
| `sealed` | 750 `root:ubay` | yes |
| `proof/requests` | 750 `harness-job:ubay` | yes |

## 4. Signing
`signing.toml` and `allowed_signers` exist (both 664 `ubay:ubay`, under `/home/ubay`); `signing.required()` returns `Required(signers=.../allowed_signers)`. `D-20261127-14`, verbatim:
> `rejected D-20261127-14: already loaded, so nothing was loaded: FXL-18 [commit 71ef7a84c595, 2026-11-27T16:41:24+00:00, signature: by a listed key]`

## 5. The runner since setup began
20 passes since 17:23: no "skipped" line of any kind, no error; the only other line is D-14's rejection; the alert unit logged nothing; status `ok`.

**Not read:** the token file, the job's `~/.ssh` or home, `sealed/`. Nothing was run as the job user. How I know what Ubay ran: the system journal's `sudo` and `systemd-run` lines, which hold command lines, not values.
