```
# /home/ubay/.config/systemd/user/harness-reviewer.service
[Unit]
Description=Harness host reviewer runner (one pass)
OnFailure=harness-reviewer-alert.service

[Service]
Type=oneshot
Environment=PATH=/home/ubay/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/ubay/.local/share/agent-harness/kit/src
WorkingDirectory=/home/ubay/.local/share/agent-harness/kit
ExecStart=/home/ubay/.local/share/agent-harness/kit/.venv/bin/python -P -m harness.reviewer
TimeoutStartSec=3600

# /home/ubay/.config/systemd/user/harness-reviewer-alert.service
[Unit]
Description=Harness alert: the host runner failed

[Service]
Type=oneshot
Environment=PATH=/home/ubay/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=/home/ubay/.local/share/agent-harness/kit/src
WorkingDirectory=/home/ubay/.local/share/agent-harness/kit
ExecStart=/home/ubay/.local/share/agent-harness/kit/.venv/bin/python -P -m harness.alert runner
TimeoutStartSec=180
```
`systemctl --user show harness-reviewer.service`: `OnFailure=harness-reviewer-alert.service`, `NeedDaemonReload=no`. The alert unit is `LoadState=loaded`, inactive, and **has never run**. Both run `~/.local/share/agent-harness/kit`, whose HEAD and `reviewed-sha` are `c06cd273c5c47dec63a9c008c4206f9e5c53525f`; the container copy is at `c06cd27` too. The first runner pass on it was at 01:53:34; runner status is ok.

## The undo line
**The `c06cd27` deploy ran twice,** and the output you were given is the second run's.
| time | evidence | run |
|---|---|---|
| 01:52:59 | host kit reflog: `76b094f` to `c06cd27`; sudo log: bundle fetch and `merge --ff-only c06cd27`; runner on `c06cd27` from 01:53:34 | first: deployed it, **without** `--install-unit` (see below) |
| 01:58:44 | sudo log: the same four git steps again; both unit files, the `.bak` and `reviewed-sha` written at 01:58:44 | second, with `--install-unit` |

The units were installed only the second time: `harness-reviewer.service.bak` (the unit as it was just before) has no `OnFailure`, and the new alert unit has no `.bak`. (`76b094f` was also run twice, at 01:38:26 and 01:49:00.)

`tools/deploy.py` reads the "previous" commits from `reviewed-sha` and the container **before** it changes anything, so on the first run it would have named `76b094f`; I do not have that run's output. On the second run the current commit already was `c06cd27`.

**For the next kit change (both are the tool):**
1. A re-run of the same sha must not print that sha as the undo. It should keep the last *different* commit, or say that this run changed nothing and the previous commit is not known from it.
2. **The host half of the undo line cannot work as printed, even with the right sha:** `harness-deploy <older sha>` is refused because it is not a fast-forward of the container copy. From the code, the order has to be the `sudo ... reset --hard <older>` line **first**, then `harness-deploy <older>`. I read this in the code and did not run it.

