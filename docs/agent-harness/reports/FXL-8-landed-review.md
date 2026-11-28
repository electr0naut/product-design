# FXL-8 landed: accepted. The page works in a real browser

Checked in the reviewing session on the landed code (trusted main at FXL-7 plus `FXL-8.patch`):

- **Real browser (Chromium, served over HTTP, the page's own CSP):** 6 messages decoded, 7 timeline events, the
  BodyLength error for message 7 shown, no console error, no request to another origin. Screenshot:
  `fix-lens/browser-check/fxl8-landed.png`.
- **Hidden suite:** 59 of 59 here too.
- **Project suite:** 119 of 123 here. The 4 that fail need the vendored Orchestra XML, which my copy does not
  have; your 123 of 123 on the VM stands.

FIX Lens v1.1 is complete: every ticket has landed. Don't load anything new. The next tickets wait for PRD v1.2.

## For the D19 branch: mutation and the data modules

`FXL-8.md` shows `stryker wrote no report (exit 1)`. Mutation is report-only, so nothing was blocked, but the
ticket has no mutation result.
- Leave the `[review] data_modules` paths out of the mutation ranges. There is no logic in them to mutate.
- Find out why Stryker exited 1 here (keep its full output in the run folder, not the last 300 characters), and
  say in the report whether it was the size of those files.

## Noted for a later ticket, not now

F1 (medium, unproven): the page's static check misses a dynamic JSON import that passes a second argument. The
hidden `acc-page` test and the browser check cover the behaviour today. It goes into the v1.2 tickets.

## Next, in this order

1. `HANDOFF-review.md` (now).
2. The bake-off additions (`BAKEOFF-round2-review2.md`) and the round 2 report.
3. D19, then D20.
