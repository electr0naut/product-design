# Live-writes audit: accepted. Go on with the fix, then D24 (instruction)

`LIVE-writes-audit.md` is accepted. It answers the question with two kinds of evidence (modification times, and
container runs with every write logged and every file checksummed), and it names its own limits. Stopping D24
until I had read it was right.

**What it establishes.** Today's suites wrote one live file, `runner-status.json`, which the next runner pass
rewrote, and could clear a marker in `alert-state.json` that does not exist on this VM. The acceptance history,
the copies, `pipeline.json`, the records, the ledgers, the outbox and the repositories were not touched. The
delivery state of v1.2 is sound.

**What is left over from 2026-11-25,** not from today: test keys `A-1`, `B-2`, `C-3` in the live `labels.json`,
and the stray repositories `trusted/r.git` and `trusted/repo.git`. They affect nothing that runs. Removing them
is deleting data, so it is Ubay's; I have told him. Leave them.

## Go on, in this order
1. **The fix, as its own commit** (after `a18c096`), as in `LIVE-writes-review.md`, with what the audit adds:
   - the fixture covers `alert-state.json`, the fix ledger, `reviewed-sha` and the mutmut check at collection;
   - the three tool tests that start processes without `HOME` get a temporary one in their environments;
   - the guard test fails if any of the paths in your last table resolves outside the test's temporary folder.
   Prove it the way the audit did: a container run with the write log and the checksums, showing **no** live
   path read or written. Put that output in the report.
2. **Then D24,** as specified.
3. **Suite runs stay in containers** until the fix is deployed, and afterwards too when cards are running: a
   guard is the second line, not the first.

Report both in `D24-expected-hidden.md`, the fix first. I review the two commits apart.
