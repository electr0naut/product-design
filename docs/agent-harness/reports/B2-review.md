# Phase B2 review

**Approved, including the gates fixes.**

## Gates fixes (`agent-harness` 81fa5ed): re-reviewed, approved

- **Collection failures:** a failed test collection now raises an error that names the commit, the command and
  the last 8 lines of output. Exit 5 is still treated as a legitimate empty result.
- **Acceptance criteria:** they now come from `readiness.json` and `--acs` is required. Unknown criteria in the
  implementer's map are reported, and an empty criteria list is an error.
- **Verified independently** in the reviewing session, on Python 3.13:

  ```text
  14 passed in 22.36s
  All checks passed!
  3 files already formatted
  ```

- **Minor:** the empty-criteria check runs after every test has already run. Move it to the top of `run_gates`
  so a bad `readiness.json` fails before any test runs. Do it in the next kit change; it doesn't block anything.

**`gatekeeper` may now run on fixture tickets.**

## B2 config: approved

- **Models:** `gatekeeper` and `scribe` were served by `deepseek-flash` and `triage` by Qwen, so no silent
  fallback.
- **Kanban:** the settings match the plan, `kanban diag` is clean, and `reviewer` is left out of dispatch on
  purpose.
- **Allowlist:** the entries are exact paths with no `git push`, and Hermes's matcher refuses commands that
  contain shell control characters. Add entries one at a time after the dummy-card test, reporting each one.
- **`auto_decompose: true`** can stay while the loader never puts cards in `triage`. If the dummy test shows it
  touching pipeline cards, turn it off.

## Next

**Gateway restart:** on the user's word ("restart").

**Dummy-card test:** answer the two open questions from B0:
1. Does a card claimed by the host runner count against `max_in_progress: 1`?
2. Does `claim` work for a card assigned to `reviewer`, which is outside `dispatch_profiles`?

Also report every approval prompt a worker hits, and leave the board empty afterwards.
