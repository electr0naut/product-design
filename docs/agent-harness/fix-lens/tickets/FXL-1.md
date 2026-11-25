+++
key = "FXL-1"
title = "Split a pasted log into messages and parse their fields"
rank = 1
blocked_by = []
labels = []
+++
Set up the project and add `src/framing.js` (pure, no DOM), following the technical design sections 1 to 3.
This ticket only finds messages and splits fields; the malformed rules come in FXL-2.

Project setup in this ticket: `package.json` (type module, dev dependencies `vitest`, `jsdom`,
`@stryker-mutator/core`, `@stryker-mutator/vitest-runner` 10.x, pinned), `test/helpers/fix.js` (builds a valid
message from a list of `[tag, value]` pairs, computing BodyLength 9 and CheckSum 10). Tests are top-level
`test()` calls in `test/`.

`splitMessages(text)` returns the message candidates in order of appearance, each
`{ number, start, end, fields }`, where `fields` is a list of `{ tag, value, position }`. `number` is 1-based;
`start`, `end` and `position` are 0-based character offsets into `text`.

Acceptance criteria
- AC1: A message separated by SOH (0x01) and the same message separated by `|` give the same fields.
- AC2: Text before `8=FIX` on a line (for example `2026-11-25 10:00:01 IN `) is ignored: the message's `start` is
  the offset of `8=FIX`.
- AC3: Two messages on one line, and two messages on two lines, are both returned as two candidates, in order,
  numbered 1 and 2.
- AC4: A candidate ends just after the delimiter that follows `10=` and 3 digits; text after it on the same line
  is not part of the message.
- AC5: Each field has its tag as a number, its value as a string (an empty value stays `""`), and the offset of the
  tag's first character. A repeated tag appears once per occurrence, in order.
- AC6: Text with no `8=FIX` returns an empty list.
- AC7: The helper in `test/helpers/fix.js` produces messages whose BodyLength and CheckSum match the TR-002
  definitions (checked against one hand-computed example).
