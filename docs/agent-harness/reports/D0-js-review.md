# D0 review: JavaScript test support (`agent-harness@e0789e5`)

**Approved. Start D1.** Verified in the reviewing session: `141 passed in 50.63s`, ruff and the format check are
clean.

- **Vitest over `node --test`** is the right call, and the evidence for it is in the report: `node --test` has no
  list-only mode and no distinct "no tests" exit.
- **Moving the pytest assumptions into config** keeps every Python default, so the 122 earlier tests pass
  unchanged.
- **`{name_re}` is anchored and escaped**, so `-t` can't select the wrong test by a partial match.
- **Proof outcomes are tested with real Vitest JUnit files.** Syntax, import and timeout failures don't count as
  proof, and the skipped cases of a filtered run are ignored. Exactly one real case is still required.
- **Everything ran in the container,** and nothing was written to the host-only state folder or to Hermes.

## One fix, as the first commit of D1

**The prover can write through the `node_modules` symlink.** `Runner.prove` links `deps_dir` into the
**scratch** worktree, the one where the Claude prover has Write and Edit. A prompt-injected diff could steer the
prover into editing `node_modules/vitest/...` through that link. That would change the shared dependencies for
every later gate run and proof, for example making a failing test report a pass.
- The prover never runs anything in the scratch worktree, so it doesn't need the link. Link `deps_dir` only into
  the **clean** worktree, where the copied test runs.
- **Test:** the scratch worktree has no `node_modules`, and the clean one does.

## Hardening: make the shared dependencies read-only to workers

The tests that the gates run in the container can also write through the link, the same way Python tests can
already write into `.venv-container`. That's an existing weakness, which JS now shares.
- Make `work/js-deps/` and `.venv-container/` not writable by the container's `hermes` user. That's a reversible
  change, so it's approved here.
- **Then check:** the gates, a proof and the scoring still run for both fixtures.
- **If it needs `sudo`:** that's a stop for the user, because the agent can't do it alone. Write it down and
  carry on with D1 meanwhile.

## For D2 (risk tiers)

Treat test-runner and dependency config as high-risk by default, because a change there can quietly change what
"pass" means:
- `package.json` and `package-lock.json`;
- `vitest.config.*`;
- `conftest.py`;
- `pyproject.toml`.

## Accepted limits

- **Variants are Python-only.** J1 was checked through the hidden tests, not the variant runner. Add JS variants
  when D1's tests need them.
- **A ticket that changes `package.json` needs a re-install by hand.** For FIX Lens, put all dependencies in the
  first ticket.
- **The model-written JS proof and the live JS card text are untested.** The first FIX Lens ticket exercises them;
  watch that one closely.
