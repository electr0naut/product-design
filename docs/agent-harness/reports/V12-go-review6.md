# Go: load FXL-17, then FXL-14 to FXL-16 (instruction)

**Ubay Gonzalez, 2026-11-27, in the reviewing session.** Given three options after FXL-13 (load FXL-17 and then
FXL-14 to FXL-16, which I recommended; load FXL-14 to FXL-16 first; hold everything), he answered: **"go with
your recommendation, dont stay idle if not absolutely necessary"**.

## Do now, in this order
1. **Finish `tools/rerun_mutation.py FXL-9`** if it is running; it refuses while a card runs, so it comes first.
   Report its counts on the PR. If it has not started, run it now.
2. **Re-check, and load nothing if anything differs:** no worker card is running; the kit is `6c483e6` on the
   host and in the container; the copies verify at `23952fd05985` (design `023e2adfdb09`, 17 hidden files, no
   `acc-render`, `acc-framing-rules` present) once `D-20261127-8` is applied, see below; the trusted `main` of `fix-lens` is `8881fce`; the board has no
   card for FXL-14 to FXL-17.
3. **Load FXL-17 alone,** from the ticket file at `445c622` or later.
4. **Then load FXL-14, FXL-15 and FXL-16,** in a second call, from the ticket files as they are on the branch
   now. Their last changes are `1b47d32` (FXL-14), `ab1db50` (FXL-15) and `7afa4d1` (FXL-16); those are the
   expected commits, not a reason to stop. FXL-14's triage must wait on `accept FXL-17`.
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

## Added 13:16 UTC: design v1.2.2 and `D-20261127-8`
Ubay approved one clarification of section 13 (his word: "A"; quoted in the design's status line and in
`acceptance/README.md`). It is on Confluence as v1.2.2 and in the repo at `23952fd`. It changes no code: FXL-12
already does it. `D-20261127-8` refreshes the copies from that commit: the design copy, and one more test in
`acc-summary.test.js`.
- **If you have not loaded FXL-17 yet:** wait for the runner to apply `D-20261127-8`, check that the copies
  verify at `23952fd05985` with design `023e2adfdb09`, then load as above.
- **If FXL-17 is already loaded:** do not stop it. Say so on the PR, with the time the decision was applied and
  which card was running then.
