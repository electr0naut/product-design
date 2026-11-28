+++
key = "FXL-19"
title = "Raise the limits to 10,485,760 bytes and 10,000 messages"
rank = 19
blocked_by = []
labels = []
+++
The largest log the tool accepts goes from 1,048,576 bytes and 1,000 messages to 10,485,760 bytes and 10,000
messages (PRD v1.3 AC-016 and TR-005; technical design v1.3 sections 4 and 9). Only the two numbers in
`src/limits.js` change. How a text is measured (UTF-8 bytes, and the message candidates of design section 3),
the four keys of `checkLimits`, the wording of the warning and what `analyse` returns over a limit all stay as
they are.

`src/limits.js`, `test/limits.test.js`, `test/analyse.test.js`, `test/render.test.js` and a new file
`test/performance.test.js` are expected to change in this ticket. The existing tests that pin the old limits
move to the new numbers: in `test/limits.test.js` every test that carries 1,048,575, 1,048,576 or 1,048,577
bytes or 1,000 or 1,001 candidates (the multi-byte test and the `toBeLessThan(1048576)` line included); in
`test/analyse.test.js` and in `test/render.test.js` the one test each that builds a refused text with
`'x'.repeat(1048577)`. The new tests of AC0 to AC3 go into `test/limits.test.js` and `test/analyse.test.js`. No
other existing test changes. The timing tests that exist today, at 100 and at 1,000 messages, stay as they are.

Nothing on the page changes in this ticket. Until FXL-21 adds paging, a log of several thousand messages is
drawn whole and slowly; do not add paging here.

Large texts are cheap to build: `'x'.repeat(n)` has `n` bytes, and one short valid message repeated `n` times
has `n` candidates. The valid messages of the performance tests come from `test/helpers/fix.js`, joined by
`\n`. The counts a performance test expects (order groups, summary rows, messages that pass a filter) follow
from how the test builds its log; work them out from that, not from the code's answer.

Acceptance criteria
- AC0: `checkLimits(text)` in `src/limits.js` still returns exactly `ok`, `bytes`, `messages` and `warning`. A
  text of 1,048,577 bytes and a text of 1,001 message candidates, both refused until now, give `ok` true and
  `warning` `null`.
- AC1: The size limit is 10,485,760 UTF-8 bytes, inclusive. A text of exactly 10,485,760 bytes is accepted. A
  text of 10,485,761 bytes is refused. Bytes are counted, not characters: 10,485,759 times `x` followed by one
  `é` is 10,485,761 bytes and is refused. A refused text gives `ok` false and the warning `Log has <bytes>
  bytes and <messages> message candidates; split the log into smaller chunks.` with the two measured numbers.
- AC2: The count limit is 10,000 message candidates, inclusive. 10,000 candidates are accepted. 10,001
  candidates are refused, also when the text is far below the size limit, with the same warning.
- AC3: `analyse` follows the new limits. A log of 10,000 valid messages gives `ok` true, 10,000 decoded
  messages and no errors. A log of 10,001 valid messages gives `ok` false, `limit` equal to
  `checkLimits(text)`, and empty `messages`, `errors`, `decoded` and `timeline`.
- AC4: Performance at the new size (design section 9). A test in `test/performance.test.js` builds a log of
  10,000 valid messages that mixes new orders (35=D), execution reports with fills (35=8) and heartbeats
  (35=0), on at least two pairs of SenderCompID and TargetCompID. `analyse` finishes in under 5 seconds, and
  `orderGroups(decoded)`, `tradeSummary(decoded)` and `applyFilters(decoded, chosen)` with one filter set each
  finish in under 1 second. The test also checks that each answer is the right one for the log it built (the
  number of decoded messages, of order groups, of summary rows and of messages that pass the filter), so it
  never times an empty answer.
- AC5: A second test builds 10,000 valid messages padded with a long Text (58) value in each (about 900 to 990
  characters, depending on the other fields), so that the log is between 10,400,000 and 10,485,760 bytes.
  `analyse` gives `ok` true with 10,000 decoded messages and no errors, in under 5 seconds.
