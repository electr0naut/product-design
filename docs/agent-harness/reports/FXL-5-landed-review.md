# FXL-5 landed: name the one hidden timeline test that fails

FXL-5 landed with a clean review and no fix pass. The hidden suite is `acc-timeline` 13 of 14, with no regressions.
(`acc-decode` 4 of 5 and `acc-dictionary` 4 of 5 are the two FXL-4B tests, which is expected.)

**Report in `FXL-5.md`, read-only:**
- the name of the failing `acc-timeline` test;
- its assertion message;
- the actual events it got.

From now on, the driver lists the failing hidden tests by name in every `FXL-<n>.md`, not just the counts.

If it's a timeline bug, I'll add it to the queue as a ticket before FXL-7. If my test is wrong, I'll fix the test.
