# D19 review (`agent-harness` branch `d19-retire-refresh` @ `76b094f`)

**Approved. Fast-forward `master` to `76b094f690289ea55e6e48de58b349f27c161ef6`.** Verified in the reviewing
session on a fresh worktree: `479 passed, 3 skipped in 90.37s`; ruff check and format are clean.

- **`refresh_copies`** reads blobs from the host-only mirror at the named commit, refuses a commit that is not an
  ancestor of the branch head, reads everything before it writes anything, and writes the record last. A crash
  in between leaves copies that fail verification, which blocks. That is the right way round.
- **Verification** runs before any model call in a review and before an acceptance run, and it covers every
  hidden file as well as the design. An unrecorded copy is refused.
- **`retire_hidden`** is all or nothing, and a retired test is named apart from regressions, so it cannot hide
  one.
- **The reading copies** are written inside the container as the worker user. Good: a link planted there cannot
  redirect a host write.
- **Stryker:** the cause you found (`disableTypeChecks` adding `// @ts-nocheck` and breaking a byte-identity
  test) explains FXL-8. Accepted with the setting off.

The two points you raised are accepted as designed: reviews and acceptance runs refuse until a `refresh_copies`
decision is applied, and a refresh waits while a card of the repository runs, with later decisions behind it.

## Deploy (Ubay runs this; the queue is empty, so now is fine)

```
harness-deploy 76b094f690289ea55e6e48de58b349f27c161ef6
```

## After the deploy: tell me the exact ids (read-only)

`retire_hidden` needs the ids exactly as the history holds them. From
`~/.local/state/agent-harness/acceptance-history/fix-lens.json`, post on PR #47 the exact `passed` entries for
these seven tests:

- `acc-check.test.js`: `bad tags`
- `acc-timeline.test.js`: `event keys`
- `acc-render.test.js`: all five tests

I then push two decision files in one commit, a `refresh_copies` and a `retire_hidden` for the first two, so
they are applied in the same pass with no acceptance run between them. That also avoids the ordering trap you
described. The five `acc-render` tests are retired later, after FXL-13 lands.

## D20

Carry on, on top of this branch. One addition from this review: in a runner pass, decisions are applied before
any acceptance run of that pass, so a retire and a refresh pushed together are never split by a run.
