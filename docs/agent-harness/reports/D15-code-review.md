# D15 review (`agent-harness` branch `d15-decisions` @ `3a0ec24`)

**Approved. Fast-forward `master` to `3a0ec24`.** Verified in the reviewing session: `400 passed, 3 skipped in
85.90s`, and ruff is clean.
- **The fetch:** into a host-only bare repo, with `GIT_SAFE` plus `protocol.ext.allow=never`, never checked out.
  Files are read by id, in order.
- **Validation and replay:** strict parsing, a whitelist of actions, wrong-state cards rejected, and applied ids
  kept in host-only state.
- **The rules:** each action reuses the D11 and D13 functions.

## The driver limit: fix it now (operator tooling, no deploy needed)

The evidence driver must **not exit on a block**. On a block, it writes the evidence and comments, then keeps
polling the board. It picks up again when the card moves on: after an `unblock_once` applied by the runner, or a
release. Otherwise every decision still needs someone to restart the driver, which defeats D15. Restart the
driver once with that change.

## Deploy

Between tickets: after FXL-5 lands, or when the queue is blocked. The user runs:

```
harness-deploy 3a0ec24a337de2374c59a52f1ffce993cfa50e96
```

From then on, my routine decisions are files under `docs/agent-harness/decisions/`. Prose review files stay for
building harness changes and for explaining decisions.
