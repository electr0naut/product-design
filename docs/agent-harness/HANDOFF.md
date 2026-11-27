# Handoff: the VM as of 2026-11-26, about 23:55 CET, updated 2026-11-27 after the audit and bake-off round 2 (HANDOFF-review.md)

Read `RULES.md` first. This file holds only what the repositories don't. No secret values; paths and names only. Clock times are the VM's.

## 1. What is running

| What | State | How to check / how it was started |
|---|---|---|
| **Host runner** | running every minute | systemd **user** units `harness-reviewer.service` + `.timer` (linger is on). `journalctl --user -u harness-reviewer.service -n 20`; `cat /srv/lab/agent-harness/work/runner-status.json`. Each pass logs the kit sha, applies decision files, then the gate and review work. |
| **Evidence driver** | **do not start it:** D20 is deployed and the runner does its job (gate cards, hidden suite, evidence, blocks). Its deletion with `d6-driver` is D20 step 6, after the first FIX Lens ticket through D20. | |
| **Review watcher** | a `/loop`, **dies with the session** | Cron job `69f040d2` (replaced `627d258e` on 2026-11-27), every 10 minutes, prompt: `Pull product-design; if there is a new *review*.md in docs/agent-harness/reports/ since your last check, read it and act on it within the standing approvals, then comment on PR #47. Also, per V12-go-review5: if a FIX Lens ticket is in progress and docs/agent-harness/STATE.md has not been rewritten for 30 minutes, check the runner (read-only) and comment once per quiet spell. If a FIX Lens card is blocked, report it on PR #47 if the runner has not; do not unblock it. When FXL-9 lands, report the two checks of V12-go-review3. Otherwise do nothing.` A new session must create it again. |
| **Bake-off** | **finished**; nothing running. |
| **tmux** | session `worker`, one window running an interactive `claude` in `~` since 24 November | `tmux ls`. I work in a Claude Code background session, id `543590b8-…`, not necessarily that pane. |
| **A stuck shell of mine** | harmless, 14 h old | pid `1144766` with child `sqlite3 -readonly file:/home/ubay/x` (an early command of mine that waits for input). Safe to kill; I left it because this task is read-only. |
| **Hermes** | containers `hermes` and `hermes-dashboard` (image `hermes-lab:fcc26fbd`) | The gateway in `hermes` dispatches cards. |
| **Alerts** | Hermes cron `45f2656e2684` "Harness kanban alerts", every 2 m, no-agent, to Telegram | script `/opt/data/scripts/harness_notify.py` (previous: `.bak-d11`; state `harness_notify_state.json`). |

## 2. Where things are

**Development clones** of `electr0naut/agent-harness` (all clean; commit identity `electr0naut` / `electr0naut@users.noreply.github.com`):
- `~/dev/agent-harness`: branch `d6-driver` @ `31401b1`, **the evidence driver** (`tools/fixlens_driver.py`, never merged).
- `~/dev/agent-harness-d12`: on branch `d23-static-mutants` @ `6c483e6` = `origin/master`. The newest clone: use it for loading tickets and for the next branch (fetch first).
- `~/dev/agent-harness-d7`, `-d10`, `-d11`: old branches, no longer needed.
- Tests: `uv run --with pytest --with ruff --no-project python -m pytest -q -p no:cacheprovider`; `uv run --with ruff --no-project ruff check .` and `ruff format --check .`. Fresh-clone them into `/tmp/fc` before posting a sha.

**Deployed:** host kit `~/.local/share/agent-harness/kit` and container copy `/srv/lab/agent-harness` are both `6c483e6` (since 13:41 on 2026-11-27). Also there: `reviewed-sha`, `local.toml` (container mounts). Wrapper `~/.local/bin/harness-deploy`. Running a kit tool by hand: `cd <kit> && PYTHONPATH=src python3 -B tools/<tool>.py` (`-B` so nothing is written into the kit).

