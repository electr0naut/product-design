# Handoff: the VM as of 2026-11-26, about 23:55 CET, updated 2026-11-27 after the audit and bake-off round 2 (HANDOFF-review.md)

Read `RULES.md` first. This file holds only what the repositories don't. No secret values; paths and names only. Clock times are the VM's.

## 1. What is running

| What | State | How to check / how it was started |
|---|---|---|
| **Host runner** | running every minute | systemd **user** units `harness-reviewer.service` + `.timer` (linger is on). `journalctl --user -u harness-reviewer.service -n 20`; `cat /srv/lab/agent-harness/work/runner-status.json`. Each pass logs the kit sha, applies decision files, then the gate and review work. |
| **Evidence driver** | **stopped** (it printed `all done` after FXL-8; log `~/driver-fxl8b.log`) | `cd ~/dev/agent-harness && nohup python3 tools/fixlens_driver.py KEY1,KEY2 /srv/lab/agent-harness/work/<name>.start > ~/driver-<name>.log 2>&1 &`. Alive: `pgrep -af "^python3 tools/fixlens_driver"`. The start file holds one epoch time (the model table counts sessions from it): use the previous ticket's scribe completion, or `date +%s` at load. It keeps polling through blocks. Nothing else runs the hidden suite until D20, so **start it before any new ticket**. |
| **Review watcher** | a `/loop`, **dies with the session** | Cron job `627d258e`, every 10 minutes, prompt: `Pull product-design; if there is a new *review*.md in docs/agent-harness/reports/ since your last check, read it and act on it within the standing approvals, then comment on PR #47; otherwise do nothing.` A new session must create it again (`/loop 10m <that prompt>`). The older shell watchers are gone. "New since my last check" was kept in session memory: see section 3 for what is done. |
| **Bake-off** | **finished**; nothing running. |
| **tmux** | session `worker`, one window running an interactive `claude` in `~` since 24 November | `tmux ls`. I work in a Claude Code background session, id `543590b8-…`, not necessarily that pane. |
| **A stuck shell of mine** | harmless, 14 h old | pid `1144766` with child `sqlite3 -readonly file:/home/ubay/x` (an early command of mine that waits for input). Safe to kill; I left it because this task is read-only. |
| **Hermes** | containers `hermes` and `hermes-dashboard` (image `hermes-lab:fcc26fbd`) | The gateway in `hermes` dispatches cards. |
| **Alerts** | Hermes cron `45f2656e2684` "Harness kanban alerts", every 2 m, no-agent, to Telegram | script `/opt/data/scripts/harness_notify.py` (previous: `.bak-d11`; state `harness_notify_state.json`). |

## 2. Where things are

**Development clones** of `electr0naut/agent-harness` (all clean; commit identity `electr0naut` / `electr0naut@users.noreply.github.com`):
- `~/dev/agent-harness`: branch `d6-driver` @ `31401b1`, **the evidence driver** (`tools/fixlens_driver.py`, never merged).
- `~/dev/agent-harness-d12`: branch `d18-data-modules` @ `0f8acf4` = `master`. The newest clone: use it for loading tickets and for the next branch (fetch first).
- `~/dev/agent-harness-d7`, `-d10`, `-d11`: old branches, no longer needed.
- Tests: `uv run --with pytest --with ruff --no-project python -m pytest -q -p no:cacheprovider`; `uv run --with ruff --no-project ruff check .` and `ruff format --check .`. Fresh-clone them into `/tmp/fc` before posting a sha.

**Deployed:** host kit `~/.local/share/agent-harness/kit` and container copy `/srv/lab/agent-harness` are both `0f8acf4`. Also there: `reviewed-sha`, `local.toml` (container mounts). Wrapper `~/.local/bin/harness-deploy`. Running a kit tool by hand: `cd <kit> && PYTHONPATH=src python3 -B tools/<tool>.py` (`-B` so nothing is written into the kit).

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

**Models now** (default; fallbacks): triage `qwen3.7-plus`; `deepseek-flash` · planner `gpt-6.2-sol`; `qwen3.7-plus`, `deepseek-flash` · implementer `gpt-6.2-sol`; `qwen4-max`, `deepseek-flash` (its `delegation` still names `qwen3.7-plus`) · gatekeeper, reviewer, scribe `deepseek-flash`; `qwen3.7-plus`. Profile backups sit beside each `config.yaml` as `config.yaml.bak-*`; undos are in `D6-morning.md`.

## 3. Work in flight

| instruction | state |
|---|---|
| **FXL-8** | **Landed** (`e721f31`), hidden 59/59, accepted (FXL-8-landed-review). Evidence and my reporting section are pushed. |
| **AUDIT (HIDDEN-suite-review)** | done: `reports/AUDIT-hidden-suite.md`. Its fix is part of D20; **load no ticket until D20 is deployed.** |
| **BAKEOFF round 2 (both reviews)** | done: `reports/BAKEOFF-round2.md`. Waiting for the reviewer's recommendation and Ubay's decision; no live profile changed. |
| **D19-review** | **next; not started.** Its conditions are met (FXL-8 landed, bake-off done). Include the D18 test id fix (`pytest.param(..., id="deep-nesting")`) and, from FXL-8-landed-review, leave `data_modules` out of mutation ranges and find why Stryker exited 1 (keep its full output). My PR note: the workers' reading copy is several paths. |
| **D20-review** | after D19. |
| **D6 "Done means"** (D6-review.md) | all tickets are on the trusted main. **Still owed: `D6-fixlens.md`** (per-ticket table and totals) and the container run of the full Vitest suite on the final main (FXL-8's fix head ran 123/123). The browser check was done by the reviewer. |
| Backlog without its own file | D16 (spec paths in cards and copied at deploy; spec_ref notes into fix feedback; a high finding under the confidence threshold is not just a note), D17 (browser smoke gate; needs Chromium, a user-approved install), finder retry on the next model, transient block retries once, triage check for computation ACs without fixed values, `vendor/*` in high-risk globs, runner sends its own "failed 5 times" alert. |
| Done, no action | all other `*-review.md` files up to FXL-8-landed-review, including MODELS-review/2, FALLBACK-review, D18-code-review. |
| Waiting on others | PRD v1.2 draft is for Gate 3; **load no new tickets** (FXL-8-landed-review). |

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
