# First batch: Ubay's word to start without the alert answer (instruction)

**Ubay Gonzalez, 2026-11-27, in the reviewing session.** Told that the first batch was waiting for his answer
about the 02:02 Telegram alert, "or your word to start without it", he answered: **"start the first batch now,
alert or no alert"**.

That lifts step 3 of `D21-code-review.md`, which was my condition. Whether the alert arrives is still unknown,
so treat it as unconfirmed: it goes on the list for the next kit change, with a second test message that Ubay
confirms.

## Do now
1. Re-check that nothing has changed since your last report: the board has no card for FXL-9 to FXL-16, no
   worker card is running, the kit is `7c190a2` on the host and in the container, the copies verify at
   `ae216b0f82e0` (design `4c2cb3fd5236`, 17 hidden files), and the trusted `main` of `fix-lens` is `e721f31`.
   If anything differs: load nothing, report, and wait.
2. **Load FXL-9 to FXL-13 only,** from the ticket files at `1b47d32` or later (they have not changed since),
   under the conditions of `V12-go-review.md` and `V12-go-review2.md`.
3. Comment on the PR with the card ids and the gate links as loaded: FXL-9 starts at once, and each later
   ticket waits on the gate before it as well as on its own blockers.

## While it runs
- Because the alert is unconfirmed, a stopped runner may be silent. If `STATE.md` has not been rewritten for 30
  minutes while a ticket is in progress, check the runner and comment on the PR.
- On FXL-9's landing, report the two checks of `V12-go-review3.md`.
- Blocks: report them on the PR; routine ones I answer with a decision file. Do not unblock by yourself.
- FXL-14 to FXL-16 follow `V12-go-review4.md`: only on my later go file.
