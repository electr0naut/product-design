# D23 review (`agent-harness` branch `d23-static-mutants` @ `6c483e6`)

**Approved. Fast-forward `master` to `6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953`.** It contains D22 (`0dee234`).
Verified on a fresh worktree: `598 passed, 3 skipped in 147.85s`; `ruff check` and `ruff format --check` are
clean. I read both commits on top of `0dee234`: the static count with its summary and evidence line, and the
raw report copied beside the rerun's record (a plain file inside the tree only, under a name the record loader
does not read).

**Do not deploy: that is Ubay's, and only when no card is running.** This replaces the deploy line of
`D22-code-review.md`.

## Deploy (Ubay runs this, when I confirm no card is running; the units did not change)

```
harness-deploy 6c483e64d2f0fc26a787f51c7b39cf4c8b2d7953
```

## After the deploy
As in `D22-code-review.md`: confirm the deployed kit, then `tools/rerun_mutation.py FXL-9` and report the counts
and where the raw report was kept. Expect about 187 killed, 70 survived, 2 static (not measured).
