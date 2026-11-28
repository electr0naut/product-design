# FXL-1 block: decision, a harness change (D7), and what runs tonight

**The harness did its job.** The implementer's tests passed the gates, and the cross-lab review still found two
real bugs, both proven by failing tests:
- `8=FIX` inside a field value starts a message;
- a CRLF after the CheckSum breaks the message.

Both are spelled out in technical design section 3 and in FXL-1's own acceptance criteria (AC3, AC5). Nothing
reached the trusted `main`.

**But the block shows a gap in the fix-loop policy.** The one automatic pass was spent on a gate failure (AC8 had
no test). So when the review then proved two bugs, nothing was left, and a ticket that's probably one small fix
away from done waits for a human. A gate failure and a proven bug are different kinds of failure. They shouldn't
share one retry.

## Decision on FXL-1 (as the user's delegate)

**Leave the card blocked. Don't unblock it, and don't edit anything in `work/fix-lens`.** FXL-1 reruns from
scratch in the morning, after D7 is deployed. That keeps the rule: the harness is never changed while a ticket is
in flight.

## Tonight: FXL-3 runs ahead (approved; a reversible board change)

FXL-3 (the dictionary) doesn't depend on FXL-1, and the rest do. Relink FXL-3's `triage` card so it waits on
nothing but the hold card (already done), instead of FXL-2's `scribe`. Use `kanban unlink`/`link`, and log both
commands in the report. FXL-3 then runs against the current trusted `main`, the initial commit, as usual.
- FXL-2 and FXL-4 to FXL-7 stay where they are.
- After FXL-3 lands, FXL-1's old branch has a stale base. That's fine, because FXL-1 reruns from scratch anyway.

Report FXL-3 as `FXL-3.md` plus its patch, as `D6-review.md` says.

## D7: the fix-pass budget per kind (build tonight; the user deploys it in the morning)

1. **One pass per kind.** A ticket gets at most **one gate-triggered pass and one review-triggered pass** per
   attempt, so never more than two, and never two of the same kind. Keep everything else:
   - unproven findings never trigger a pass;
   - mixed findings block;
   - stored proofs are rerun on the retry;
   - a fix pass that touches base tests blocks.
2. **Per attempt:** count passes per `(key, base)`, not per key. Write `base` into each ledger entry, and treat an
   old entry without one as matching any base, which fails safe. A rerun from scratch on a new trusted `main` is a
   new attempt, with its own budget. A rerun on the same base gets no new passes.
3. **Order inside one attempt:** gate pass, then review pass, or the reverse. Both work, because each kind is
   counted separately. Stored proofs from a review pass still have to pass on every later retry.
4. **Tests:**
   - gate pass, then proven findings: a review pass is granted;
   - a second review failure blocks;
   - a second gate failure blocks;
   - never three passes;
   - a new base gets a fresh budget;
   - the same base doesn't;
   - a legacy entry without a base counts against every base;
   - the ledger still fails closed.
5. **Report as `D7-fix-budget.md`.** Push the branch for review; don't merge or deploy it. In the morning, the
   user runs the deploy line, as with D5.

## Morning plan (after the user deploys D7)

Archive FXL-1's cards and reload FXL-1 alone (the loader finds its blockers on the board). It reruns from scratch
on the then-current trusted `main`, with the new budget. FXL-2 and the rest follow in order.

## Small fix to the evidence driver

The cost column in `FXL-1.md`'s model table is empty, and the token columns are shifted by one. Fix the table
formatting.
