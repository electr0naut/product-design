# D22 review (`agent-harness` branch `d22-mutation-source-text` @ `0dee234`)

**Approved as built: option A. Fast-forward `master` to `0dee234ccbcaa6397c041de8d3969b2edb17baae`. Do not
deploy: that is Ubay's, and only when no card is running.** Verified on a fresh worktree: `589 passed, 3
skipped in 143.33s`; `ruff check` and `ruff format --check` are clean. I read `mutation.py`, `statefile.py`,
`tools/rerun_mutation.py` and the config line.

## Your question: A
No ticket in v1.2 changes only the audit tool, and B does nothing for a mixed change, which is the case FXL-14
may bring. So B would be code for a case nobody has. With A, a tool-only ticket gives a mutation error that
`STATE.md` now names, and mutation stays report-only. Record the limit in `HANDOFF.md`: with the static check
left out, mutants of `tools/audit-source.mjs` always show as without tests, and that number says nothing about
the tool's tests.

## What I checked in the code
- The list is validated before anything is skipped: exact paths, existing test files, no symlink, no `..`.
- The files are moved out for Stryker's run only and put back in a `finally`. The tree is the gate's throwaway
  one and mutation is its last user, so a killed run cannot change what lands.
- The rerun tool takes the range from the host's approval record, checks both commits are on the trusted
  `main`, runs the gate's own function with the gate's changed-line map, and writes only a `mutation-rerun`
  record and its log. It refuses while a card of the repository is running.
- Two accepted limits: the "running card" check is made once, at the start; and the result file is written in
  the container's work folder, where a worker could reach it if one started mid-run. The result is report-only.

## Deploy (Ubay runs this, when I confirm no card is running; the units did not change)

```
harness-deploy 0dee234ccbcaa6397c041de8d3969b2edb17baae
```

The first moment without a running card is after FXL-13 lands, before FXL-14 to FXL-16 are loaded.

## After the deploy
1. Confirm the deployed kit as for D21 (fresh-process import of `harness.mutation`, the tool's `--help`).
2. `tools/rerun_mutation.py FXL-9`. Report the counts, and the survivors in `src/framing.js` with their lines.
   Your trial run showed 72 survivors and 25 mutants without tests there. If the official run is close to
   that, FXL-9's tests are thinner than its green gates suggest, and I will write a follow-up ticket for them.
3. The same for any later ticket whose mutation run errored.
