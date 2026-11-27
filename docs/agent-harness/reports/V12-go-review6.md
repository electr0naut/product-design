# Go: load FXL-17, then FXL-14 to FXL-16 (instruction)

**Ubay Gonzalez, 2026-11-27, in the reviewing session.** Given three options after FXL-13 (load FXL-17 and then
FXL-14 to FXL-16, which I recommended; load FXL-14 to FXL-16 first; hold everything), he answered: **"go with
your recommendation, dont stay idle if not absolutely necessary"**.

## Do now, in this order
1. **Finish `tools/rerun_mutation.py FXL-9`** if it is running; it refuses while a card runs, so it comes first.
   Report its counts on the PR. If it has not started, run it now.
2. **Re-check, and load nothing if anything differs:** no worker card is running; the kit is `6c483e6` on the
   host and in the container; the copies verify at `9448c0b99295` (design `4c2cb3fd5236`, 17 hidden files, no
   `acc-render`, `acc-framing-rules` present); the trusted `main` of `fix-lens` is `8881fce`; the board has no
   card for FXL-14 to FXL-17.
3. **Load FXL-17 alone,** from the ticket file at `445c622` or later.
4. **Then load FXL-14, FXL-15 and FXL-16,** in a second call, from the ticket files at `1b47d32` or later.
   FXL-14's triage must wait on `accept FXL-17`.
5. Comment on the PR with the card ids and the gate links.

## While it runs
- As before: report blocks on the PR, do not unblock by yourself, and report each ticket's mutation line.
- The gate does not yet hold on a ticket's own hidden tests (D24 is not deployed), so I check them at each
  landing: `acc-filters` 8 of 8 after FXL-17, `acc-presentation` after FXL-14, `acc-order-story` after FXL-15,
  `acc-trades` after FXL-16.
- Keep building D24 in a clone. It is not deployed while cards run.

## How I read "dont stay idle if not absolutely necessary" (my reading, not his words)
For the rest of v1.2 I act on my own recommendation without waiting, where the work stays inside the approved
PRD and design: loading the tickets already written for it, a corrective ticket like FXL-17, and the tests-only
follow-up for the framing rules. I tell him each time, and he can stop it. **Everything in section 3 of
`RULES.md` still waits for him:** deploys, secrets, new hosts, model changes, deleting data, anything sent
outside, and any change to an approved PRD or design.