**Host-only state** `~/.local/state/agent-harness/`:
| entry | what it is |
|---|---|
| `trusted/<repo>.git` | the trusted `main` of each repository (`fix-lens.git` main = `e721f31`, FXL-8). Others are older test repos. |
| `fix-ledger.json` (`.bak` from the D7 migration) | fix passes, resets, approved test edits |
| `proofs/` | stored proof tests, rerun on every retry |
| `tickets/<KEY>.md` | the ticket text the loader recorded (what the spec pass reads) |
| `specs/fix-lens/technical-design.md` | the design the spec pass reads |
| `acceptance/fix-lens/*.test.js` | the hidden suite (9 files, 59 tests) |
| `acceptance-history/fix-lens.json` | which hidden tests have ever passed (regression rule) |
| `labels.json`, `queue.json` | ticket labels (risk tier); the order `relink_bounced` uses |
| `decisions.git`, `decisions-state.json` | host-only fetch of the review branch; applied decision ids (only `D-20261126-1`) |

**Workers' reading copies of the design** (each profile's `~` is its own folder): `/opt/data/.hermes/profiles/{implementer,planner}/home/.local/state/agent-harness/specs/fix-lens/`, `/opt/data/.local/state/agent-harness/specs/fix-lens/`, `/srv/lab/agent-harness/work/specs/fix-lens/`, plus one in each `bake-r2-*` profile's home.

