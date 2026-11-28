# D25 after-deploy step 2: you are right, C now and B later (instruction)

A dry run reads no board, so it cannot show the refusal, and its silence would prove nothing. Thank you for
checking before I relied on it.

- **Now: C.** Step 2 of `D25-code-review2.md` is dropped. Your 15:37 read-only run of the branch code against the
  real board stands as the evidence, together with the tests.
- **Later: B,** in the next kit change: a dry run reads the board and says what a real run would do, refusal
  included. Put it on the list in `HANDOFF.md`.
- **Not A.** A real deploy with a card running, to see whether it refuses, is the thing the refusal exists to
  prevent.

The first real proof comes by itself: the next time Ubay deploys while a card runs, the installed tool refuses
and names it.

Steps 1, 3 and 4 stand. The deploy line is unchanged.
