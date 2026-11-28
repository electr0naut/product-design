# FXL-1B: the fix pass edited base tests. Show me the edit, then I decide.

The review proved findings, and the review-triggered fix pass (Codex) then edited `test/framing-f1.test.js` and
`test/framing.test.js`. Both exist on the base, so the gate blocked for a person, as designed.

My expectation, which I'll confirm from the diff: `test/framing-f1.test.js` came from FXL-1's own fix pass. It
asserts that `8=FIX` after `58=resend ` at the **start of a line with no delimiter** is not a message start. The
design (section 3, step 2) says the opposite: with no delimiter earlier on the line and a non-digit before it,
it **is** a start. If that's what the edit does, then the base test encoded FXL-1's bug, and changing it is
correct.

## Put in `FXL-1B.md` (read-only; change nothing)

1. **The review that triggered the pass** (`review-3.json`): each proven finding's claim, its proof test id, and
   its `spec_ref` if it has one.
2. **The exact diff of the two base test files** between the attempt's first head and the fix head
   (`git diff <first head> <fix head> -- test/framing-f1.test.js test/framing.test.js`), in full.
3. **The fix head's** `vitest run` summary in the container.

Then comment on PR #47. Don't unblock anything. I'll answer with a review file:
- **if the edits only bring the old tests in line with the design,** I approve that edit once, recorded;
- **otherwise** the ticket stays blocked.
