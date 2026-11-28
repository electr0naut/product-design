# D4 review: the live JavaScript run (`agent-harness@47c65fa`)

**Approved.** Verified in the reviewing session: `262 passed, 3 skipped in 74.30s`, and ruff is clean.

- **JSN-1 and JSN-2 ran end to end with no stage played by hand:** 9/9 hidden tests and a baseline of 11/11,
  with the trusted `main` advanced only by the pipeline.
- **The JSEED-1 failure was the useful kind.** A Python-shaped prover prompt produced an unusable proof. The
  id and path checks refused it, and the unproven finding blocked instead of starting a fix pass. That's the
  fail-closed behaviour we designed. The fix takes the folder and the id format from the overlay, and it has a
  test.
- **JSEED-2:** the bug was proven, fixed in one pass, the stored proof passed and the ticket completed. The JS
  proof path works live.
- **The `.gitignore` detail** (no trailing slash, so the `node_modules` symlink is ignored) was a good catch.
- **Stopping when auto mode refused the deploy** was right, and so was moving the work off the live tree.

## Answers

1. **One live JS proof run is enough to start the pilot.** The first FIX Lens reviews are the second run. I'll
   read their `proofs.json` closely.
2. **Mutation time:** keep `time_cap_s = 300`. A capped run reports `incomplete`, which is fine for a
   report-only field. If FIX Lens tickets often hit the cap, we'll tune Stryker's per-mutant timeout then, not
   now.

## The live tree is also your working tree

The failed runner tick at 23:43 confirms what the D3.1 review describes: the code the host runs and the code you
edit are the same folder. D5 is what fixes it. Until it's deployed, don't edit `/srv/lab/agent-harness` with
uncommitted work. Use a separate clone, or a branch checked out in another worktree outside `/srv/lab`.

## D5: push for review, don't deploy yet

**Push only the `d5-host-kit` branch** to `agent-harness`. Don't merge it into `master`, and don't run the deploy
tool or touch the unit. Then post the commit on PR #47. I'll review the code first, and the deploy follows that
review. Write `D5-host-kit.md` with:
- what the deploy tool does, step by step;
- the exact unit file it would install;
- the one-line `sudo` command for the container kit, with its undo;
- the test count and outputs.

If auto mode refuses the push as well, stop there. The user approves it in the morning.
