# D25 review, second commit (`d25-runner-actions` @ `5b6c863`)

**Approved. Fast-forward `master` to `5b6c863f6cb4b61d41333d79b32e40276820238a`.** It contains `264c8e4`,
approved in `D25-code-review.md`. Verified on a fresh worktree, in my own container: `674 passed, 3 skipped in
92.56s`; `ruff check` and `ruff format --check` are clean.

The refusal is what was asked: it reads the board after the password prompt and again just before the switch,
names the running card, treats a board it cannot read as a refusal, and has no override. Your read-only run
against the real board (refused, naming FXL-16's implementer) is the evidence I wanted. `D24-deploy-check.md`
is accepted too: the deploy of `b20b702` did no harm.

**Your warning is right and goes to Ubay as it stands:** the deploy that installs D25 is run by the old tool,
which does not refuse. That one is still timed by hand.

## Deploy (Ubay runs this only after my message that the board is idle; the units did not change)

```
harness-deploy 5b6c863f6cb4b61d41333d79b32e40276820238a
```

The idle moment is after FXL-16 lands: nothing is loaded behind it, so the board stays idle until FXL-18 is
loaded, and I will not order that load before the deploy is confirmed.

## After the deploy
1. Confirm the deployed kit as before.
2. `harness-deploy --dry-run` of the same commit with a card running, when one next runs, to see the refusal
   from the installed tool.
3. A `load_tickets` decision that must be refused (a ticket already loaded), to run the new path against the
   real board without loading anything. I send that decision file.
4. The first real `load_tickets` is FXL-18.

D26 waits for Ubay's answer.
