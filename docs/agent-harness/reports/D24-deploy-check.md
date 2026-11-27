# The deploy of `b20b702`: the four checks (D25-code-review). **Nothing is off in 1 to 3.**

Read-only.

## 1. When, and what ran
| time (15:xx) | event |
|---|---|
| 22:34 | FXL-15 reviewer completed |
| 22:38 | **FXL-15 scribe started** |
| 22:58 | a runner pass finished (`completed t_0c234ab4; completed t_b3087bc2`); the next one started within the same second |
| **22:58** | **host kit checked out `b20b702`** (reflog; `reviewed-sha` and `local.toml` written the same second) |
| **22:59** | **container copy fast-forwarded** |
| 23:39 | the pass that spanned the switch finished: `idle; idle` |
| 24:17 | first pass that logs `b20b702`: `idle; idle` |
| 25:27 | FXL-15 scribe completed |

Within a minute either side of the switch (21:58 to 23:59), the only cards running or changing were those two: the reviewer ended 24 seconds before, and **the scribe was running, 20 seconds in.** FXL-16 had not started.

## 2. The deployed kit
- 157 tracked files, **0 differ** between host and container; both at `b20b702`; the host kit's tree is clean.
- Fresh-process import of all 28 modules: **28 of 28** with the host kit's interpreter and **28 of 28** with the container's.
- `--help` for the 8 tools that have one: **8 of 8** in the container. On the host, 7 of 8 in my first try; `deploy.py` failed with `No module named 'deploy_host_kit'` **because of my command:** I ran it with `-P` without the `tools/` path. The installed `harness-deploy` wrapper uses `-P` **with** that path, and `harness-deploy --help` works (exit 0).

## 3. The spanning pass and the scribe
- The pass from 22:58 to 23:39 logged `6c483e6` (the sha it read when it started), `idle; idle`, and `Finished`. **No error, traceback, "failed" or "skipped" line** in the runner's journal from 15:20 until this check; the alert unit logged nothing. It published a state file that names the new sha, which it read after the switch. I have not checked whether that pass imported any module after the checkout; it did no gate, review or finishing work.
- **FXL-15's scribe finished normally:** one run, outcome `completed`, no error, no retry, regular heartbeats across the switch; `handoff.md` and `mr.md` written at 25:14 and 25:22.

## 4. FXL-15's acceptance run (under D24)
Evidence shows **`acc-order-story.test.js`: 12 of 12 pass, met.** Runner records: 159 of 173, no regression, `gate_was_open` false, nothing ran beside it, no errors or blocks. No scoring folder or container left.

## A correction to my own messages
My comment at 15:22 and the report to Ubay that followed said `b20b702` was not deployed. That was checked at 15:21 and true then; the deploy came at 15:22:58, after it. My D26 messages a little later did not recheck, and `HANDOFF.md` said "not deployed" until now.
