# Phase C stall review (from the agent's chat report; no report file has been pushed yet)

## The hole is real, and it starts earlier than `advance_main`

PRC-5 depends only on PRC-1, but its branch was built on top of `harness/PRC-3`. The likely cause:
- the implementer is *told* to "create branch harness/<KEY> from main";
- the fixture repo's working tree was still on `harness/PRC-3`;
- so the LLM's `git checkout -b` forked from the current HEAD.

Branch creation is left to model instructions, and nothing deterministic checks it. As a result:
- **gates and review** for PRC-5 ran on a diff that also contained PRC-3's code;
- **`advance_main`** then moved `main` over PRC-3's unapproved commit.

The fix belongs in three places, all deterministic. Write a test for each:
1. **Gates:** fail if `git merge-base <base> <head>` is not `<base>`. Also fail if any commit in `base..head` is
   reachable from another `harness/*` or `variant/*` branch (`git branch --contains <commit>`). The second
   check catches a branch stacked on another ticket's work.
2. **`advance_main`:** require `base.txt` to equal the current `main` before fast-forwarding. If it doesn't,
   block `needs_input`. With check 1, `main` can then only move over the ticket's own reviewed commits.
3. **Implementer card text:** have it run `git checkout -B harness/<KEY> <main-sha>`, using the sha it wrote
   to `base.txt`, never a bare `checkout -b`. That's a backstop only; checks 1 and 2 are what enforce it.

## PRC-3: decide on evidence, not by default

"False block" needs proof before the card is unblocked. From `work/runs/PRC-3/review.json`, report, with no code
pasted:
- the finding (severity, confidence, claim);
- the refuter's verdict and reason;
- the proof result (`proven` true, false or null) and its `note`.

Then apply the matching rule:
- **The prover's test passed** (`proven: false`) **and the card still blocked:** that's a bug in `decide`,
  which should have made it a note. Fix it with a test. Option 3 is then just this bug fix.
- **The refuter said `stands`, there's no proof (`null`), and confidence is at least 80:** that's
  `blocking_unproven`, working as designed. The user reads the finding. If it's wrong, unblock it (option 1)
  and **count it as a false block** in the results.

## How to finish Phase C

This run is contaminated: `main` holds unreviewed PRC-3 code, and PRC-5 was gated and reviewed on a mixed diff.
**Don't score it as the Phase C result.**
1. Record what happened in a report, `C1-stall.md`: cards, findings, costs, and the hole. It's useful evidence.
2. Fix the three checks above, plus `decide` if the evidence shows a bug. Push them, and I'll review.
3. Re-run Phase C **from a fresh fixture repo**. The cost is small: about $0.02 of DeepSeek plus a few dollars of
   Claude, and about an hour.

**Recommendation to the user:** option 2 for this run (stop and record it, don't unblock), then fix and rerun.
Yes, fix `advance_main`, but together with the gate and branch checks, and **before** the rerun, not after.
Also leave the repo on `main` after each ticket.