**To go back to before D20, if ever needed** (Ubay's, not run): `sudo git -C /srv/lab/agent-harness reset --hard 76b094f690289ea55e6e48de58b349f27c161ef6`, then `harness-deploy 76b094f690289ea55e6e48de58b349f27c161ef6`, then restore `~/.config/systemd/user/harness-reviewer.service.bak` over the runner unit and reload. Gate cards would then be completed by nobody, so only with no D20-loaded ticket on the board.

## Check 2: acceptance on the real suite
Host kit's `harness.acceptance` on trusted `main` `e721f31`, the recorded copies and the live history (so the history is updated, as in any run). No worker card was running. Exit 0 in about 2 s. Afterwards `scoring/` was empty and no `acc-*.test.js` was under `work/`.

Hidden acceptance suite on trusted main `e721f31862`: **67/166** pass.

| file | passed | total | note |
|---|---|---|---|
| acc-analyse.test.js | 4 | 4 |  |
| acc-check.test.js | 9 | 9 |  |
| acc-decode.test.js | 5 | 5 |  |
| acc-delimiters.test.js | 4 | 14 |  |
| acc-dictionary.test.js | 5 | 5 |  |
| acc-events.test.js | 0 | 11 | module did not import (feature not built yet?) |
| acc-filters.test.js | 0 | 8 | module did not import (feature not built yet?) |
| acc-framing.test.js | 9 | 9 |  |
| acc-limits.test.js | 3 | 3 |  |
| acc-order-story.test.js | 0 | 12 |  |
| acc-orders.test.js | 0 | 10 | module did not import (feature not built yet?) |
| acc-page.test.js | 5 | 5 |  |
| acc-presentation.test.js | 4 | 21 |  |
| acc-render.test.js | 5 | 5 |  |
| acc-summary.test.js | 0 | 17 | module did not import (feature not built yet?) |
| acc-timeline.test.js | 14 | 14 |  |
| acc-trades.test.js | 0 | 14 |  |

Host copies from commit `db3b087c00fe`: 17 hidden test files.

Retired on purpose (not counted): `test/acc-check.test.js > bad tags`, `test/acc-timeline.test.js > event keys`


- **No regression.** `passed` went from 57 to 67; nothing left the list. The two retired tests are named apart.
- The v1.2 files mostly fail as not built: `acc-events`, `acc-filters`, `acc-orders`, `acc-summary` don't import; `acc-order-story` 0/12, `acc-trades` 0/14; `acc-delimiters` 4/14; `acc-presentation` 4/21. `acc-render` 5/5 (retired after FXL-13).
- Runtime copies: commit `db3b087c00fe`, 17 hidden files, verified.

**Please look before the go: ten tests are newly in `passed`, so a later failure of any of them holds the queue.** Two are the renamed replacements you expected. **Eight are v1.2 tests that already pass on v1.1 code,** some perhaps only because the thing they check does not exist yet (for example "pasted markup stays text, **in cards** and in the timeline"). If FXL-9 to FXL-13 may break one on the way, retire it first.
```
test/acc-check.test.js > bad tags: 07 and 0 with a pipe, and a non-number with the SOH character
test/acc-delimiters.test.js > a value holding the delimiter followed by digits and = reads as a new field: CheckSum error, no second reading
test/acc-delimiters.test.js > no delimiter form after BeginString is header_order; lower-case <soh> is not a delimiter
test/acc-delimiters.test.js > the delimiter after the CheckSum ends the message even when text follows
test/acc-delimiters.test.js > with the SOH character nothing changes: an empty piece is an error and text forms are ordinary text
test/acc-presentation.test.js > index.html has no inline script, style element, style attribute or event attribute
test/acc-presentation.test.js > no dynamic import, no setAttribute, and no attribute-like property is assigned anywhere in src
test/acc-presentation.test.js > pasted markup stays text, in cards and in the timeline
test/acc-presentation.test.js > the dictionary modules are export default plus one JSON object
test/acc-timeline.test.js > an event carries its sender, target and message number
```

## Check 3: one test alert
One message, sent at **02:02:48** through the alert path's own sender (`harness.alert.configured_send` from the host kit, target `telegram`, the home channel); `hermes send` exited 0. Text:
> TEST ONLY, nothing is wrong. This is the harness runner's alert path being checked after the D20 deploy (live check, 2026-11-27 02:02 CET). No action needed.

**Ubay: please confirm it arrived, and where.** Not exercised: systemd actually starting the alert unit through `OnFailure=` (that needs a failing runner), and the unit's own journal-tail text. I left the once-per-failure record untouched, so a real failure still alerts. The real alert text still starts with an emoji (already noted for the next kit change).

## Also seen
The runner published `docs/agent-harness/STATE.md` by itself at 01:53:32 (commit `6256b76`, "harness state"): **the first real publish through the new path** (a commit; the state file has no PR comment). Its profile table matches the live profiles; the outbox is empty.
