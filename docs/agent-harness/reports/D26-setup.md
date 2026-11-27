# D26 setup: what only you can do

**For Ubay. The VM session has not run any of this.** Do it in order, and only **after** the reviewer has approved the D26 commit and you have deployed it with `harness-deploy`. Nothing here is on until you do it. Commands marked **(untested)** could not be tried without `sudo` or without the new credential. If a step fails, stop and tell the reviewer.

First, in your shell: `KIT=~/.local/share/agent-harness/kit`

## 1. The job user (no `sudo`, not in `docker`) (untested)
| command | does | undo |
|---|---|---|
| `sudo adduser --disabled-password --gecos "Harness job" harness-job` | creates the user, with no password login | `sudo deluser --remove-home harness-job` (deletes its home) |
| `sudo chmod 750 /home/harness-job` | keeps other users out of its home | `sudo chmod 755 /home/harness-job` |
| `id harness-job` | **check:** the groups must not include `sudo`, `docker`, `adm`, `lxd` or `ubay` | |
| `sudo install -d -o harness-job -g harness-job -m 750 /home/harness-job/jobs` | the job's work folders, **owned by the job user**: the one part of its home a job can write | `sudo rm -r /home/harness-job/jobs` |

## 2. The programs the job uses (root-owned copies it cannot change) (untested)
First check `ls /usr/local/bin/claude /usr/local/bin/uv`: both should be "No such file". If one exists, stop.
| command | does | undo |
|---|---|---|
| `sudo install -o root -g root -m 755 "$(readlink -f ~/.local/bin/claude)" /usr/local/bin/claude` | the CLI version tested here (2.1.332) | `sudo rm /usr/local/bin/claude` |
| `sudo install -o root -g root -m 755 ~/.local/bin/uv /usr/local/bin/uv` | `uv` | `sudo rm /usr/local/bin/uv` |
| `sudo install -d -o root -g root -m 755 /usr/local/lib/harness-jobs` | the launcher's folder | `sudo rm -r /usr/local/lib/harness-jobs` |
| `sudo install -o root -g root -m 755 $KIT/jobs/dispatch.py $KIT/jobs/run-job /usr/local/lib/harness-jobs/` | launcher and job script | (with the folder) |
| `sudo install -o root -g root -m 644 $KIT/jobs/settings.json $KIT/jobs/prompt.txt $KIT/jobs/jobs.env $KIT/jobs/gitconfig /usr/local/lib/harness-jobs/` | permissions, fixed prompt, the job's git identity, settings (`MAX_BUDGET_USD=5` per job; edit here to change) | (with the folder) |

`harness-deploy` does **not** update these root-owned files. After a reviewed change under `jobs/`, repeat the last two lines.

## 3. The job's Claude credential: **a `setup-token`** (your choice "A", `D26-credential-review.md`)
The job user authenticates with that token and nothing else. **Never run `claude auth login` as `harness-job`.**

**Where to type this:** a fresh terminal of your own (a new SSH login), **not** inside the `tmux` session the VM agent runs in. The value must not reach a repository, a report, a log, a unit file's text or your shell history. (The standing VM session runs as `ubay`, which has `sudo`, so it *could* read the file; it is not to, and it is closed after two jobs.)

| command | does | undo |
|---|---|---|
| `claude setup-token` | run **as yourself**: signs you in through the browser and shows a long-lived token. Copy it; type it into no other command. **(untested** whether it changes anything about your own login) | revoke it in your Claude account, if offered there |
| `sudo install -d -o root -g harness-job -m 750 /etc/harness-job` | a folder only root and the job user can enter | `sudo rm -r /etc/harness-job` |
| `sudo install -o root -g harness-job -m 440 /dev/null /etc/harness-job/claude.env` | an empty file only `harness-job` (and root) can read, and the job cannot change | (with the folder) |

