# FXL-2B: the fix pass edited `test/helpers.test.js`. Show the diff.

That file came from FXL-1, and tests the helper's BodyLength and CheckSum. Since the helper computed CheckSum over
the raw pipe bytes (the bug FXL-2B fixes, AC4), I expect the old test to assert a pipe-byte CheckSum, and that the
edit corrects it. I need to see it before I approve.

**Put in `FXL-2B.md` (read-only):**
1. the full diff of `test/helpers.test.js` between the attempt's first head and the fix head, with both shas;
2. the fix head's `vitest run` summary in the container;
3. the hidden suite's `acc-check` result on the fix head, if you can run it against a scratch trusted root, as in
   the bake-off.

Then comment on PR #47. I'll answer with an approval or a refusal.

**For later (D14):** a ticket should be able to declare the existing test files it's **expected** to change, as
`may_edit_tests = [...]` in the ticket front matter, written by the ticket writer. A fix pass may then edit
exactly those files without a person. Any other file still blocks. FXL-1B and FXL-2B both needed a person only
because the ticket couldn't say this up front.
