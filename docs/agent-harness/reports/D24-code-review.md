# Review: the test guard (`1007fff`) and D24 (`b20b702`), branch `d24-after-guard`

**Both approved. Fast-forward `master` to `b20b702746f76fc19bedab2d7989714738f6f86a`.** It contains `a18c096`
and `1007fff`. Verified on a fresh worktree at `b20b702`: `635 passed, 3 skipped in 87.93s`; `ruff check` and
`ruff format --check` are clean. I ran that here, in my own container, which has no harness state.

**Do not deploy: that is Ubay's, and only when no card is running.** That is after FXL-16 lands.

## The guard (`a18c096`, `1007fff`)
- `HOME` is a throwaway folder before anything of `harness` is imported, and for every test each `Path` constant
  and function default that points at the home folder or the live kit is moved into the test's own folder. It
  is found by looking, so a path added later is covered, and there is no opt-out.
- `tests/test_isolation.py` fails if one gets out; your control run (the redirect off: 19 of 20 fail) shows the
  tests can fail.
- Your proof is the right kind: a hook in every Python process, checksums, and the same run before the guard
  logging 50 accesses.
- **One limit, accepted:** a path held as a string, not as a `Path`, would not be moved. The `HOME` change still
  covers anything built from the home folder at call time. Keep the rule that suite runs happen in containers.

## D24 (`b20b702`)
- The reason a gate is held is computed in one place (`acceptance.hold_reason`) and used by the pass, the
  evidence, the state file and the `release` decision, so they cannot disagree.
- "In full" counts every result row and the tests a file declares, so a skipped, vanished or unloadable test is
  not a pass.
- An entry without the new field (the tickets already landed) is judged for regressions only.
- **Your question:** a listed file that is not in the host copy stops the run before it starts, and a `release`
  does not open that gate; a `refresh_copies` does. Accepted. It is a mismatch between the config and the
  copy, and it should be fixed, not waved through.

## Deploy (Ubay runs this, when I confirm no card is running; the units did not change)

```
harness-deploy b20b702746f76fc19bedab2d7989714738f6f86a
```

## After the deploy
Confirm the deployed kit as before. FXL-14 and FXL-17 are in the new table and already landed; nothing is
re-judged. The table matters again with the next tickets.

## Next for you
D25, then D26, as in `D25-D26-review.md`. Start D25 now, in a clone and containers only.
