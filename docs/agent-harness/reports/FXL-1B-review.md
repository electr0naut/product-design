# FXL-1B block: the gates can't map the criteria to tests

Both attempts failed the gates on `missing_acs` (AC0 to AC3), even though new tests exist, are listed as
`valid_tests`, and fail on the base and pass on the head. The `unmapped` list shows ids that don't match what
`vitest list` prints. One begins `t/framing-f1b...`. The implementer's tests sit inside a `describe(...)`, so their
ids are `file > suite > test`, and `implement.json` names them some other way. The criteria are probably met. The
**mapping** is what fails.

## Check (read-only), then report in `FXL-1B.md`

1. `implement.json`'s `ac_tests` (the ids exactly as written) next to the head's `vitest list` lines for
   `test/framing-f1b.test.js`.
2. Which model ran each stage. Was the planner `gpt-6-sol`?
3. `removed_ids` lists `test/framing-f1.test.js > AC3: ...`. Did the fix pass rename or delete an FXL-1 test? If
   so, say what changed, because that's a base test.

## Decision

- **If it's only the id format:** this is a harness weakness, not a ticket failure. Leave FXL-1B blocked, and add
  to **D11**:
  1. **Resolve criterion test ids robustly.** A listed id resolves when exactly one collected id has the same file
     and the same final test-name segment, whatever the suite segments in between. A typo in the file part still
     fails. Record the resolution in `gates.json`, as `resolve_id` already does. Tests:
     - a `describe`-nested id written without its suite resolves;
     - an ambiguous one doesn't;
     - a wrong file doesn't.
  2. **A recorded reset of an attempt** (`tools/reset_attempt.py KEY --reason "..."`, run on the host by the
     operator after a review file approves it). It writes a `reset` entry to the fix ledger, and passes are
     counted only after the latest reset for that key and base. FXL-1B then reruns from scratch with a fresh
     budget. The reset is visible in the ledger, not hidden. Tests:
     - passes before a reset don't count;
     - passes after it do;
     - a reset needs a reason.

  Then FXL-1B reruns from scratch after the D11 deploy.
- **If the tests don't actually cover AC0 to AC3,** or a base test was weakened: report it, and I'll decide.
  Nothing is unblocked either way.
