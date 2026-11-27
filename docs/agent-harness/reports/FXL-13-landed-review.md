# FXL-13 landed: NOT clean. Two of its own hidden tests fail, because of a sentence in my ticket

Trusted `main` `8881fce`, evidence `fix-lens/runs/FXL-13.md`. Rebuilt here from the published patch.

| check | result |
|---|---|
| hidden suite, the runner's isolated run and mine | 121 pass, no regression; **`acc-filters` 6 of 8** |
| the two that fail | `Account keeps whole orders, and a message outside all orders that carries the Account`; `filters combine, and order grouping for Account uses the whole log` |
| the cause | `applyFilters` leaves out every Heartbeat when an Account is chosen, also one that carries the Account. Design section 14 has no such exception |
| where it came from | **my ticket.** FXL-13 AC5 ends "A Heartbeat never passes it". I meant a Heartbeat without the Account. The implementer followed the words, and wrote a test for them (`test_apply_filters_heartbeat_with_matching_account_is_excluded`) |
| everything else, against the independent build | with FXL-13's module in the independent v1.2 build, every other hidden test passes (170 of 172; the two above are the only failures) |
| gates, reviewer, mutation | passed; no finding; 68 killed, 2 survived, 0 static |

The code does what the ticket said and not what the design says. Nothing else is wrong with it.

## What this shows about the harness
**FXL-13 landed and its gate opened with two of its own hidden tests failing.** The acceptance gate only stops a
regression: a hidden test that passed before and fails now. It does not know which hidden tests a ticket is
meant to turn green, so a feature that lands half-right goes through. Only the review caught it.

## What happens now
- **FXL-14 to FXL-16 are not released.** `V12-go-review4.md` makes the release depend on five clean landings,
  and this is not one. It waits for Ubay.
- **A corrective ticket is written, not loaded:** `fix-lens/tickets/FXL-17.md`. Loading it needs Ubay's word.
- **The hidden suite is brought up to date now,** which is in my scope and does not depend on that:
  `D-20261127-6` retires the five `acc-render` tests and `D-20261127-7` refreshes the copies from `9448c0b`
  (the `acc-render` file removed, `acc-framing-rules` added). Confirm on the PR that both were applied and that
  the copies verify: 17 files.
- **Run `tools/rerun_mutation.py FXL-9` now,** while no card is running, and report it.

## Build D24, on a branch from `6c483e6` (in a clone only; no deploy)
**The gate also holds when a ticket's own hidden tests fail.**
- A table in the reviewed host config, per repository: ticket key to the hidden test files that must pass in
  full once that ticket has landed. For `fix-lens`, from `acceptance/README.md`: FXL-14 `acc-presentation`,
  FXL-15 `acc-order-story`, FXL-16 `acc-trades`, FXL-17 `acc-filters`.
- After the isolated run for a ticket in the table: if any test in its files fails or does not run, the gate
  stays shut, exactly as for a regression, and the block report names the files and the counts. A `release`
  decision opens it.
- A ticket not in the table behaves as today. A file named in the table that is not in the host copy is an
  error that keeps the gate shut.
- The evidence says which files were expected and how they did.
- Tests: a ticket whose expected file passes; one with a failing test (held, then released by a decision); a
  missing file; a ticket not in the table.

Report as `D24-expected-hidden.md`. It is deployed only if Ubay says so; the batch does not wait for it.
