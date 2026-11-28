+++
key = "FXL-1"
title = "Split a pasted log into messages and parse their fields"
rank = 1
blocked_by = []
labels = []
+++
Set up the project and add `src/framing.js` (pure, no DOM), following the technical design sections 1 to 3.
This ticket only finds messages and splits fields; the malformed rules come in FXL-2.

`package.json` (with the pinned dev dependencies) and `vendor/orchestra/` are already in the repository from the
operator's initial commit; don't change `package.json`. Add `test/helpers/fix.js`, which builds a valid message from a
list of `[tag, value]` pairs, computing BodyLength 9 and CheckSum 10. Tests are top-level `test()` calls in
`test/`.

`splitMessages(text)` returns the message candidates in order of appearance, each
`{ number, start, end, fields }`, where `fields` is a list of `{ tag, value, position }`. `number` is 1-based;
`start`, `end` and `position` are 0-based character offsets into `text`.

Acceptance criteria
- AC1: A message separated by SOH (0x01) and the same message separated by `|` give the same fields. On a line
  that contains SOH, a `|` inside a value (for example `58=a|b`) is ordinary text.
- AC2: Text before `8=FIX` on a line (for example `2026-11-25 10:00:01 IN `) is ignored: the message's `start` is
  the offset of `8=FIX`.
- AC3: `8=FIX` inside another field (`448=FIXCLIENT`, `58=resend 8=FIX.4.2`) never starts a message.
- AC4: Two messages on one line, and two messages on two lines, are both returned as two candidates, in order,
  numbered 1 and 2.
- AC5: A candidate ends after a field that starts with `10=` and 3 digits, followed by the delimiter, a line end
  (`\n`, `\r\n` or `\r`) or the end of the text; `110=100` or `58=x10=123` inside the message don't end it.
  Text after the end on the same line is not part of the message.
- AC6: The empty piece after a message's final delimiter is not a field. Each field has its tag as a number, its value as a string (an empty value stays `""`), and the offset of the
  tag's first character. A repeated tag appears once per occurrence, in order.
- AC7: Text with no `8=FIX` returns an empty list.
- AC8: The helper in `test/helpers/fix.js` produces messages whose BodyLength and CheckSum match the TR-002
  definitions (checked against one hand-computed example).
