# Phase B6 review

**Results accepted, code not yet reviewable.**

## Blocking: the security fix commit is not on GitHub

The report cites `agent-harness@28153d3`, but `electr0naut/agent-harness` `master` is still at `de03aab`. Neither
`git ls-remote` nor a fetch of `28153d3` finds it, so the two B5 security fixes exist only on the VM:
- proofs run in the container;
- run-folder files are validated.

Push it, check with `git ls-remote origin` that `master` points at the new commit, then post the sha. Until I've
reviewed that code, treat the host runner as **not cleared for real (non-fixture) repositories**. The fixture
runs already done are fine.

## Results

| Measure | Target (DESIGN §12) | Result |
|---|---|---|
| Review recall on seeded bugs | ≥ 5/6 | **6/6** (4 proven by a failing test, 2 blocking-unproven) |
| False blocks on clean variants | 0/4 | **0/4** |
| Claude spend | — | about $1.94 for 6 reviews, about $0.32 each |

That's a strong result for the review design. The cross-lab refuter upheld every real bug, and the clean code
produced no findings at all.

## Two things to look at

1. **B3 and B5 weren't proven, but both bugs are easy to test.**
   - B3 is a currency mismatch that is silently allowed; the proving test is `Money(1,"USD") + Money(1,"EUR")`
     expecting `CurrencyMismatch`.
   - B5 is a class-level dict shared between `PriceList` objects; the proving test builds two lists and checks
     that they don't share prices.

   Since the fix, the prover has no Bash and writes tests blind. Read its `could_not_prove_because` for B3 and
   B5 in `work/runs/VAR-B3/` and `VAR-B5/proofs.json`. If the cause is that it can't run its own test, consider
   one in-container dry run that the runner performs and feeds back once, so Claude can fix a broken import
   before the real proof run. Report the reasons first; don't change anything yet.
2. **False blocks were only measured on easy cases.** Qwen raised no findings on the clean variants, so the
   refute and prove steps never had to reject a false finding. Phase C on real tickets will show whether false
   findings get through. Keep counting them there.

## Pending user items

- Telegram: confirm that the PRC-6 alert arrived, and decide on the noise (the B5 review suggests problems plus
  one "done" message per ticket).
- The 03:00 CET backup run tonight is the first real test of the fixed script and the new redaction. Check it
  in the morning.

## Next

1. Push `28153d3`. I'll review it.
2. Then Phase C: load PRC-1 to PRC-6 together on a fresh fixture repo, score with the hidden tests (target
   22/22), and report per-ticket cost, time and model. Expected: PRC-1 to PRC-5 merge in dependency order and
   PRC-6 bounces. The planner can use Codex after its reset at 2026-11-26 08:21 CET, so you could also wait
   for that.
