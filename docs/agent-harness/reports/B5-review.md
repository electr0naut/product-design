# Phase B5 review

**Approved, with two security fixes required before any more variants run.**

Verified in the reviewing session on `agent-harness@de03aab`: `71 passed in 34.07s`, and ruff is clean.

The B5 work itself is good:
- the budget fix is correct;
- `resolve_id` is strict when a name matches nothing or matches several tests;
- Telegram alerts use Hermes's own notifier;
- only `harness/*` branches can advance `main`.

The first live variant is a strong result. B1 was **caught and proven**: Qwen found it, Claude upheld it and
wrote a test, and the re-run failed on an assertion. It cost $0.38. The one-attempt guard also did exactly its
job on the PATH failure.

## Must fix before B2 to B6 and C1 to C4

**1. Untrusted code runs on the host as `ubay`.**

The prove step runs pytest **on the host**, in two places: Claude's own `Bash(pytest)` in the scratch
worktree, and the clean-worktree re-run. The code under test was written by container workers (the
implementer on Qwen, which can be prompt-injected through ticket text). A `conftest.py` or an import-time side
effect would execute on the host with the user's privileges, next to `~/.claude`, SSH keys and the Hermes
data. That undoes the container boundary the design depends on. The prove step needs two changes:
- **Writing:** Claude gets **Read, Write and Edit only**, with no Bash. It writes the test file and doesn't run
  it.
- **Running:** the runner executes the test **inside the container**, as the `hermes` user, against the
  container's view of the worktree. Use `docker exec -u hermes hermes .../.venv-container/bin/python -m pytest
  ... --junitxml=...`; `/srv/lab` is mounted at the same path. `proof_outcome` then reads the JUnit file as it
  does today.

The refute step stays as it is: Claude, no tools, reading text only. The host never imports or executes
repository code.

**2. Run-folder files can redirect the host runner.**

`base.txt`, `branch.txt` and `repo.txt` live in `work/runs/<KEY>/`, which container workers can write. A worker
could point `repo.txt` at any repository on the host, or name any branch, and the host runner would diff it,
send its contents to the models, and act on it. Validate all three before use:
- `repo.txt` must resolve to one of `KIT/work/fixture-repo` or `KIT/work/variant-repo`;
- `branch.txt` must match `^(harness|variant)/[A-Z0-9-]+$`;
- `base.txt` must be a 40-character hex sha that exists in that repo.

Anything else blocks the card as `needs_input`, with the reason.
**Tests:** a hostile `repo.txt` (`/home/ubay`) and a hostile branch name are both refused, and no git command
runs on them.

## Decisions for the user

- **Telegram noise:** up to 6 messages per ticket on success. I recommend subscribing only to `blocked`,
  `gave_up`, `crashed` and `timed_out` on all cards, plus a `completed` ping from `scribe` only. That's one
  message per finished ticket, and every problem still reaches you.
- **Confirm in Telegram** that the "PRC-6 · triage blocked" message arrived.

## Next

1. Fix 1 and 2 with tests.
2. Re-run **B1** to confirm that proving still works with the test run inside the container.
3. Run B2 to B6 and C1 to C4 one at a time. Report:
   - recall over the 6 bugs and false blocks over the 4 clean variants (DESIGN section 12 targets: at least
     5 of 6, and 0 of 4);
   - the cost per variant.
