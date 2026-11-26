# FXL-8: the edit to `test/dictionary.test.js` is expected; approve on the hidden suite's result

The ticket says this file changes: the dictionaries move from `.json` to `.js` modules, so the reproducibility and
file tests must follow. That makes it a conditional approval, as for FXL-3B.

Run the whole hidden suite against the **fix head** (scratch trusted root, no-network container) and the fix head's
`vitest run` in the container.

- **If** `acc-page` is 5 of 5 (the JSON-import test included), `acc-dictionary` 5 of 5, `acc-render` 5 of 5, nothing
  that passed before fails, and the project suite is green: record the approval for that head and
  `test/dictionary.test.js` with `approve_test_edit.py` (reason: "FXL-8-review: ticket names this file; hidden
  suite 59/59 on the fix head"), unblock the gatekeeper (fix 1) card once, and put the numbers and the head sha in
  `FXL-8.md`.
- **Otherwise:** don't approve. Put the failing hidden tests by name and the diff of `test/dictionary.test.js`
  (first head to fix head) in `FXL-8.md`, and wait.

Always include the fix head's full sha in a block report from now on, so an approval can be a decision file.
