# Budget commit review (`agent-harness` `071195d`, branch `d12-fxl-budget`)

**Approved. Fast-forward `master` to `071195d`.** The change: `[review] max_usd_per_card = 5.0` for `fix-lens`
only, with a config test. The spec budget and the per-call limits are unchanged. The watcher pattern fix is
good too.

The user installs D12 together with this commit, with the line the reviewer gives them. After the user says it's
deployed:
1. remove FXL-1B's reviewer card from the reviewer attempts file, and unblock it **once**;
2. restart the evidence driver;
3. comment on PR #47.

Follow `FXL-1B-review2.md` from there.
