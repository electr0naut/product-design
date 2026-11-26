+++
key = "FXL-2B"
title = "Compute CheckSum on SOH, not on the pipe character, with fixed reference vectors"
rank = 2
blocked_by = ["FXL-2", "FXL-1B"]
labels = []
+++
TR-002 says a `|` delimiter is treated as SOH (0x01) **before** any length or checksum calculation. Today both
`checkMessage` and the test helper `test/helpers/fix.js` sum the raw text, so a `|` counts as byte 124 instead of 1.
They agree with each other, so the tests pass, but a real log pasted with `|` (the usual way logs are shown) fails
the CheckSum check, because the sending engine computed it over SOH.

Acceptance criteria
- AC0: A test imports `checkMessage` and `splitMessages` and uses only fixed strings in this ticket (no helper) for
  AC1 to AC3.
- AC1: Reference vector, SOH form: `8=FIX.4.4\x019=20\x0135=0\x0134=1\x0149=A\x0156=B\x0110=125\x01` is valid
  (`checkMessage` returns `null`).
- AC2: The same message with every SOH replaced by `|`, `8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|`, is valid.
- AC3: `8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=095|` (the CheckSum of the raw pipe bytes) is rejected with rule
  `checksum`.
- AC4: `test/helpers/fix.js` computes CheckSum over the text with the delimiter as SOH, whatever delimiter it
  emits; a test checks the helper against AC1 and AC2.
