# FIX Lens hidden acceptance suite

Written by the reviewer from the PRD v1.1 and technical design v1.1, with FIX reference values computed
independently (Python, CheckSum and BodyLength over SOH). **Never shown to the implementing agents.** Copied to
host-only state and run with `harness.score` against the trusted `main` after every ticket (see `D10-review.md`).

Files for features not built yet fail at import; that is expected. A test that passed once must never fail later.
Each file carries its own small message builder (`fixmsg`), computed over SOH, independent of the product's
helper.
