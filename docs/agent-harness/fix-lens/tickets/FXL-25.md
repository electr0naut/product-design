+++
key = "FXL-25"
title = "Messages with single-byte text outside ASCII are valid"
rank = 25
blocked_by = []
labels = []
+++
A paste holds characters, not the bytes that were on the wire. Many FIX links send accented text in ISO-8859-1,
one byte per character, so the BodyLength and CheckSum of such a message were computed with `é` as one byte,
0xE9. The tool counts UTF-8 bytes, where `é` is two, and called these messages malformed. From v1.4 they are
valid (PRD v1.4 TR-002; technical design v1.4 section 3, step 7).

The rule. When rule 5 (BodyLength) or rule 6 (CheckSum) of step 8 fails with the UTF-8 count, and the candidate
holds at least one character from U+0080 to U+00FF and no character above U+00FF, both rules are checked once
more with every character counted as one byte whose value is its code point. When both hold that way, the
message is valid. Otherwise the error of the UTF-8 count is reported, exactly as today. A message whose counts
hold in UTF-8 is valid as today. Nothing on the page says which count held. Windows-1252 text (a euro sign,
curly quotes) is not covered.

`src/framing.js` and `test/framing.test.js` are expected to change. No existing test is expected to change; if
one fails, stop and say which in the handoff. `test/helpers/fix.js` builds UTF-8 messages only; a test of this
ticket computes the single-byte BodyLength and CheckSum itself, or uses the fixed lines below.

Reference lines (the `|` form):

- single-byte counts: `8=FIX.4.4|9=57|35=D|49=CLI|56=BRK|34=1|11=A1|55=ABC|54=1|38=100|58=café|10=031|`
- UTF-8 counts: `8=FIX.4.4|9=58|35=D|49=CLI|56=BRK|34=1|11=A1|55=ABC|54=1|38=100|58=café|10=163|`

Acceptance criteria
- AC0: `splitMessages` and `checkMessage` keep their signatures, and `analyse(text)` its shape.
- AC1: `analyse` of the single-byte reference line gives no error and one decoded message whose Text (58) is
  `café`, the characters as pasted.
- AC2: `analyse` of the UTF-8 reference line gives no error, as today. Both lines in one paste give two decoded
  messages and no error.
- AC3: The same holds for every delimiter form: the SOH character, `|`, `^A` and `<SOH>`.
- AC4: Both rules must hold with the same count. The single-byte line with its CheckSum replaced by `10=163`
  gives the error `Message 1: BodyLength (9) says 57, actual 58 at position 11`. The UTF-8 line with its
  CheckSum replaced by `10=031` gives `Message 1: CheckSum mismatch at position 73`.
- AC5: When neither count holds, the UTF-8 error is reported unchanged. The single-byte line with `58=cafés`
  in place of `58=café` (9 and 10 as they were) gives `Message 1: BodyLength (9) says 57, actual 59 at position
  11`.
- AC6: A character above U+00FF switches the second check off. A line built like the single-byte one, with
  `58=café€` and with 9 and 10 computed as if each character were one byte, is malformed, with the UTF-8
  BodyLength error (`says 58, actual 61`).
- AC7: Every character from U+0080 to U+00FF counts with its own value: a message built with one byte per
  character is valid for U+0080, U+00A0, U+00E9 and U+00FF in a value.
- AC8: The second check never touches a neighbour: in a paste of a valid ASCII message, a single-byte message
  and a malformed message, the three get the same verdicts as each alone, and the positions in the error do
  not move.
- AC9: A fill whose Text holds single-byte accented characters is counted in the trading summary like any
  other fill.