**Write the token with a silent prompt, not an editor** (the editor route lost it without any sign: the file stayed empty). Paste this line as it is, press Enter, **then** paste the token at the prompt and press Enter. Nothing shows as you paste. The token is on no command line and in no history. (Its logic was tried here on a scratch file with a made-up value, without `sudo`; it needs `bash`, not `sh`.)
```
sudo bash -c 'IFS= read -rs -p "Paste the token, then press Enter (nothing will show): " T; echo; T=${T//[[:space:]]/}; if [ -z "$T" ]; then echo "NOTHING ENTERED: the file was not changed"; exit 1; fi; printf "CLAUDE_CODE_OAUTH_TOKEN=%s\n" "$T" > /etc/harness-job/claude.env; echo written'
```
**Check that it is there, without showing it:** `sudo grep -o '^[A-Z_]*=' /etc/harness-job/claude.env` **must print `CLAUDE_CODE_OAUTH_TOKEN=`.** If it prints nothing, the file does not hold it: do not go on. (If `setup-token` showed the token over two screen lines, only the first may have been pasted: widen the terminal. Step 4b's `ready` call catches a cut token.)
Then `clear; tmux clear-history 2>/dev/null` and close that terminal. Undo: `sudo truncate -s 0 /etc/harness-job/claude.env`, and revoke the token.

**Check the login (untested).** The first must say you are not logged in; the second must show `authMethod` `oauth_token`. **`claude.ai` in either is wrong: stop and tell the reviewer.**
```
sudo -u harness-job -H /usr/local/bin/claude auth status
sudo systemd-run --pipe --wait -p User=harness-job -p EnvironmentFile=/etc/harness-job/claude.env -E HOME=/home/harness-job /usr/local/bin/claude auth status
```
**If the second one says `loggedIn: false` / `authMethod: none` (it then exits with status 1), the file did not set the variable.** Check the names only, never the value: `sudo ls -la /etc/harness-job` (there must be only `claude.env`; remove any other file there, such as a `claude.env5~`, and if it held the token revoke that token) and `sudo grep -o '^[A-Z_]*=' /etc/harness-job/claude.env` (it must print exactly `CLAUDE_CODE_OAUTH_TOKEN=`). **`oauth_token` does not show that the token is valid:** any value, even a wrong one, shows it. Step 4b starts by proving it works.

Then do **4**, and then **4b**, which needs both.

## 4. A deploy key for `agent-harness` only (untested)
| command / action | does | undo |
|---|---|---|
| `sudo -u harness-job -H sh -c 'umask 077; mkdir -p ~/.ssh && ssh-keygen -q -t ed25519 -N "" -C harness-job-kit -f ~/.ssh/harness-kit'` | makes the key pair | delete both files |
| `sudo cat /home/harness-job/.ssh/harness-kit.pub` | shows the **public** half | |
| GitHub: `agent-harness` → Settings → Deploy keys → Add; paste it; tick **Allow write access** | the job can push branches to this one repository | delete the key on that page |
| `sudo -u harness-job -H sh -c 'ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts && ssh-keygen -lf ~/.ssh/known_hosts'` | records GitHub's host key. **Check** the fingerprint shown against GitHub's page "GitHub's SSH key fingerprints" before going on | remove `known_hosts` |
| `sudo -u harness-job -H sh -c 'printf "Host github.com\n  IdentityFile ~/.ssh/harness-kit\n  IdentitiesOnly yes\n" >> ~/.ssh/config'` | tells git to use the key | remove those lines |

(The job's git name and address come from the root-owned `gitconfig` of step 2. You set none here. A running job can read `~/.ssh` and cannot change it.)

**No GitHub credential for `product-design`:** the job does not need one and must not get one.

## 4b. Your one check: this token must be **refused** a cloud session (do it once; **untested**, the VM has not run it)
> The first runs tested **a login stored in the check folder, not the token** (the token file was empty, and the first run signed in through the browser: `D26-setup-review3.md`). Nothing is yet known about what a `setup-token` can do.
> ## **IF THE SCREEN OFFERS OR ASKS YOU TO SIGN IN: STOP. DO NOT SIGN IN.** Quit and tell the reviewer. A sign-in stores a full account login, and the check would then test that login instead of the token.
> **The check counts only if no other credential can take part:** a home that has never been used, no stored login in it before or after, and `auth status` **in that very home** showing the token.

First do the log-out and clean-up in "After the home fix". It needs a git clone with a GitHub remote, so that a refusal cannot be about a missing repository. **Run these one at a time; go on only when each shows what is written.**

**1. A never-used home** (must print `unused`; then make it and the clone):
```
sudo test ! -e /home/harness-job/cloud-check-home && echo unused || echo "STOP: it exists"
sudo -u harness-job mkdir /home/harness-job/cloud-check-home
sudo -u harness-job -H git clone -q git@github.com:electr0naut/agent-harness.git /home/harness-job/cloud-check
```
**2. In that very home, the login must be the token.** `auth status` must show `"authMethod": "oauth_token"`, **not** `claude.ai`, and no stored claude.ai login; and the second command must print `no stored login`:
```
sudo systemd-run --pipe --wait -p User=harness-job -p EnvironmentFile=/etc/harness-job/claude.env -E HOME=/home/harness-job/cloud-check-home /usr/local/bin/claude auth status
sudo test -e /home/harness-job/cloud-check-home/.claude/.credentials.json && echo "STOP: a stored login" || echo "no stored login"
```
**3. The token must work at all,** or everything would be refused and the check would "pass" for the wrong reason. This **must answer `ready`** (one tiny model call):
```
sudo systemd-run --pipe --wait -p User=harness-job -p EnvironmentFile=/etc/harness-job/claude.env -p WorkingDirectory=/home/harness-job/cloud-check -E HOME=/home/harness-job/cloud-check-home /usr/local/bin/claude -p --model sonnet --tools "" -- "Reply with the single word ready." < /dev/null
```
**4. The check itself.** (If it first asks whether you trust the folder, say yes: it is that clone. **Any sign-in: stop.**)
```
sudo systemd-run --pty --wait -p User=harness-job -p EnvironmentFile=/etc/harness-job/claude.env -p WorkingDirectory=/home/harness-job/cloud-check -E HOME=/home/harness-job/cloud-check-home /usr/local/bin/claude --cloud "Reply with the single word ready. Change nothing."
```
**5. Afterwards,** run the `no stored login` line of step 2 again. **If it now says a stored login, the result counts for nothing:** log it out (as in "After the home fix") and tell the reviewer.

| what you see | meaning | what to do |
|---|---|---|
| a refusal **about the sign-in**: it needs a claude.ai sign-in, or says to run `claude auth login`, or cloud sessions "aren't available with this ... sign-in" (the exact words for this token are not documented) | **passed** | note the message for the reviewer (it holds no secret; check before pasting) and go on. **Do not run `auth login`**, even though the message may suggest it |
| it **creates a session** (a session id or a claude.ai/code link) | **failed: this token can start cloud sessions** | open the link or claude.ai/code and stop and delete that session; **stop the setup here**, start no timer, tell the reviewer. The fallback is B below, **which is then a new choice of yours**, not covered by "A" |
| any **other** error (repository, GitHub connection, network, unknown option, an organisation policy) | **not shown either way** | stop here and send the reviewer the message |

(It runs with its own empty home folder, as a job does.) When done: `sudo rm -rf /home/harness-job/cloud-check /home/harness-job/cloud-check-home`.

**Fallback B (only on a new choice of yours): a Console API key.** The documentation states it cannot use cloud sessions; it is billed per use. Same file and permissions, with the one line `ANTHROPIC_API_KEY=` followed by the key; remove the `setup-token` line, revoke that token, and repeat the login check (`authMethod` `api_key`).

## 5. Branch protection for `agent-harness` `master`: **not available as things are**
GitHub's API answered: "Upgrade to GitHub Pro or make this repository public to enable this feature." So the deploy key **can push `master`.** What that cannot do: deploy. `harness-deploy` takes one exact commit that you copy from a review, and only fast-forwards. What it could do: move or rewrite `master` and branches. With GitHub Pro you could restrict `master` to yourself; otherwise accept this.

## 6. Switch signed decisions on (before any job runs)
What it covers, and no more: **a commit made on this VM** (a job has no signing key). It does **not** show that the reviewer wrote it: the key is the cloud platform's. With it on, only decision and job files whose commit carries that signature are used; **one you write or edit yourself is refused.**
| command | does | undo |
|---|---|---|
| `printf '%s\n' 'claude-cloud namespaces="git" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKy87HxSEheG8vEPhSs9u2KZCtVErAQfpmprtUJCZ2w7' > ~/.local/share/agent-harness/allowed_signers` | the platform's **public** key, fingerprint `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc` | delete the file |
| `echo 'require_signed = true' > ~/.local/share/agent-harness/signing.toml` | the switch. No deploy touches it | delete the file |

Checked here, read-only: all 13 decision files on the branch verify against exactly this key. **Check afterwards:** the next decision's PR comment ends with `signature: by a listed key`.

## 7. Folders. Making them switches the job queue and the proof runner on (untested)
| command | does |
|---|---|
| `sudo install -d -o root -g root -m 755 /var/lib/harness-jobs /var/lib/harness-jobs/proof /var/lib/harness-jobs/ledger` | the ledger is root's: no job can write it |
| `sudo install -d -o ubay -g ubay -m 755 /var/lib/harness-jobs/queue /var/lib/harness-jobs/proof/results` | written by the harness, read by the job |
| `sudo install -d -o ubay -g harness-job -m 1770 /var/lib/harness-jobs/outbox` | a running job leaves reports here |
| `sudo install -d -o root -g ubay -m 750 /var/lib/harness-jobs/sealed` | the launcher moves an ended job's reports here. **The job user cannot even enter it** (a moved folder is still the job user's, so the mode of `sealed` is what keeps jobs out); the harness reads it through the `ubay` group |
| `sudo install -d -o harness-job -g ubay -m 750 /var/lib/harness-jobs/proof/requests` | the job asks for test runs here |

Undo all: `sudo rm -r /var/lib/harness-jobs` (this also deletes the ledger and any unpublished report).

## 8. The proof runner (as you, no `sudo`) (the runner itself was tried for real; these install lines were not)
| command | does | undo |
|---|---|---|
| `~/.local/bin/uv pip install --target ~/.local/share/agent-harness/proof-site pytest` | `pytest` for the test containers | delete that folder |
| `cp $KIT/systemd/harness-proof.service $KIT/systemd/harness-proof.timer ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now harness-proof.timer` | installs and starts it | `systemctl --user disable --now harness-proof.timer`, then delete the two files |

## After the home fix (`6ff69fa`, once it is approved and deployed)
1. **Stop the job timer** if it is on (do this now, not only after the fix): `sudo systemctl disable --now harness-job-dispatch.timer`
2. **Log out the login the first cloud check stored** (it is a full account login, and a job could read it), then **clean the job's home** of what the first setup run left there (one line each):
```
sudo -u harness-job env HOME=/home/harness-job/cloud-check-home /usr/local/bin/claude auth logout
```
```
sudo rm -rf /home/harness-job/cloud-check /home/harness-job/cloud-check-home /home/harness-job/.probe /home/harness-job/.probe2 /home/harness-job/.probe3 /home/harness-job/.claude /home/harness-job/.claude.json /home/harness-job/.claude.json.lock
```
Removing the folder does not end a login: if you signed in during a check, also sign that session out in your Claude account, and delete any cloud session it created.
3. **Repeat the unit install line of step 9 and `daemon-reload`** (with `KIT` set as at the top), then run all of step 9's checks again. Only then start the timer.
Between 2 and 3 you will need step 4b again (as the reviewer says), which makes new check folders: clean them the same way afterwards. Step 3's login check also writes `.claude` files into the job's real home: remove them with the same line.

## 9. The job units. Check first, then start the timer (untested)
| command | does | undo |
|---|---|---|
| `sudo install -o root -g root -m 644 "$KIT/systemd/jobs/harness-job@.service" $KIT/systemd/jobs/harness-job-dispatch.service $KIT/systemd/jobs/harness-job-dispatch.timer /etc/systemd/system/ && sudo systemctl daemon-reload` | installs the units | remove the three files, `daemon-reload` |

**Checks. Every one of these must FAIL (except `id`):**
```
sudo -u harness-job cat /home/ubay/.local/state/agent-harness/pipeline.json     # Permission denied
sudo -u harness-job docker ps                                                   # permission denied
sudo -u harness-job sudo -n true                                                # not allowed
id harness-job                                                                  # no sudo, docker, ubay
sudo systemd-run --wait --pipe -p User=harness-job -p NoNewPrivileges=yes -p ProtectSystem=strict -p ProtectHome=read-only -p ReadWritePaths=/home/harness-job/jobs -p 'InaccessiblePaths=-/home/ubay -/srv -/run/docker.sock' sh -c 'ls /home/ubay; ls /srv; curl -sS --unix-socket /run/docker.sock http://localhost/version; touch /var/lib/harness-jobs/outbox/probe; touch /home/harness-job/.probe; crontab -l; echo true | at now; ls /var/lib/harness-jobs/sealed'
```
The last one tries the unit's protections on this Ubuntu: **each of the eight commands inside must print an error.**
1. and 2. the blocked paths;
3. must not print Docker's version;
4. and 5. `ProtectSystem` (the outbox) and `ProtectHome` (the home; `ProtectSystem=strict` alone leaves `/home` writable): the job user may normally write both places (step 7; its own home), so only the protections can stop it. The home must be read-only to a job, so that one job cannot leave files that act on the next;
6. `crontab -l` must fail with a **permission** error. **`no crontab for harness-job` counts as NOT failed:** it means cron's store could be reached;
7. `at` must be refused (`command not found` is also fine: then there is nothing to leave a job with). With 6, this shows a job cannot leave something that runs after it;
8. the job user must not be able to look into `sealed/` (step 7).

**If any of the eight succeeds, do not start the timer**, and send the reviewer the output. (If `curl` is missing, say so instead of counting that as a failure.) If `at` did accept the command, remove it with `sudo -u harness-job atrm <number it printed>`.

**One inside the unit that must succeed** (the one part of the home a job may write); it prints `jobs-folder-is-writable`:
```
sudo systemd-run --wait --pipe -p User=harness-job -p NoNewPrivileges=yes -p ProtectSystem=strict -p ProtectHome=read-only -p ReadWritePaths=/home/harness-job/jobs sh -c 'touch /home/harness-job/jobs/.probe && rm /home/harness-job/jobs/.probe && echo jobs-folder-is-writable'
```

**One more that must succeed:** `sudo -u harness-job touch /var/lib/harness-jobs/proof/requests/<full sha of the deployed commit>`, then within a few minutes `cat /var/lib/harness-jobs/proof/results/<sha>.txt` shows the test report.

Then: `sudo systemctl enable --now harness-job-dispatch.timer` (undo: `sudo systemctl disable --now harness-job-dispatch.timer`).

## 10. The first jobs
Ask the reviewer for a first job that only writes a report. **It is also the first proof that the CLI starts with an empty home folder and only the token:** that could not be tried before this setup. If the job fails at its start, tell the reviewer. **The standing VM session stays until two jobs have run to the end.**
**To stop everything at once:** `sudo systemctl disable --now harness-job-dispatch.timer && sudo systemctl stop 'harness-job@*'`.
