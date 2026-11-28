# D12 review (`agent-harness` branch `d12-deploy` @ `743819c`)

**Approved. Fast-forward `master` to `743819c`.** Verified in the reviewing session: `363 passed, 3 skipped in
102.57s` (with `-p no:cacheprovider`), and ruff is clean.

- **Safety checks:** sha validation before any command, one `sudo -v`, hardened git flags, and the fast-forward
  check before anything moves. No reset is ever done by the tool itself.
- **The alert script** is copied only when it changed.
- **The wrapper** runs the host kit's copy, and refuses a path under `/srv/lab`.
- **The tests** use injected fake commands.

**Deploy it between tickets:** after FXL-1B lands and before FXL-2B's review starts. The hold-card pattern is
fine, if needed. Comment on PR #47 when FXL-1B lands, and the reviewer gives the user the one install line.
