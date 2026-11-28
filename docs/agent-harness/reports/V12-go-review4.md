# FXL-14 to FXL-16: Ubay's yes to release them overnight, and how it will be done (instruction)

**Ubay Gonzalez, 2026-11-27, in the reviewing session.** Asked "may I release FXL-14 to FXL-16 overnight if the
first five all land clean? Without a yes I stop after FXL-13 and wait for you", he answered: **"yes release"**.

This does not load anything now, and it does not answer step 3 of `D21-code-review.md`: the first batch still
waits for his line about the 02:02 alert.

## What "land clean" means
All of these, for each of FXL-9 to FXL-13:
- the ticket is finished and its `accept` gate was completed by the runner;
- the isolated hidden-suite run shows no regression;
- no block or hold is open, and no card was unblocked more than once;
- I have reviewed the landing and said so in a review file.

If any one of them does not hold, the release does not happen and it waits for Ubay.

## The order, when they have all landed clean
1. I push, in one commit: `retire_hidden` for the five `acc-render` ids, the removal of `acc-render.test.js`
   from the acceptance folder, and `refresh_copies` naming that same commit.
2. You confirm on the PR that both decisions were applied and that the copies verify.
3. I push the go for FXL-14 to FXL-16 as a review file. **Load them only on that file,** from ticket commit
   `1b47d32` or later, not on this one.
