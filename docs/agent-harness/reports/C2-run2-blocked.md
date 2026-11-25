# Phase C run 2: blocked at PRC-3 reviewer (runner failure, not a finding)

Run 2 started 2026-11-25 17:35 CET on a fresh fixture repo (`b13172e`) and a fresh trusted repo, kit `7e99d0e`, planner on Qwen.

## State (18:10 CET)
| Ticket | State |
|---|---|
| PRC-1, PRC-2 | done; trusted `main` advanced in order (`45db90f`, then `6702730`); work repo mirrored |
| PRC-3 | triage..gatekeeper done; **reviewer card blocked** (`transient`) |
| PRC-4 | waiting (needs PRC-2 and PRC-3 scribes) |
| PRC-5 | triage ready, not started |
| PRC-6 | blocked at triage, as intended |

## The block
`reviewer runner failed: $: missing 'findings'`. Qwen's reply for PRC-3 parsed as a JSON object but had no `findings` key, so `validate` raised and the runner blocked the card as `transient`. No finding, refutation or proof exists; `work/runs/PRC-3` has no `review.json`. No Claude spend. By design (one attempt per card) the runner will not retry it.

## Questions for the reviewer (technical, not for the user)
1. The runner discards Qwen's raw reply on a schema failure, so I cannot say what it returned (an empty object, a bare list, or the schema echoed back). I suggest saving the raw reply next to the run files and allowing one automatic re-ask with the validation error before blocking.
2. Is a transient block after one attempt the behaviour you want for a malformed finder reply, or should a malformed reply count as "no findings" (fail open, no) or retry (fail closed)? I have not changed anything.

Nothing was worked around: PRC-3's card stays blocked until you decide.
