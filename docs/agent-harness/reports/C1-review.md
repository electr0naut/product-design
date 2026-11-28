# Phase C run 1 review (`agent-harness@a7e36aa`)

Verified in the reviewing session: `95 passed in 47.67s`, and ruff is clean. Good investigation work: the log
showed the real cause, which my guess got wrong.

## What the stall really showed

1. **A worker merged unreviewed code into `main` on its own initiative.** The PRC-5 implementer ran
   `git checkout main && git merge harness/PRC-3`. Nothing stopped it, because Hermes's `command_allowlist`
   isn't a list of permitted commands: it only exempts commands that Hermes classes as *dangerous*. Plain
   `git merge` is not dangerous to Hermes, so it ran without any approval. **Treat every worker as able to
   run any ordinary command in the container.** The container boundary is the real control, not the
   allowlist.
2. **PRC-3 was blocked wrongly, for a clear reason.** The refuter saw only an excerpt of `discount.py`, not
   `Money`, which already rounds half-even. The prover was right that no failing test exists. Count it:
   **1 false block**, on real tickets.

## Fixes in a7e36aa

- **Approved:** `check_lineage` (the branch must fork from its base, with no commits shared with another
  ticket's branch) and `advance_main` requiring base == `main`. Correct, and tested.
- **Not sufficient: the trusted-main ledger.**
  - **Workers can rewrite it.** `work/main-trusted.txt` lives in `/srv/lab`, which the container can write. A
    worker that can merge into `main` can also update the ledger.
  - **It fails open.** `check_trusted_main` and `advance_main` skip the check if the file is missing, or if
    `work_dir` isn't set. Deleting the file disables it.

## Required before the rerun: keep the trusted `main` outside the container's reach

Don't try to stop workers from running git. Make their copy of `main` irrelevant:

1. **A trusted repo the container can't see.** Create a bare repository at a host-only path, not under
   `/srv/lab` or `/srv/hermes`: `~/.local/state/agent-harness/trusted/<repo>.git`. Its `main` is the only
   `main` that counts. Only the host reviewer runner writes to it.
2. **Approving a ticket** (`advance_main`) means:
   - fetch `harness/<KEY>` from the work repo into the trusted repo;
   - check `merge-base --is-ancestor <trusted main> <branch>` and base == trusted main;
   - run `update-ref refs/heads/main <branch> <old trusted main>`;
   - then copy `main` back into the work repo (`update-ref` there too), so workers start from it.
3. **Every ticket starts from the trusted `main`.** Before work starts on a ticket, the host side resets the
   work repo's `main` to the trusted `main`. Either the loader does this at load time, or the runner does it
   after each approval. The gates check that `base` is the trusted `main`. The gates run in the container
   and can only *read* it, so the runner stores a copy of the trusted sha in the run folder, and
   `advance_main` re-checks against the real trusted repo anyway.
4. **Fail closed.** A missing trusted repo, or a missing `work_dir`, is an error, never a skip.
5. **Scoring.** The hidden tests run against the **trusted** `main`.
6. **Tests:**
   - a worker-style merge into the work repo's `main` changes nothing in the trusted repo, and the next
     ticket's gates refuse the stale base;
   - deleting the copied sha file makes the gates fail, not skip;
   - the happy path still advances `main` in order.

Remove the `work/main-trusted.txt` ledger once this replaces it.

## Recommended, and cheap: give the refuter context

The false block came from missing context, not a wrong rule. Run the refute call with `--tools Read`, its
working directory set to a clean worktree of head (under `work/prove/`), and an instruction to read the files
the finding's file imports. Reading files executes nothing, so the "no code runs on the host" rule still
holds.

Test it by re-running the review of the contaminated PRC-3 card on a fresh variant-style branch, as PRC-3's
own reference module plus the implementer's code. It should now be refuted, or be a note.

## Implementer card text

Add this line: "Never check out, merge into, reset or otherwise change `main`. If you need code from
another ticket, stop and call kanban_block." It isn't a control on its own, but it stops a well-meaning
model from trying.

## Next

Make the trusted-repo change and the refuter change, plus the card line, with tests. Push, then I review.
Then rerun Phase C from a fresh fixture repo **and** a fresh trusted repo.
