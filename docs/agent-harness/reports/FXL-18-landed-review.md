# FXL-18 landed: review (trusted main `6f2f554`). v1.2 is built.

**Clean. No fix needed.** Loaded through `D-20261127-12` at 16:24, landed at 16:38: fourteen minutes, on the
fallback models throughout (planner `qwen3.7-plus`, implementer `deepseek-v4.1-flash-1017`; the Codex plan was
at its limit), no fix pass, no block. Claude on the review: $0.46.

## What I checked
- **Rebuilt here** from the FXL-16 tree plus the published patch. The patch touches `styles.css` and the new
  `test/styles.test.js`, nothing else. **`styles.css` is byte for byte the rule set I attached to the ticket**,
  which I had checked in a real browser beforehand.
- Hidden suite 173 of 173 (runner). The project's own tests: `264 passed`, and the usual 4 dictionary tests
  fail in my scratch copy for want of the vendored XML.
- **In a real browser, on the landed build** (`fix-lens/browser-check/check16.mjs`, both themes, no problems
  reported; screenshots `fxl18-landed-*.png`): the behaviour checks of FXL-16 all still pass. At 375 pixels
  wide with 60-character ids and symbols, the page does not scroll sideways; the table scrolls inside its box.
  With a filter or an order chosen, the sequence-gap count is no longer green.
- Smallest font size among the new elements: 12.8 px (`.8rem`).

## What this run shows about the harness
- An easy, well-specified ticket went through on the cheapest models without help. The ticket carried a rule
  set that already met every criterion, so this says little about those models on hard work. FXL-16, a hard
  ticket, also came out right on the same fallback implementer; that is one data point, not a pattern.
- The first real `load_tickets` decision worked: no one typed on the VM between my writing the ticket and its
  landing.
- Mutation shows `None` for every count. Correct here (no source file changed), but the evidence should say
  "not run: no source file changed" instead of a row of `None`. Next kit change.

## State of v1.2
Every ticket has landed: FXL-9 to FXL-18. Hidden suite 173 of 173. What is left is not the harness's to do:
1. **Ubay's own test with real logs.**
2. Open with Ubay: a line in design section 15 for the missing-CheckSum position change; the "kill or justify"
   proposal for mutation survivors; the unclassified survivors of FXL-12 (19) and FXL-14 (12).
