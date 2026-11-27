# `be46d02` deployed: the read-only checks (D27-code-review2). **All pass.**

## The deploy
Host kit checked out `be46d0267f4082a3b0a87b9ac4d4c7444bc1d008` at **18:35:51**. The pass before it ended at 18:35:35 on `6ff69fa`; the next began at 18:36:34 on `be46d02`. **No pass spanned the switch.** The board showed no running, ready or blocked card at my checks of 18:32 and 18:42.

## 1. The deployed code
- 178 tracked files: **0 differ** between host and container, and **0 differ** between the host and the commit. Host tree clean; container HEAD and `reviewed-sha` are `be46d02`.
- Fresh-process imports (the package and its modules): **34 of 34** on the host (kit venv) and in the container.
- Tools, in the groups of `tests/test_d21.py`, **host and container:** `--help` exits 0 for **8 of 8**; the 6 load-only ones make their imports; `record_tickets` with no arguments prints its usage. The installed `harness-deploy --help` exits 0. The temporary home stayed empty. (My first host try failed for `deploy.py` because I ran it with `-P`, which hides its neighbouring module; without it, as the tests and the wrapper run it, it passes.)
- **Alert script:** the container's `/opt/data/scripts/harness_notify.py` equals the commit's; the deploy left a backup `harness_notify.py.bak-20261127-183551`. Its state file was rewritten at 18:41, after the switch. **No alert was sent to try it,** so a new message's wording has not been seen arriving.
- The root-installed job files equal the new kit's `jobs/` (all six).

## 2. Runner passes
Six passes on `be46d02` between 18:36:34 and 18:42, all `idle; idle`. No line since 18:35 with skipped, error, traceback or failed. `STATE.md` was rewritten at 18:36:56 with the new commit. No wait file exists (no limit met).

## Open
**The first real usage limit is the real test** of the matcher; I will report its raw `rate_limit_event` and result fields, without prompt text. **Next:** `D27-proposal.md` and the free bake-off.
