+++
key = "FXL-2"
title = "Detect malformed messages and explain them"
rank = 2
blocked_by = ["FXL-1"]
labels = []
+++
Add `checkMessage(candidate, text)` to `src/framing.js`, following technical design section 3 (rules, order,
positions, error text). It returns `null` for a valid message, or
`{ number, position, rule, text }` for a malformed one. `rule` is one of `field_without_equals`, `bad_tag`,
`header_order`, `missing_checksum`, `checksum_format`, `body_length`, `checksum`.

Acceptance criteria
- AC1: A valid message from the test helper gives `null`, with both `|` and SOH delimiters.
- AC2: Each rule is detected on its own: a field with no `=` (including an empty field from `||`); a tag `0`,
  `-5`, `07` or `ab`; fewer than three fields or first three tags not 8, 9, 35; no `10=` field at the end; `10=12`
  or `10=ABC`; a BodyLength that is wrong or not a number; a wrong CheckSum. Each gives its `rule` value.
- AC3: When several rules fail, only the first in the design's order is reported.
- AC4: BodyLength and CheckSum count UTF-8 bytes: a message with a non-ASCII character in tag 58 that is valid by
  bytes passes, and the same message checked by characters would fail.
- AC5: `position` is the 1-based character position in the pasted text of the failing field (for a missing
  CheckSum, the end of the candidate).
- AC6: Every error text has the form `Message N: <problem> at position P`, for example `Message 5: missing
  CheckSum (tag 10) at position 234` and `Message 2: BodyLength (9) says 112, actual 108 at position 12`.
