# D11 review (`agent-harness` branch `d11-robustness` @ `0ae59d0`)

**Approved. Fast-forward `master` to `0ae59d0`.** Verified in the reviewing session: `356 passed, 3 skipped in
97.48s` (with `-p no:cacheprovider`), and ruff is clean.

- **`run_collect`** keeps the whole output and fails closed over the limit. `collect_ids` is the only parser
  that switched, which matches my audit.
- **One key pattern in `keys.py`,** imported everywhere and enforced at load.
- **A bad card blocks only itself,** the alerts are in place, and the reset is recorded with a required reason.

## Note for later (not blocking)

The alert script lives in `/opt/data/scripts`, which a Hermes worker could edit to silence alerts. Its
counterpart, the runner's own status, is written by the host. Later: have the host runner send the "runner
failed 5 times" alert itself, from host-only code, so a worker can't mute it.

## The user's lines

The pinned-sha lines in `D11-robustness.md` are correct. I'm giving them to the user as written (plain shell,
no `!`). After the deploy: reset FXL-1B with the reason given in `D11-review.md`, then reload, as planned.
