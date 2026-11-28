# D25 and D26: take the standing VM session out of the delivery path (instruction; build after D24)

**Why.** Ubay asked on 2026-11-27 whether the single long-running session on the VM is solved. It is half
solved: since D20 the runner moves tickets, scores them and publishes. But loading tickets, the diff a block
needs, mutation reruns and kit builds still go through one session with ageing context. Today that session
missed a review file once, posted two statements that were already stale, and ran the kit's tests against live
state. You reported each one yourself; the point is the design, not the conduct.

**Order: finish the live-writes audit and D24 first.** Then D25, then D26. Each on its own branch, in a clone
or a throwaway container, never against live state. Each is deployed only by Ubay.

## D25: routine actions become runner decisions
Three additions, each applied by the runner like the existing decisions, with the result as a PR comment.

1. **`load_tickets`**: `{id, action, key, tickets: [keys in load order], commit: <40 hex>, reason}`.
   The runner reads each ticket file from that commit of the published branch (the tickets folder comes from
   the reviewed host config, per repository), and loads them in the given order with the same code as
   `tools/load_tickets.py`. It refuses, loading nothing, if any key is already in the registry, a file is
   missing at that commit, or a `blocked_by` names a ticket that is neither loaded nor in the list. The comment
   gives, per ticket, the triage and gate card ids and what the triage waits on.
2. **`rerun_mutation`**: `{id, action, key, reason}`. What `tools/rerun_mutation.py KEY` does. If a card of the
   repository is running, the decision is refused and says so; it is not retried by itself.
3. **A block for "the fix pass edited or deleted base tests" carries its own evidence.** The block report
   includes: the failing items of the first gates run; the fix pass's diff of the named test files; the whole
   ticket's diff of those files; the `--stat` of the fix pass; the latest gates summary with the mutation line.
   Diffs come from the work repository with the root-safe git settings. A diff over 400 lines is cut, with the
   count stated.

Tests: each refusal above; a load of two tickets where the second waits on the first one's gate; a decision
applied twice is applied once; the block report for a fix pass that adds tests, and for one that deletes one.

## D26: one-shot jobs for what still needs an agent
What remains for an agent after D25 is mainly kit builds and audits. Each becomes a job that starts fresh.

- **A job file** `docs/agent-harness/jobs/J-<yyyymmdd>-<n>.md` on the published branch: the instruction, as the
  review files are today.
- **A host timer** finds job files that have no entry in a host-only ledger and runs them one at a time: a new
  Claude Code session, non-interactive, in a fresh scratch clone, whose prompt is fixed text: read `RULES.md`,
  read `HANDOFF.md`, read the job file, do it, write `reports/<job id>.md`, update `HANDOFF.md` if anything a
  later job must know has changed, push, stop.
- **Limits, in the unit and the settings, not in the prompt:** a time cap and a turn cap; the permission
  allowlist the standing session uses today, and never a skip-permissions flag; no `sudo`; no write to the
  trusted repos or the host state except through the kit's own tools; one job at a time, with a lock.
- **The runner comments** on the PR when a job starts and when it ends, with the exit state. A job that hits a
  cap or fails is not retried by itself.
- **Trust:** a job file is accepted on the same footing as a decision file is today (the branch is the channel;
  signed decisions are still on the backlog). Say in the report what a person with push access to the branch
  could and could not make a job do, given the allowlist.

**Say first what exists:** how the standing session is started and with which settings, so the job uses the
same and nothing wider. Propose the unit, the settings file and the fixed prompt in your report before
building, if anything in this spec does not fit the VM.

**When D26 is deployed and two jobs have run to the end,** the standing session is closed. Until then it stays.

## What stays with Ubay
Everything in section 3 of `RULES.md`. Neither change lets a decision or a job deploy the kit, change a model,
touch a secret, or send anything outside.
