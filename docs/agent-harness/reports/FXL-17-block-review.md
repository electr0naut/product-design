# FXL-17 block (fix pass edited a base test): the diff, please (instruction)

The same block as FXL-10, and the ticket lists `test/filters.test.js` as expected to change. I approve a named
edit only after reading it.

**Read-only; this comes before the live-writes audit, because the queue is held on it.** Push
`FXL-17-block-diff.md` with, as for FXL-10:
1. why the first gates run failed (its failing items);
2. the fix pass's change to `test/filters.test.js`: the diff from the first gates head to
   `bfb67b789917b5f15fa0cbfdc1b3bffcf76bc1ee`, in full;
3. the whole ticket's diff, base `8881fce` to that head, for `test/filters.test.js` and `src/filters.js`, in full;
4. the other files the fix pass touched, as a `--stat`;
5. the latest gates record's summary, with the mutation line.

**For the next kit change:** a block for "the fix pass edited base tests" should carry items 1 to 4 itself, so
the decision does not need a second round. Add it to the list in `HANDOFF.md`.
