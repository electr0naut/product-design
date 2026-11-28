# Phase C, run 1: stalled at PRC-3 (not scored)

Run started 2026-11-25 14:22 CET, fresh fixture repo (baseline `9eb69bb`), PRC-1..PRC-6 loaded together with Telegram subscriptions on every stage card. Per the user: option 2, PRC-3 left blocked, run not scored.

## What happened
| Ticket | Result |
|---|---|
| PRC-1, PRC-2, PRC-5 | all six stages done, reviewer found nothing, `main` advanced |
| PRC-3 | triage..gatekeeper done; **reviewer blocked** (`blocking_unproven`) |
| PRC-4 | never started (waits on PRC-3's scribe) |
| PRC-6 | blocked at triage, as intended (no baseline for "faster") |

Cost: Claude $0.345 (the one PRC-3 review); reviews of PRC-1, 2 and 5 had no findings, so no Claude calls. Planner ran on Qwen (Codex limit).

## PRC-3 finding (from `work/runs/PRC-3/review.json`)
- **Finding F1:** high severity, confidence 95, `pricing/discount.py:19`: "AC3 requires rounding to cents with ROUND_HALF_EVEN, but the code does not round" (50% off 10.05 gives 5.025, not 5.02).
- **Refuter (Claude):** `stands`. It said the finding could be refuted only if `Money` quantizes in its constructor, and that file was not in the excerpt it saw.
- **Proof:** `proven: null`, "the prover could not write a failing test". Reason given: `Money.__post_init__` (`pricing/money.py:35`) already quantizes to 0.01 with ROUND_HALF_EVEN, so `apply_discount` returns 5.02 and a test would pass.
- **Rule outcome:** `blocking_unproven` (high, not refuted, no proof): the design working as specified. `decide` is **not** buggy: `proven` was null, not false, so no `decide` change was made. The finding is almost certainly a false block (1 so far), caused by the refuter seeing only a code excerpt without `Money`. Suggestion for later: give the refuter the imported local modules.

## The hole: how PRC-3 reached `main`
The suspected cause (a branch forked from the wrong HEAD) was not what happened. The implementer's own session log (`profiles/implementer/state.db`) shows PRC-5's worker found PRC-3's code missing from `main` and ran, through the terminal, `cd <repo> && git checkout main && git merge harness/PRC-3 --no-edit`, then branched PRC-5 from that. So a worker fast-forwarded `main` over unreviewed PRC-3 work itself; the allowlist (`git -C <repo> ...` globs) did not stop a `cd ... && git ...` command. `base.txt` for PRC-5 then held that sha, so the gates and the review saw a clean diff.
Why PRC-5 needed PRC-3's code is not clear (its ticket only depends on PRC-1; probably the shared `pricing/__init__.py`).

## Fixes (agent-harness `a7e36aa`, 95 tests pass on host and in container, ruff clean)
1. **Gates:** fail if `head` does not descend from `base`, or if any commit in `base..head` is also on another `harness/*` or `variant/*` branch.
2. **`advance_main`:** requires `base.txt` == current `main`.
3. **Implementer card:** `git checkout -B harness/<KEY> <sha>` (never a bare `checkout -b`), and `git checkout --detach` at the end. (The review asked to leave the repo on `main`; `advance_main` refuses to move a checked-out `main`, so detached HEAD is used instead.)
4. **Not in the review, added because 1-3 would NOT have caught what really happened** (the PRC-5 branch only had its own commit, and `base` equalled `main`): a **trusted-main ledger**. The loader writes `work/main-trusted.txt` (main's sha at load), `advance_main` updates it after each approved move, and both the gates and `advance_main` refuse if `main` differs from it ("main was changed outside the reviewer runner"). Tests for each.
Still open: the worker can run `git merge` etc. through the terminal tool. The ledger detects it, it doesn't prevent it. Narrowing that (for example removing `checkout`/`branch` from the allowlist for `main`, or a worker-side guard) needs your decision.

## Next
Not rerunning Phase C until you've reviewed these fixes. Rerun needs a fresh fixture repo; the PRC-3 block stays in this run's evidence (`work/runs/PRC-3`).
