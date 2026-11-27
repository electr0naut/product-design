# FXL-14 landed: reviewed, clean

Trusted `main` `ee91fe2`, evidence `fix-lens/runs/FXL-14.md`. Rebuilt here from the published patch. No fix pass,
no block, no reviewer finding. (I expected a block on AC15, a criterion that asks for no change; the implementer
gave it a test that fails on the old page, so the gates passed first time.)

| check | result |
|---|---|
| hidden suite, the runner's isolated run and mine | **149 of 173**, no regression |
| the ticket's own hidden file | **`acc-presentation` 21 of 21** |
| the project's own tests | 222 pass (the 4 dictionary tests fail here for want of the vendored XML, as before) |
| real browser over HTTP, light and dark (`browser-check/check14.mjs`, `session.log`) | 12 messages in all four delimiter forms: 5 counts in the strip (12 messages, 11 valid, 1 malformed, 1 sequence gap, 2 orders), 12 timeline rows with all four row classes, 12 cards, the malformed one at its place; no console error, no dialog, no `<img>` from the pasted markup, no request to another origin; no horizontal scroll at 1280 or at 390 wide |
| the theme button | starts from the system setting; one click sets `theme-dark` on `<html>`, changes the page background and its own text to `Light theme` |
| opened as a file from disk | the page shows `FIX Lens did not start. Open it through a web server, not as a file from disk.` and the tool stays hidden (AC-024) |
| the CSP | unchanged and first in `<head>` |

Screenshots: `browser-check/fxl14-landed-light.png`, `fxl14-landed-dark.png`.

**Mutation:** 227 killed, 12 survived, 2 without tests, 4 static (not measured). I have not classified the 12.
From their text, four are optional-chaining guards around `matchMedia` in `src/main.js`, which only matter in a
browser without it; the others are in `render.js`. They go on the list for the mutation-driven fix pass.

**FXL-14 counts as landed clean.**
