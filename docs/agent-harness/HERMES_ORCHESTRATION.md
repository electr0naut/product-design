# Ticket orchestration on Hermes Agent

Audience: the Claude Code session that runs on the VM (`ubay@ailab`) and builds this, and the user who
approves each change.

Related files:

- `DESIGN.md` explains why the pipeline looks the way it does.
- `BUILD_SPEC.md` provides three parts reused here: the deterministic gates (M3), the review schemas (M4)
  and the eval fixture (M5).
- This file replaces BUILD_SPEC's M2 Python driver with Hermes's Kanban board, profiles and gateway.

Every Hermes command below comes from the Hermes docs in `github.com/NousResearch/hermes-agent`
(`website/docs/`). Anything marked **verify** was not confirmed there: check it on this machine before you
rely on it, and record the result in `.harness/hermes-probe.md`.

## Rules for the builder

1. **Read-only first.** In each phase, show what you found and what you propose, then wait for the user's
   OK before changing anything.
2. **Never print secret values.** Show variable names only, and mask keys when you print config.
3. **Ask before acting.** Get explicit OK before you stop or remove containers, install services, edit
   Hermes config, delete profiles or change cron jobs.
4. **Back up first.** Back up before the first change in each phase.
5. **Avoid Anthropic, Ollama and spare Codex.** Never configure Anthropic or `ollama-local` anywhere.
   Codex (`gpt-6-sol`) is scarce: it has a 7-day usage window, so only the planner uses it.

## Starting state (to confirm in Phase A)

There are two Hermes installs:

| | Host install | Docker container `hermes` (plus `hermes-dashboard`) |
|---|---|---|
| Code and data | `~/.local/bin/hermes`, `~/.hermes` | `/opt/hermes`, `/opt/data` |
| Gateway | runs with `--idle-exit`, so it is not always on | always on: s6-supervised, restart policy set |
| Fallback chain | `gpt-6-sol` (openai-codex) → `qwen3.7-plus` (alibaba-token-plan) → `deepseek-flash` | was `gpt-5.6-terra` → Anthropic Fable → `deepseek-v4-flash` (twice). The user has since removed the Fable models; confirm the current chain in A1 |
| Profiles | to list | 21 role profiles generated on 2026-11-21, on DeepSeek then Ollama Qwen. The `-fable` twins have been removed; confirm in A1 |
| Jobs and bots | to list | cron jobs, including the "International Markets Daily Briefing", plus the Telegram and Discord bots |

Known problems:

- **DeepSeek:** Hermes reported "no headroom", but the user confirmed on 2026-11-24 that the account has
  credit, so that report was wrong. Verify agent status claims against the provider before acting on them.
- **Codex** is rate-limited until 2026-11-26 08:21 CET.
- **The briefing job** uses a custom provider, `gpt-5.5-pro`, whose key is the placeholder `no-key-required`.
- **Browser cron jobs** can't reach the browser's DevTools port inside the container.

Target (user decision, 2026-11-24, after A1): **the container is the only always-on Hermes.** It is the
compose project at `/srv/hermes`, with data at `/srv/hermes/data`. The host keeps only the `hermes`
command for chatting, and runs no gateway.

## Phase A: one always-on Hermes, in the container

### A1. Inventory (read-only)

**Container:**

```bash
docker inspect -f '{{.HostConfig.RestartPolicy.Name}} | compose: {{index .Config.Labels "com.docker.compose.project.working_dir"}}' hermes
```

```bash
docker inspect -f '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}' hermes
```

```bash
docker exec hermes hermes cron list
```

```bash
docker exec hermes sh -c 'cut -d= -f1 /opt/data/.env' | grep -i -E 'telegram|discord'
```

**Host:**

```bash
hermes --version; hermes profile list; hermes cron list
```

```bash
hermes fallback list; hermes fallback check --live
```

```bash
cut -d= -f1 ~/.hermes/.env | grep -i -E 'telegram|discord'
```

**Verify:**

```bash
hermes kanban --help
```

```bash
hermes gateway --help
```

Report a table of the cron jobs, each with name, schedule, model, delivery target, and a keep-or-drop
question for the user. Also report which bot tokens each install has.

### A2. Back up both installs

Copy the compose project, which includes its data, and the host install. The data contains credentials,
so keep the copies owner-only:

```bash
sudo cp -a /srv/hermes ~/hermes-srv-backup-$(date +%F) && sudo chown -R ubay: ~/hermes-srv-backup-$(date +%F) && chmod 700 ~/hermes-srv-backup-$(date +%F)
```

```bash
cp -a ~/.hermes ~/hermes-host-backup-$(date +%F) && chmod 700 ~/hermes-host-backup-$(date +%F)
```

