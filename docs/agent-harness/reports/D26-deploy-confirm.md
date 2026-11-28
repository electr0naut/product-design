# `25a315e` deployed: the three checks before Ubay's setup (D26-code-review2). **All pass.**

Read-only.

## The deploy
Host kit checked out `25a315e` at **17:20:14**; container copy fast-forwarded the same second. No card started or completed since 17:00, and none is running, ready or blocked. The runner pass before it ended at 17:19:21; the next began at 17:20:19. **No pass spanned the switch.**

## 1. The deployed kit
- 176 tracked files, **0 differ** between host and container; host tree clean; `reviewed-sha` is `25a315e`.
- Fresh-process imports: **32 of 32** with each interpreter.
- `--help`: **8 of 8** in each, for the 8 tools that have it; the installed `harness-deploy --help` works. The other 7 tools have no `--help`: on the host, the 6 load-only ones make all their imports in a fresh process with a throwaway home (nothing written there), and `record_tickets` with no arguments prints its usage. The load-only check was not repeated in the container.
- **Nothing of D26 is switched on:** no `/var/lib/harness-jobs`, signing file, signer list, proof `pytest` folder, proof timer or job timer.

## 2. Runner passes
Passes at 17:20:19 (done 17:20:44) and 17:21:24 (done 17:21:33) both log `25a315e` and `idle; idle`. Since the switch: **no line with "skipped"**, none with error, traceback or failed; nothing from the alert unit.

## 3. `D-20261127-13`
The PR comment (17:21:28 local), verbatim:
> `rejected D-20261127-13: already loaded, so nothing was loaded: FXL-18 [commit 20c36153415c, 2026-11-27T16:20:28+00:00, signature: present, not checked (no key list)]`

The commit is the one that added the file (`20c36153415c126a703cbb3f1260de687d09a11e`, author `Claude`). The ledger records the same commit, time and signature state. Nothing was loaded (12 registry entries as before; no card) and the publishing outbox is empty.

**In advance of your step-6 decision,** read-only with the switch off: D-13's commit **verifies** against the key line of setup step 6, using the deployed kit's own check.
