# D21: the loader cannot be imported on the deployed kit. Build the fix (instruction)

**Build it.** Stopping was right, and so was not applying it yourself.

Reproduced in the reviewing session on `c06cd27`, each in a fresh process: `import harness.loader` fails with
the circular import you describe, and so do six tools that import the loader first (`load_tickets.py`,
`record_tickets.py`, `review_variant.py`, `seed_fixfail.py`, `seed_js.py`, `seed_risk.py`). Every other module
imports, the runner included. My review of D20 missed this, as the tests did: both imported in an order that
works.

## The change (branch on `c06cd27`, my review, then Ubay deploys)

1. **The fix:** break the cycle `loader` → `pipeline` → `evidence` → `fixloop` → `loader`. Your one-line fix (import
   `fixloop` inside `evidence._passes`) is accepted. If you see a cleaner cut that moves no behaviour, say which
   and why; do not refactor further.
2. **The test that would have caught it:** for **every** module under `src/harness/`, a fresh process runs
   `python -c "import harness.<name>"` and must exit 0. One test per module, so a failure names it. For the tools
   that have a `--help` or a dry run, a fresh process must reach it without an import error.
3. **Also in this change, since it is one line:** remove the emoji from the alert text in `alert.py`.
4. Nothing else. The deploy tool's undo fixes wait for a later change.

Report as `D21-import-fix.md` with the commit, the test output and the dry run of loading FXL-9 to FXL-13 from
the current ticket files.

## After Ubay deploys it

The conditions of `V12-go-review.md` and `V12-go-review2.md` stand unchanged. Run the fixture ticket check, add
it to `V12-live-checks.md`, and load the first batch only if everything holds. The acceptance run of check 2
does not need repeating: the hidden suite was identical at both commits.
