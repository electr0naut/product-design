# FXL-4 landed: note F1 is a real bug, so add FXL-4B

The dictionary check came back clean: the independent extraction is identical, and F1 on FXL-3B is a false alarm.

FXL-4's note F1 (unproven) is right, though. With plain-object lookups, an enum value of `constructor` returns
`Object.prototype.constructor` instead of `undefined`, so the decode shows a function instead of
"unknown value". It's pasted input, so it will happen.

1. **The ticket:** `fix-lens/tickets/FXL-4B.md`. It includes a fixed reference message whose BodyLength (35) and
   CheckSum (240) were computed independently. Load it to run **after FXL-5 and before FXL-6.** Reload FXL-6 and
   FXL-7 (unstarted) so they wait on FXL-4B's `scribe`. Don't touch FXL-5.
2. **The hidden suite** has two new tests: one in `acc-decode`, one in `acc-dictionary`. Copy the updated files to
   `~/.local/state/agent-harness/acceptance/fix-lens/`. They'll fail until FXL-4B lands. That's not a regression,
   because they've never passed.
