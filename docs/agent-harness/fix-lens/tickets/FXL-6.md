+++
key = "FXL-6"
title = "Refuse logs over the size limits"
rank = 6
blocked_by = ["FXL-1"]
labels = []
+++
Add `src/limits.js`, following technical design section 4: `checkLimits(text)` returns
`{ ok, bytes, messages, warning }`. `analyse()`, which calls it first, comes in FXL-7.

Acceptance criteria
- AC0: A test imports `checkLimits` from `src/limits.js` and checks its result has exactly the keys `ok`,
  `bytes`, `messages`, `warning`.
- AC1: Bytes are measured as UTF-8 (`TextEncoder`): a paste of exactly 1,048,576 bytes is accepted and 1,048,577 is
  refused; a paste with multi-byte characters is measured in bytes, not characters.
- AC2: The message count is the number of candidates from `splitMessages`: 1,000 is accepted, 1,001 is refused.
- AC3: A refused paste gives `ok: false`, the measured bytes and count, and a warning that states both numbers and
  suggests splitting the log into smaller chunks.
- AC4: An accepted paste gives `ok: true` with the measured numbers and no warning.