### A3. Stop the host gateway (needs the user's OK)

The host gateway, started by hand (PID in A1), has no bot tokens and no cron jobs. Stop it, and check that
no host gateway service is installed:

```bash
hermes gateway stop; hermes gateway status
```

Next, decide how to chat from the host terminal.

1. Compare the two versions:

```bash
hermes --version; docker exec hermes hermes --version
```

2. Choose based on the result:
   - **Same version, and `/srv/hermes/data` readable by `ubay`:** chat with
     `HERMES_HOME=/srv/hermes/data hermes`. Never run `gateway` commands with that setting, because the docs
     allow only one gateway per data folder.
   - **Different versions, or the folder is root-only:** chat through the container with
     `docker exec -it hermes hermes`. Don't loosen permissions on the data folder.

### A4. Apply the cron decisions (needs the user's OK)

Apply `reports/A1-decisions.md` with `docker exec hermes hermes cron remove <id>` and
`docker exec hermes hermes cron pause <id>`. Then:

- find and report the cause of the nightly backup's exit 128;
- run `docker exec hermes hermes cron doctor`;
- show `cron list` as a table.

### A5. Codex load (report only)

All 22 container profiles use Codex `gpt-6-sol` as their primary model. Report:
- which profiles and agent cron jobs actually run;
- when Codex's 7-day window resets;
- a proposal for which profiles should start on `qwen3.7-plus` instead.

Change nothing without the user's OK.

### Phase A acceptance

- `docker ps` shows `hermes` up, and its restart policy is `unless-stopped`.
- No Hermes gateway runs on the host (`pgrep -af "hermes.*gateway"` lists only container processes).
- The Telegram bot answers a message.
- Each kept cron job has one successful run, and the paused jobs show as paused.

## Phase B: the ticket pipeline on Kanban

All Hermes commands in this phase run inside the container: prefix them with `docker exec hermes`, or
`docker exec -it hermes` for interactive ones. Profile aliases such as `triage config set` become
`docker exec hermes hermes -p triage config set ...`.

**Decide before B4:** the reviewer stage calls `claude -p`, and `claude` is not in the container image,
which the docs describe as immutable. Propose one of these to the user:
- install the Claude Code native binary and its login under the mounted `/srv/lab`, only if that folder is
  private to `ubay`;
- a small host-side service that the reviewer card calls;
- running the reviewer stage from the host on a timer.

### B1. Profiles

Create six profiles. The docs use this pattern; `<name>` also becomes a command alias:

```bash
hermes profile create triage --description "Readiness gate: testable criteria, bounded scope, blockers done"
```

```bash
triage config set model.default qwen3.7-plus
```

| Profile | Stage | Primary model | Fallback chain |
|---|---|---|---|
| `triage` | readiness | `qwen3.7-plus` | `deepseek-flash` |
| `planner` | plan, with a criterion-to-test map | `gpt-6-sol` | `qwen3.7-plus` → `deepseek-flash` |
| `implementer` | code plus the planned tests | `qwen3.7-plus` | `deepseek-flash` |
| `gatekeeper` | runs the gates script; makes no judgment calls | `deepseek-flash` | `qwen3.7-plus` |
| `reviewer` | finds defects with Qwen, then refutes and proves them with Claude Code | `qwen3.7-plus` | `deepseek-flash` |
| `scribe` | writes the handoff and posts to Telegram | `deepseek-flash` | `qwen3.7-plus` |

- **Provider and fallbacks.** Set `model.provider` and `fallback_providers` per profile, using the same
  provider names as the host's `hermes fallback list`.
- **Role files.** Each profile gets a `SOUL.md` with its role. Copy the instructions from the matching
  BUILD_SPEC skill:
  - `ticket-readiness` for triage
  - `plan-ticket` for planner
  - `implement-ticket` for implementer
  - `review-evidence` for reviewer
  - `handoff` for scribe
- **Delegation.** Inside any stage, `delegate_task` is only for short lookups. In each profile:
  - set `delegation.model` and `delegation.provider` to `qwen3.7-plus` on Alibaba;
  - set `delegation.fallback_providers` explicitly, so children never fall back to Codex;
  - keep `max_spawn_depth: 1`.
- **Check the profiles:**

```bash
hermes profile list
```

```bash
triage config get model --json
```

### B2. Board, dispatcher and approvals

```bash
hermes kanban init
```

Dispatcher config (`kanban:` block):

```yaml
kanban:
  dispatch_in_gateway: true
  max_in_progress: 1
  max_in_progress_per_profile: 1
  failure_limit: 2
```

`max_in_progress: 1` makes tickets run one at a time. After `failure_limit` consecutive failures a card is
blocked as `gave_up`. The scribe, or a cron job running `hermes kanban list --status blocked`, notifies
Telegram so a human can step in.

