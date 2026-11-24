# Phase B3: loader, host reviewer runner, configs, 2026-11-24

User said go. Kit repo `electr0naut/agent-harness` (private, branch `master`): commits `131abfd` (gates) and `2ca74ea` (everything else), pushed.
No secrets recorded. No pipeline card exists; the board is empty. Nothing was installed (no systemd timer, no linger).

## What was built (stdlib only, in `src/harness/`)

- `gates.py` (`131abfd`): the empty-criteria check now runs first, before any worktree or test.
- `loader.py` + `tools/load_tickets.py`: per ticket, in dependency order: a parent card holding the ticket text (completed at once, so the
  text arrives as "Parent task results"), then six stage cards chained with `--parent`; the first stage card also waits on the last
  (`scribe`) card of each blocker. Cards use `--body-file` (bodies in `work/cards/<KEY>/`), `--idempotency-key <KEY>:<stage>`,
  `--assignee`, `--workspace dir:<fixture repo>`, `--json`. A dependency cycle stops the load and names the keys; `--dry-run` shows the plan.
  Dry run on PRC-1..6 gives the expected graph (PRC-4 waits on PRC-2 and PRC-3).
- Stage bodies tell each worker where to write its JSON (`work/runs/<KEY>/<stage>.json`, so later stages read files, since only direct parents
  reach a card), to write files with the file tool (heredocs are denied), and never to push. The gatekeeper runs one exact `harness.gates` command.
- `reviewer.py` (host runner): `flock` lock; take one ready `reviewer` card; `kanban claim --ttl 1800`; heartbeat thread every 60 s; find with the Hermes
  `reviewer` profile (Qwen) via a one-shot call; validate against `schemas/findings.json`; filter (confidence, file in diff, line within 3 of a
  changed line); refute each survivor with `claude -p --model sonnet --tools "" --max-budget-usd 0.75 --json-schema refutations`; prove critical/high
  that are not refuted with a Claude run in a scratch worktree (tools: Read, Write, Edit, `Bash(<python> -m pytest *)` only), then re-run the test in a
  clean worktree (proven only if pytest exits 1); decide per BUILD_SPEC 6.2; write `findings/refutations/proofs/review.json` to the run folder;
  `kanban complete --metadata` or `kanban block --kind needs_input`. Any error blocks the card as `transient`. Per-card spend cap `$3` (default).
- Config: `harness.toml` (container paths: `.venv-container`, `work/fixture-repo`) and `harness.host.toml` (same with the host `.venv`).
  Both venvs got a `harness.pth` so `python -m harness.gates` needs no `PYTHONPATH`.
- Fixture repo: `work/fixture-repo` (local, `main`, one baseline commit, **no remote**), baseline tests and ruff pass on host and container.
  Repo-local git identity `harness <harness@localhost>`: the container's global git identity carries a personal email, so workers' commits would have used it.
- `systemd/harness-reviewer.{service,timer}` and a README (every 60 s, `Type=oneshot`). **Not installed**; needs your OK and `sudo loginctl enable-linger ubay`.
- Tests: 40 pass (14 gates, 9 loader, 17 reviewer) on the host and in the container; ruff check and format clean.
  Reviewer tests use fake Qwen/Claude/kanban plus real git worktrees and pytest, and cover each row of the decide table, a proven finding blocking
  the card, a passing proof disproving it, no findings, a failure blocking as transient, idle, and the budget cap.

## Verified live (details in `.harness/hermes-probe.md`)

- `claude -p` here has no `--max-turns` (the doc's command is wrong); the runner uses `--max-budget-usd`. Its JSON result carries `structured_output`
  and `total_cost_usd`; one tiny call cost $0.016.
- **Claim TTL:** a reviewer card claimed with `--ttl 20` and never completed went back to `ready` about 60 s later, so a crashed runner does not strand a card.
  (The test card is archived.)

## Not done / honest gaps

- The real runner has not seen a card with real run files, so the Qwen "find" call, the Claude prove step and the claim loop are untested end to end
  (only with fakes). The PRC-1 smoke test will be the first full run.
- No `risk.py`: the runner always uses the medium-risk path (refute all, prove critical/high).
- Fix loops are not automated: a gate failure or a blocking review blocks the card with a reason; nobody creates the `implementer` fix card yet.
- Between tickets, `main` does not advance: PRC-2..5 depend on PRC-1's code, and the implementer branches from `main`. Phase C needs a merge step
  (e.g. the scribe fast-forwards `main` locally; that needs `git merge*` in the allowlist). Not built; decision for you and the review.
- The `-fable` s6 service folders are untouched.

## Next

Review the kit code (`agent-harness@2ca74ea`). Then, with your go: B4/smoke test, loading PRC-1 (`python tools/load_tickets.py eval/fixture/tickets/PRC-1.md`),
and installing the reviewer timer (your OK and sudo).
