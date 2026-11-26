+++
key = "FXL-1b"
title = "Make splitMessages match FXL-1's interface and the design's boundary rules"
rank = 2
blocked_by = ["FXL-1", "FXL-2"]
labels = []
+++
FXL-1 landed with deviations from its ticket and technical design section 3. Fix them in `src/framing.js`,
keeping every existing test that still applies, and keep whatever FXL-2 added.

Acceptance criteria
- AC0: A test imports `splitMessages` and checks each candidate has exactly the keys `number`, `start`, `end`,
  `fields`, and each field exactly `tag`, `value`, `position` (FXL-1's interface; today `end` is missing and the
  field key is `offset`). Every caller in `src/` and `test/` uses `position`.
- AC1: A prefix that contains `=` before `8=FIX` on a line (for example `session=ABC 8=FIX.4.4|...`) does not
  hide the message: a candidate starts at `8=FIX` when the character before it is not a digit and the line
  before it contains no delimiter (design section 3, step 2). `58=resend 8=FIX.4.2` inside a delimited message
  still never starts one.
- AC2: A candidate with no CheckSum is still returned (it ends where the next candidate starts or at the line
  end), so FXL-2 can report it; if FXL-2 already did this, a test proves it.
- AC3: Inside a candidate that has not reached its CheckSum, `8=FIX` right after a delimiter starts a new
  candidate: `8=FIX.4.4|9=5|35=0|8=FIX.4.4|9=5|35=0|10=123|` gives two candidates, the first without CheckSum.