**Approvals (verify before Phase C).** Kanban workers run unattended, so a command that needs approval has
no one to answer it.

- Find Hermes's command-allowlist setting (`hermes config`, approvals docs).
- Allow only what each stage needs:
  - the gates script;
  - `claude -p` (reviewer only);
  - `git` on `harness/*` branches;
  - the project's test and lint commands.
- Do not use `--yolo`.

### B3. Ticket loader

`tools/load_tickets.py` (Python 3.12 standard library) reads `tickets/*.md`, the BUILD_SPEC ticket format
(TOML front matter between `+++` lines with `key`, `title`, `rank`, `blocked_by`). For each ticket in
dependency order, it creates:

- a **parent card** `<KEY>: <title>`, holding the ticket text;
- **child cards, in sequence:** `triage`, `planner`, `implementer`, `gatekeeper`, `reviewer`, `scribe`.
  Each one names its assignee and links to the previous card with `--parent`.
- **cross-ticket links:** the first card of a ticket is linked to the last card of each ticket in its
  `blocked_by` list.

It uses `hermes kanban create "<title>" --body ... --assignee <profile> --parent <id> --json` and reads the
new card's id from the JSON. If it finds a dependency cycle, it stops and names the keys in the cycle.

### B4. Stage contracts

Each card's output reaches the next stage through `## Parent task results`. Workers end with
`kanban_complete(summary, metadata)`, with metadata as follows:

| Stage | `metadata` | Blocks the card when |
|---|---|---|
| triage | `readiness.json` (BUILD_SPEC `schemas/readiness.json`) | `ready` is false; post the questions for the author |
| planner | `plan.json` | the plan can't cover every criterion |
| implementer | `implement.json`; branch `harness/<KEY>` pushed | lint or the planned tests fail after 2 attempts |
| gatekeeper | `gates.json` from the BUILD_SPEC M3 gates script | the gates fail; an `implementer` fix card is created as a child |
| reviewer | `findings.json`, `refutations.json`, `proofs.json` | there is a proven or blocking-unproven finding; a fix card is created, at most 2 loops |
| scribe | `handoff.md` path, plus the MR description from BUILD_SPEC `template/mr_description.md` | never |

**Cross-lab review.** For each Qwen finding, the reviewer runs Claude Code on the user's subscription. It
fills the prompt with the finding and ±20 lines of code around it:

```bash
claude -p --model sonnet --max-turns 10 --output-format json --json-schema "$(cat schemas/refutations.json)" < refute_prompt.txt
```

- **Proving.** For surviving high and critical findings, it runs `claude -p` with `schemas/proof.json`,
  then runs the reported test itself. If the test fails on the branch head, the finding is proven.
- **Decision rules** are BUILD_SPEC section 6.2.
- **Verify** that `claude -p` works from a Kanban worker. The docs say tools keep the real `HOME`, so the
  `~/.claude` subscription login should apply.

### Phase B acceptance

- **Smoke test.** Load the single ticket PRC-1 from the BUILD_SPEC fixture (`eval/fixture/tickets/`).
  Watch it with `hermes kanban watch` until the six cards are `done`. Then:
  - `hermes kanban runs <id>` shows one run per card;
  - every card's metadata validates against its schema;
  - the branch `harness/PRC-1` exists.
- **Bounce test.** Load PRC-6, the deliberately vague ticket. It must stop at `triage`, blocked, with
  questions posted to Telegram.

## Phase C: measure

1. Load PRC-1 to PRC-6 together. Expected:
   - **Order:** they run in the order PRC-1, PRC-2, PRC-3, PRC-4, PRC-5.
   - **Bounce:** PRC-6 stops at triage.
2. **Score:** merge each finished branch into the fixture's `main` in order, then run the hidden tests from
   `eval/fixture/hidden/`. Target: 22 of 22 pass.
3. **Collect** these into `.harness/hermes-eval.md`:
   - `hermes kanban stats` output;
   - `hermes kanban runs <id>` output per card;
   - wall time per stage;
   - fix-loop count;
   - usage per provider (Codex, Alibaba, DeepSeek and the Claude subscription), from each provider's
     usage page or Hermes's own reporting (**verify** where Hermes reports usage).
4. **Compare** against the targets in DESIGN.md section 12, then report.

## Kickoff prompt (paste into Claude Code on the VM)

```text
Pull the branch claude/amazing-gauss-xk4abw in ~/product-design, then read
docs/agent-harness/HERMES_ORCHESTRATION.md fully. Follow its builder rules exactly. Start Phase A1 (read-only
inventory), show me the results as tables, and stop. Do not change anything until I approve each step.
Record every "verify" result in .harness/hermes-probe.md.
```
