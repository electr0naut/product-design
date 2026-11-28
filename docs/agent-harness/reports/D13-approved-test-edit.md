# D13: a recorded approval of one fix-pass edit to base tests (FXL-1B-review6.md)

Branch `d13-approved-test-edit` in agent-harness, on top of master `071195d`, at **`8f9f21f8e3cfa8674749810eeec2f7edb7a0f60d`**. Fresh clone: 371 passed, 3 skipped; ruff check and format clean. Not merged, not deployed.

## What changed
- **`tools/approve_test_edit.py KEY --head SHA --files F... --reason "..." [--base SHA | --repo NAME]`** (host, operator). Writes an `approved_test_edit` entry (key, base, head, files, reason, time) to the fix ledger. Base defaults to the trusted `main` of `--repo`. A missing reason, no files, or a base or head that is not a 40-character sha is refused (exit 2), and nothing is written.
- **`fixloop.fix_pass_test_violations`** drops from its list exactly the files approved for the same key, base and head. Another head, another base, another key or another file still blocks.
- **An approval is not a pass:** `passes_used`, `attempt_entries` and `kind_used` skip it (so `e["trigger"]` never meets an entry without one). The evidence driver on `d6-driver` skips it too.
- **Tests** (`tests/test_d13.py`, 7): approved files at the approved head pass; the same files at another head block; another file blocks; another base or key does not match; a missing reason, files or sha is refused and writes nothing; an approval is not a pass; the tool writes the entry with the trusted main as base.

## After the reviewer's approval and the user's `harness-deploy <sha>`
1. `approve_test_edit.py FXL-1B --head 7f47748347ef82ec10c4e5eaba5274a534744abd --files test/framing-f1.test.js test/framing.test.js --reason "FXL-1B-review6: edits remove assertions of FXL-1's prefix bug and follow F3"`
2. Clear the gatekeeper (fix 3) card `t_11abf68b` from `gatekeeper-attempts` (the attempts file, if it is listed).
3. Unblock it once, restart the evidence driver.
