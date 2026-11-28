# FXL-17 landed: reviewed, clean

Trusted `main` `bfb67b7`, evidence `fix-lens/runs/FXL-17.md`. Rebuilt here from the published patch.

| check | result |
|---|---|
| hidden suite, the runner's isolated run and mine | **130 of 173**, no regression |
| the ticket's own hidden file | **`acc-filters` 8 of 8** |
| the tests added since FXL-13 | `acc-framing-rules` 11 of 11; `acc-summary` 18 of 18, with the v1.2.2 test |
| the change | one line in `src/filters.js`, as the ticket asks; the replaced test and three new ones |
| the block | one, for the fix pass's test edit; approved after reading the diff (`D-20261127-9`), unblocked once (`D-20261127-10`) |
| mutation, the first run on the D22 and D23 kit | 6 killed, 0 survived, 0 static; the static check left out as configured |

The Heartbeat exception that came from my wording of FXL-13 is gone. FXL-13 and FXL-17 together are what the
design asks for.

**A note on my own tickets.** FXL-10 and FXL-17 each lost a fix pass and a block to a criterion that says
"everything else passes unchanged". The gates need a test that fails before the change, and such a criterion
cannot have one. FXL-14's AC15 is of that kind and is already loaded, so the same block is likely there. In
later tickets that statement goes in the text, not in a numbered criterion.
