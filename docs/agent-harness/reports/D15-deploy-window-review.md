# D15 deploy window: a hold before FXL-4B

Place `HOLD: D15 deploy` on FXL-4B's `triage` now (approved). FXL-5 keeps running untouched. When FXL-5 lands, I
tell the user to run `harness-deploy 3a0ec24a337de2374c59a52f1ffce993cfa50e96`. After the user confirms, verify that
the runner logs the new sha and a clean decisions pass, then release the hold. That's the last hold you release by
hand: from then on, holds and releases can be decision files.
