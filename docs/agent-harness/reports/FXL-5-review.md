# FXL-5 blocked: rerun it with the medium findings written into the ticket

**What happened:** the gates passed first time. The first review proved F2 (event `kind`) and F3 (a GapFill lost
its SequenceGap). The fix pass fixed those, and the retry's review then proved the "Logon 141=Y without 34" bug.
That's the second review failure, so the ticket blocked.

**What I learned:**
- **The medium findings were real spec deviations,** but as "notes" they never reached the fix pass: the Logon
  without 34, NewSeqNo 0, the empty-string direction key and kind values.
- **The hidden timeline tests didn't cover them either.** That's my gap as the test writer.

## Decision (as the user's delegate)

1. **The queue is blocked, so nothing is in flight. The user deploys D15 now.**
2. **Then:**
   - copy the updated hidden `acc-timeline.test.js`, which has 5 new tests;
   - reset FXL-5 with the reason "medium spec deviations not fed to the fix pass; ticket now states them as AC11
     to AC15 (FXL-5-review)";
   - archive the FXL-5, FXL-4B, FXL-6 and FXL-7 cards and the D15 hold;
   - reload those four tickets in one call, in this order: FXL-5, FXL-4B, FXL-6, FXL-7, using the **updated**
     `FXL-5.md`, which now has AC11 to AC15.
3. Restart the evidence driver.

## Harness backlog (D16)

On a review-triggered fix pass, include in the fix feedback any **note that carries a verbatim `spec_ref`,** with
its quote. The implementer then fixes spec deviations together with the blocking findings, instead of the next
review promoting one of them to a block.
