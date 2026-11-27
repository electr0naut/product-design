# D26 setup: what only you can do

**For Ubay. The VM session has not run any of this.** Do it in order, and only **after** the reviewer has approved the D26 commit and you have deployed it with `harness-deploy`. Nothing here is on until you do it. Commands marked **(untested)** could not be tried without `sudo` or without the new credential. If a step fails, stop and tell the reviewer.

First, in your shell: `KIT=~/.local/share/agent-harness/kit`

## 1. The job user (no `sudo`, not in `docker`) (untested)
| command | does | undo |
|---|---|---|
| `sudo adduser --disabled-password --gecos "Harness job" harness-job` | creates the user, with no password login | `sudo deluser --remove-home harness-job` (deletes its home) |
| `sudo chmod 750 /home/harness-job` | keeps other users out of its home | `sudo chmod 755 /home/harness-job` |
| `id harness-job` | **check:** the groups must not include `sudo`, `docker`, `adm`, `lxd` or `ubay` | |

## 2. The programs the job uses (root-owned copies it cannot change) (untested)
First check `ls /usr/local/bin/claude /usr/local/bin/uv`: both should be "No such file". If one exists, stop.
| command | does | undo |
|---|---|---|
| `sudo install -o root -g root -m 755 "$(readlink -f ~/.local/bin/claude)" /usr/local/bin/claude` | the CLI version tested here (2.1.332) | `sudo rm /usr/local/bin/claude` |
| `sudo install -o root -g root -m 755 ~/.local/bin/uv /usr/local/bin/uv` | `uv` | `sudo rm /usr/local/bin/uv` |
| `sudo install -d -o root -g root -m 755 /usr/local/lib/harness-jobs` | the launcher's folder | `sudo rm -r /usr/local/lib/harness-jobs` |
| `sudo install -o root -g root -m 755 $KIT/jobs/dispatch.py $KIT/jobs/run-job /usr/local/lib/harness-jobs/` | launcher and job script | (with the folder) |
| `sudo install -o root -g root -m 644 $KIT/jobs/settings.json $KIT/jobs/prompt.txt $KIT/jobs/jobs.env /usr/local/lib/harness-jobs/` | permissions, fixed prompt, settings (`MAX_BUDGET_USD=5` per job; edit here to change) | (with the folder) |

`harness-deploy` does **not** update these root-owned files. After a reviewed change under `jobs/`, repeat the last two lines.

## 3. The job's Claude credential: **your choice first** (see `D26-cloud-check.md`)
- **Recommended: a Console API key.** Per the documentation it cannot use cloud sessions. Billed per use; make a key only for this, and set a spending limit in the Console if it offers one.
- Or a `claude setup-token` token: stays on your subscription; that it cannot start cloud sessions is an inference.
- **Never run `claude auth login` as `harness-job`.**

| command | does | undo |
|---|---|---|
| `sudo install -d -o root -g root -m 700 /etc/harness-job` | a root-only folder | `sudo rm -r /etc/harness-job` |
| `sudo install -o root -g root -m 600 /dev/null /etc/harness-job/claude.env` | an empty root-only file | (with the folder) |
| `sudoedit /etc/harness-job/claude.env` | type **one** line: `ANTHROPIC_API_KEY=` or `CLAUDE_CODE_OAUTH_TOKEN=`, followed by your value. Do not paste it anywhere else | empty the file, and revoke the key where you made it |
| `sudo -u harness-job -H /usr/local/bin/claude auth status` | **check:** no `claude.ai` login (this command does not get the file) | |

**(untested)** whether the job's command works with either credential: only your subscription login was available. The first job will show it.

## 4. A deploy key for `agent-harness` only (untested)
| command / action | does | undo |
|---|---|---|
| `sudo -u harness-job -H sh -c 'umask 077; mkdir -p ~/.ssh && ssh-keygen -q -t ed25519 -N "" -C harness-job-kit -f ~/.ssh/harness-kit'` | makes the key pair | delete both files |
| `sudo cat /home/harness-job/.ssh/harness-kit.pub` | shows the **public** half | |
| GitHub: `agent-harness` → Settings → Deploy keys → Add; paste it; tick **Allow write access** | the job can push branches to this one repository | delete the key on that page |
| `sudo -u harness-job -H sh -c 'ssh-keyscan -t ed25519 github.com >> ~/.ssh/known_hosts && ssh-keygen -lf ~/.ssh/known_hosts'` | records GitHub's host key. **Check** the fingerprint shown against GitHub's page "GitHub's SSH key fingerprints" before going on | remove `known_hosts` |
| `sudo -u harness-job -H sh -c 'printf "Host github.com\n  IdentityFile ~/.ssh/harness-kit\n  IdentitiesOnly yes\n" >> ~/.ssh/config'` | tells git to use the key | remove those lines |
| `sudo -u harness-job -H git config --global user.name harness-job` and `... user.email harness-job@localhost` | the name on its commits | `git config --global --unset ...` |

**No GitHub credential for `product-design`:** the job does not need one and must not get one.

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
| `sudo install -d -o ubay -g harness-job -m 1770 /var/lib/harness-jobs/outbox` | the job leaves reports here |
| `sudo install -d -o harness-job -g ubay -m 750 /var/lib/harness-jobs/proof/requests` | the job asks for test runs here |

Undo all: `sudo rm -r /var/lib/harness-jobs` (this also deletes the ledger and any unpublished report).

## 8. The proof runner (as you, no `sudo`) (the runner itself was tried for real; these install lines were not)
| command | does | undo |
|---|---|---|
| `~/.local/bin/uv pip install --target ~/.local/share/agent-harness/proof-site pytest` | `pytest` for the test containers | delete that folder |
| `cp $KIT/systemd/harness-proof.service $KIT/systemd/harness-proof.timer ~/.config/systemd/user/ && systemctl --user daemon-reload && systemctl --user enable --now harness-proof.timer` | installs and starts it | `systemctl --user disable --now harness-proof.timer`, then delete the two files |

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
sudo systemd-run --wait --pipe -p User=harness-job -p NoNewPrivileges=yes -p ProtectSystem=strict -p 'InaccessiblePaths=-/home/ubay -/srv -/run/docker.sock' sh -c 'ls /home/ubay; ls /srv; curl -sS --unix-socket /run/docker.sock http://localhost/version; touch /var/lib/harness-jobs/outbox/probe'
```
The last one tries the unit's protections on this Ubuntu: **each of the four commands inside must print an error.** The first two test the blocked paths. The third must not print Docker's version. The fourth tests `ProtectSystem`: the job user may normally write that folder (step 7), so only the protection can stop it. **If any of the four succeeds, do not start the timer.** (If `curl` is missing, say so to the reviewer instead of counting that as a failure.)

**One that must succeed:** `sudo -u harness-job touch /var/lib/harness-jobs/proof/requests/<full sha of the deployed commit>`, then within a few minutes `cat /var/lib/harness-jobs/proof/results/<sha>.txt` shows the test report.

Then: `sudo systemctl enable --now harness-job-dispatch.timer` (undo: `sudo systemctl disable --now harness-job-dispatch.timer`).

## 10. The first jobs
Ask the reviewer for a first job that only writes a report. **The standing VM session stays until two jobs have run to the end.**
**To stop everything at once:** `sudo systemctl disable --now harness-job-dispatch.timer && sudo systemctl stop 'harness-job@*'`.
