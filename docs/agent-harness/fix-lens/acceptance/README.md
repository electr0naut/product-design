# FIX Lens hidden acceptance suite

Written by the reviewer from the PRD v1.1 and technical design v1.1, with FIX reference values computed
independently (Python, CheckSum and BodyLength over SOH). **Never shown to the implementing agents.** Copied to
host-only state and run with `harness.score` against the trusted `main` after every ticket (see `D10-review.md`).

Files for features not built yet fail at import; that is expected. A test that passed once must never fail later.
Each file carries its own small message builder (`fixmsg`), computed over SOH, independent of the product's
helper.

## Baseline (reviewer, 2026-11-26, against FXL-3 + FXL-1 + FXL-2 rebuilt from their patches)

- `acc-framing`: 4 of 9 pass. The failures are the FXL-1 deviations FXL-1b fixes: no `end`, `offset` instead of
  `position`, a prefix with `=` hiding the message, and a candidate without CheckSum dropped.
- `acc-check`: 4 of 9 pass. The failures: CheckSum over pipe bytes (FXL-2b), UTF-8 BodyLength on a pipe line (the
  same CheckSum cause), and a missing or malformed CheckSum not reaching `checkMessage` (FXL-1b).
- `acc-dictionary`: 1 of 4 pass. The argument order is reversed (FXL-3b). Calling it with the current order
  instead, every expected value is right (`SenderCompID`, `Buy`, `ExecutionReport`, `Trade` in 4.4 only,
  `Logon`), which confirms the suite's values against the real Orchestra data.
- `acc-decode`, `acc-timeline`, `acc-limits`, `acc-analyse`: not built yet.

After FXL-1b, FXL-2b and FXL-3b land, `acc-framing`, `acc-check` and `acc-dictionary` should pass in full.