**Work folder** `/srv/lab/agent-harness/work/`: `fix-lens/` (work repo), `fix-lens-tickets/` (copies the loader read), `runs/<KEY>/`, `old/` (retired run folders), `reviewer-attempts.json` (one runner attempt per card), `fixlens*-load.log`, `*.start`, `hold-*.md`, `bake/` (only the running bake-off's current folder). The many other files are leftovers of earlier phases.

**Scratch and throwaway (mine):**
- `~/.local/state/agent-harness-bake/` (a sibling of the state folder, not inside it): round 1 `done/`, `bare/`, `gates/`, `scores.json`, `usage.jsonl`, scripts `run.py`, `gates.py`, `score.py`, `usage.py`, `rel.py`, `pause.py` (pauses candidate processes), `accfull.py` (full hidden suite on a head, no network), `harness.bake.toml`; `fxl2b/`, `fxl3b/` (scratch trusted roots); `dictcheck/` (independent XML extraction); `r2/` (round 2).
- **No throwaway Hermes profiles remain.** Round 2 session databases were copied to `~/.local/state/agent-harness-bake/audit/sessions/` before deletion (round 1's were not kept). Do the same before deleting any profile whose records may matter. The name prefix `bake-` keeps a profile out of the driver's model tables. `audit/` also holds the audit scripts and raw results; `work/bake/` is deleted.
- Host `/tmp`: `dsprobe.py`, `bake_setup.sh`, `bake_cfg.sh`, `fxl5orig.md`, `fxl8add.md`. Container `/tmp/dsprobe.py`. Both `dsprobe.py` files are my probe for the provider's model name (no secrets); a safety check refused a command that removed them, and I did not retry. Other files in those `/tmp` folders I have not identified as mine.

**Models now** (default; fallbacks): triage `qwen3.7-plus`; `deepseek-flash` · planner `gpt-6.2-sol`; `qwen3.7-plus`, `deepseek-flash` · implementer `gpt-6.2-sol`; `deepseek-v4.1-flash-1017`, `qwen4-max`, `deepseek-flash` (its `delegation` still names `qwen3.7-plus`) · gatekeeper, reviewer, scribe `deepseek-flash`; `qwen3.7-plus`. Profile backups sit beside each `config.yaml` as `config.yaml.bak-*`; undos are in `D6-morning.md`.

**Last model change (FALLBACK2-review, 2026-11-27 00:4x; Ubay: "agreed on all points", 2026-11-26), `implementer` fallbacks only.** Old: `qwen4-max`, `deepseek-flash`. New: `deepseek-v4.1-flash-1017` (alibaba-token-plan), `qwen4-max`, `deepseek-flash`. Default unchanged. Backup `/opt/data/profiles/implementer/config.yaml.bak-20261127-fallback2`; **undo:** copy it over `config.yaml`. The diff against it is three added lines in the fallback list. One call afterwards answered on `gpt-6.2-sol` (`openai-codex`), with no `Fallback activated` line. A live failover is untested.

## 3. Work in flight

| instruction | state |
|---|---|
| **FXL-8** | **Landed** (`e721f31`), hidden 59/59, accepted (FXL-8-landed-review). Evidence and my reporting section are pushed. |
| **AUDIT (HIDDEN-suite-review)** | done: `reports/AUDIT-hidden-suite.md`. Its fix is part of D20; **load no ticket until D20 is deployed.** |
| **BAKEOFF round 2 (both reviews)** | done: `reports/BAKEOFF-round2.md`. Waiting for the reviewer's recommendation and Ubay's decision; no live profile changed. |
| **D19-review** | done and deployed (`76b094f`). **Copies are recorded:** `D-20261127-1` (`refresh_copies`, commit `db3b087`: design v1.2 and 17 hidden files, host and all four worker reading copies) and `D-20261127-2` (two tests retired; 57 remain in `passed`) applied 01:52. The five `acc-render` tests are retired after FXL-13 lands. |
| **D20-review** (+ HIDDEN-suite-review §2) | deployed (`c06cd27`), but its loader cannot be imported (`V12-live-checks.md`). Fix = D21. |
| **D21-review** | **done, deployed** (`7c190a2`, `master` too). D21-code-review steps 1 and 2 **met** (`V12-live-checks.md`: fixture tickets SMK-1/SMK-2 through the pipeline). **Stopped at step 3.** |
| **D6 "Done means"** (D6-review.md) | all tickets are on the trusted main. **Still owed: `D6-fixlens.md`** (per-ticket table and totals) and the container run of the full Vitest suite on the final main (FXL-8's fix head ran 123/123). The browser check was done by the reviewer. |
| Backlog without its own file | **Gate cards:** stop a worker with Kanban tools completing one (a board permission or a separate owner; today detected only). **Next kit change:** no emoji in anything the harness prints or sends (`alert.py`; `harness_notify.py` has some too); `deploy.py` must not print a re-run's own sha as the undo, and its host undo needs the container `sudo ... reset` first (a deploy of an older sha is refused as not a fast-forward). Also D16 (spec paths in cards and copied at deploy; spec_ref notes into fix feedback; a high finding under the confidence threshold is not just a note), D17 (browser smoke gate; needs Chromium, a user-approved install), finder retry on the next model, transient block retries once, triage check for computation ACs without fixed values, `vendor/*` in high-risk globs. D20 step 6 (delete the driver and `d6-driver`) waits for the first FIX Lens ticket through D20. **From `FXL-17-block-review.md`:** a block for "the fix pass edited base tests" carries, in the block report itself: the first gates run's failing items, the fix pass's test diff, the whole ticket's diff of the touched test and source files, and the other files the fix pass touched. |
| Done, no action | all other `*-review.md` files up to FXL-8-landed-review, including MODELS-review/2, FALLBACK-review, D18-code-review. |
| **V12-go-review4** (FXL-14 to FXL-16) | Ubay, 2026-11-27, quoted there: "yes release", **only if FXL-9 to FXL-13 all land clean:** each finished with its gate completed by the runner; isolated hidden run with no regression; no block or hold open and no card unblocked more than once; the reviewer has accepted each landing in a review file. Any one missing: no release, wait for Ubay. Then: the reviewer pushes one commit (retire the five `acc-render` ids, remove the file, `refresh_copies` of that commit); confirm on the PR that both applied and the copies verify; **load FXL-14 to FXL-16 only on the reviewer's later go file** (files from `1b47d32` or later). It does not answer D21 step 3. |
| **First v1.2 batch (V12-go-review5)** | **FXL-9 to FXL-13 loaded 12:10 on 2026-11-27** (Ubay: "start the first batch now, alert or no alert"; ids in `V12-live-checks.md`). The runner publishes evidence and block reports itself; **do not start the old driver; do not unblock** (decision files only). With FXL-9's landing report the two checks of `V12-go-review3.md`. If `STATE.md` is unwritten for 30 min while a ticket is in progress, check the runner and comment. The 02:02 alert is **unconfirmed**: next kit change, with a second test message Ubay confirms. FXL-14 to FXL-16: `V12-go-review4.md`, only on the reviewer's later go file. |
| **FXL-9** | **landed clean** (`60b1211`; hidden 77/166, no regression; accepted in `FXL-9-landed-review.md`; both V12-go-review3 checks met). Mutation did not run: Stryker's instrumentation adds `new Function`, which the source check forbids, and the check is selected only when `tools/audit-source.mjs` is mutated (`reports/FXL-9-checks-and-mutation.md`). **To do:** confirm from FXL-10's mutation log that it did not recur. Next kit change: keep source-text tests out of Stryker's runs; mutation errors named in `STATE.md`; then rerun the missed mutation runs on landed commits before v1.2 is called finished. **No kit change while cards run.** |
| **D22 (source-text tests out of Stryker's runs)** | approved, option A (`D22-code-review.md`); deployed as part of D23 (next row). **Known limit:** with the static check left out, mutants of `tools/audit-source.mjs` always show as without tests, which says nothing about that tool's tests; a ticket changing only that tool gives a mutation error (named in `STATE.md`). |
| **D23 (with D22)** | deployed `6c483e6` at 13:41:18 on 2026-11-27 and confirmed (`reports/D23-deploy-confirm.md`). **FXL-9 rerun done** (14:14): 187 killed, 70 survived, 32 timeout, 156 no tests, 2 static; identical to the trial; raw report in the host records `records/FXL-9/*.stryker-report` (`reports/V12-batch2-load.md`). The automated review gets no mutation data. |
| **FXL-9 test gaps (the batch's main finding, goes to Ubay)** | `reports/FXL-9-survivors-classified.md`, **corrected** (`FUZZ-correction.md`: the reviewer's random generator was faulty; the earlier 28/7/35 are wrong). Of 70 trial survivors, **44 change behaviour; at landing the hidden suite caught 5** of them (so 39 by no test); with `acc-framing-rules.test.js` (now 11 tests) it catches 23, and **21 are still caught by nothing**; 26 showed no difference. Six rows are approximate. The new tests reach the host copy only with the next `refresh_copies`, in the `acc-render` retirement commit. The landed-clean verdicts for FXL-9 to 11 stand. A tests-only follow-up ticket comes after FXL-16. `tools/rerun_mutation.py FXL-9` still runs. |
| **FXL-10** | **landed clean** (`80116ec`; hidden 88/166, no regression; `FXL-10-landed-review.md`). Blocked once (approved by `D-20261127-4`, unblocked once by `-5`). Its 5 listed mutation survivors are static mutants run against one page test only (`reports/FXL-10-static-survivors.md`; proposed kit change: count them as not measured; **not to be built without a review saying so**). |
| **FXL-11** | **landed clean** (`fa78e7b`; hidden 98/166; no fix pass or block; its 6 survivors are equivalent mutants; `FXL-11-landed-review.md`). `reports/FXL-9-trial-survivors.md` lists the trial's 70 survivors, 25 untested and 32 timeouts in `src/framing.js`; the reviewer decides on a follow-up. |
| **FXL-12** | **landed clean** (`ea0b353`; hidden 115, no regression; `FXL-12-landed-review.md`, which also accepts the D23 deploy). **Settled:** Ubay approved it (design v1.2.2; the reviewer quotes "A"). It was a design clarification (section 13: a later report whose ExecRefID names a remembered, unmatched cancel or correction; FXL-12 treats it as unmatched, the reviewer prefers that). No code change. Its 19 mutation survivors are unclassified and go to the follow-up ticket's list. |
| **FXL-13** | **landed, NOT clean** (`8881fce`; `acc-filters` 6 of 8, from a sentence in the ticket; `FXL-13-landed-review.md`). So the `V12-go-review4` release lapsed; replaced by `V12-go-review6`, which quotes Ubay (2026-11-27): "go with your recommendation, dont stay idle if not absolutely necessary" (the reviewer's reading of the second part is in that file; RULES section 3 still waits for him). `D-20261127-6/-7` applied: copies at `9448c0b99295`, 17 hidden files. |
| **FXL-17, then FXL-14 to FXL-16** | **loaded 14:16 and 14:17 on 2026-11-27** (`reports/V12-batch2-load.md` has the card ids and links; FXL-14 waits on `accept FXL-17`). While they run: report blocks, do not unblock; **report each ticket's mutation line**; the reviewer checks each ticket's own hidden file at landing, since D24 is not deployed. Copies now `23952fd05985`, design v1.2.2 `023e2adfdb09`, 17 hidden files (`D-20261127-8`, applied before the load; see the correction in that report). **FXL-17 landed clean** (`bfb67b7`; `acc-filters` 8 of 8; 130 of 173; mutation 6 killed, 0 survived). The reviewer expects FXL-14 may block the same way (its AC15). **FXL-14 landed clean** (`ee91fe2`; `acc-presentation` 21 of 21; 149 of 173; mutation 227 killed, 12 survived, 4 static; `FXL-14-landed-review.md`). |
| **D24 and the test guard** | built and reported (`reports/D24-expected-hidden.md`): branch **`d24-after-guard`**: `a18c096`, guard `1007fff`, D24 `b20b702` (`d24-expected-hidden` is superseded). **Waiting for review** (two commits reviewed apart). Dev clone `~/dev/agent-harness-d12`. Deployed only if Ubay says so. **Suite runs stay in throwaway containers** until the guard is deployed, and afterwards while cards run; the proof scripts were in the job's scratch folder (method: `LIVE-writes-audit.md`). |
| **D25, D26** | `D25-D26-review.md`: routine actions as runner decisions, then one-shot jobs. Build **after** the audit and D24. |

## 4. Recurring jobs, as commands

**Load tickets** (on the host, from the newest clone; paths absolute; only between tickets):
```
cp <product-design>/docs/agent-harness/fix-lens/tickets/<KEY>.md /srv/lab/agent-harness/work/fix-lens-tickets/
cd ~/dev/agent-harness-d12 && PYTHONPATH=src python3 -B tools/load_tickets.py --repo /srv/lab/agent-harness/work/fix-lens /srv/lab/agent-harness/work/fix-lens-tickets/<KEY>.md [...] > /srv/lab/agent-harness/work/<name>-load.log
```
Traps: one load chains its tickets in order of `(rank, key)`, and its first ticket waits only on its own `blocked_by`, so it can start beside a running ticket. To force an order, load with `--hold "<why>"`, re-link with `hermes kanban link/unlink` (**add the new wait before removing the old one**), rewrite `queue.json` with `harness.queue.write_queue`, then complete the hold.

**Retry a card** (only when a review says so; once): prefer a decision file. By hand: remove its id from `work/reviewer-attempts.json` if listed, then `docker exec hermes hermes kanban unblock <id>`.
**Approve a test edit / reset:** `tools/approve_test_edit.py KEY --head <40 hex> --files ... --reason "..."`; `tools/reset_attempt.py KEY --reason "..."`. For a reload after a reset: `hermes kanban archive <id>` each of the ticket's and the unstarted later tickets' cards, `mv work/runs/<KEY> work/old/runs-<KEY>.attemptN`, keep the report as `<KEY>-attemptN.md`, load, restart the driver.

**Hidden suite on a head** (nothing written to the history; never visible to workers): `python3 -B ~/.local/state/agent-harness-bake/accfull.py <40-hex head> <scratch name>`.
**Project tests on a head:** `D=/srv/lab/agent-harness/work/scratch-<name>; mkdir $D && git -C /srv/lab/agent-harness/work/fix-lens archive <head> | tar -x -C $D && ln -s /srv/lab/agent-harness/deps/fix-lens/node_modules $D/node_modules; docker exec --user hermes --workdir $D hermes node_modules/.bin/vitest run`, then remove `$D`.
**Publish evidence:** the driver writes `fix-lens/runs/<KEY>.md` and `.patch` (blocks also as `<KEY>-block-<card>-<n>.md`) and comments. **It overwrites `<KEY>.md` at landing**, so copy anything added by hand first. After a landing I append "Implementer, finder and Codex use" (models, fallback yes/no, Codex calls and tokens from the table, rate-limit lines from the profiles' `logs/agent.log`, comparison) and comment.
**Push and comment:** in `~/product-design` (branch `claude/amazing-gauss-xk4abw`; the reviewer pushes there too): `git pull --rebase` before and after committing, then push; `gh pr comment 47 --repo electr0naut/product-design --body "..."`. Avoid `@` names in bodies.
**One tiny model check:** `docker exec --user hermes --workdir /tmp hermes timeout 180 hermes -p <profile> chat -Q -q "Reply with the single word: ready"`, then read the newest row of `/opt/data/profiles/<profile>/state.db` (`sessions.model`, `billing_provider`). Container Python needs `docker exec -i` for heredocs; its system Python has no `yaml`; use `hermes -p <p> config set` (it may re-indent the file: diff against the backup).

## 5. Habits that are in no file
- Comment on PR #47 after each push of evidence or of a kit branch.
- When auto mode or a safety check refuses an action: stop, don't route around it, tell Ubay.
- Questions for the reviewer go in reports; Ubay is asked only for decisions a review marks for him, briefly. Deploy lines reach Ubay as plain shell lines, not with a leading `!`.
- Load nothing and change no profile unless a review says so.
- Keep a copy of block evidence before anything overwrites it.
- My tiny verification calls show up as extra sessions in a ticket's model table: say so in the report.
- Before running the hidden suite while a bake-off candidate runs, use the no-network container (`accfull.py`), not the live-container scoring.

## Differences from RULES.md
1. **§4 "never copy hidden tests into a work folder" is broken by the kit itself.** `harness.acceptance` / `harness.score` check out the trusted main under `/srv/lab/agent-harness/work/prove/` and copy the hidden files there to run them in the container. The driver does this after every landing, **while the next ticket's first cards may be running** as the same container user. The folder is removed after the run (seconds), and I found no sign a worker read it, but I did not audit every worker session. D19/D20 should score in a place workers cannot see (a separate no-network container, as `accfull.py` does).
2. **§3 "nothing written by hand to `~/.local/state/agent-harness/`":** until D19's `refresh_copies`, I have copied hidden tests and the design there with `cp`, each time a review told me to (including earlier today, before the rules were approved). I also rewrote `queue.json` once by calling `queue.write_queue` from a one-line script (after the FXL-5 reload), which is a kit function but not a kit tool. Say whether either is allowed; otherwise such steps wait for Ubay or D19.
3. **§3 model changes and §1 quoting Ubay:** the finder was moved to `deepseek-flash` on the reviewer's delegated decision (FXL-1B-review4), and the fallback change (FALLBACK-review) says "approved by the user" without quoting him. Both predate the approval of the rules. Under them, such an instruction would be a stop. MODELS-review2 quotes him.
4. **§3 deleting:** settled: RULES now allows deleting what a job created itself, listed in its report.
5. **§5 branch checks:** RULES asks for tests and ruff clean; I also run them from a fresh clone before posting a sha.
6. **Not in RULES:** the hold-then-relink loading trap and the "start the driver before a ticket" dependency above.
