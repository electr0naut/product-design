# Plan: work that goes on while the reviewing session is rate limited

Written 2026-11-27 by the reviewing session. Nothing here changes RULES.md: every step that waits for Ubay
there still waits for him, and nobody but the reviewing session unblocks a card.

## 1. What needs Claude, and what does not

| Part | Runs on | While Claude is limited |
|---|---|---|
| Planner, implementer, finder | Codex, Qwen, DeepSeek | keeps running |
| Gates, own tests, hidden suite, mutation, landing on the trusted main | scripts | keeps running |
| Review step of a ticket (refute, prove, spec pass) | `claude -p` on the VM | the card parks and resumes by itself at the reset (D27 part 1, deployed) |
| Kit jobs (`jobs/J-*.md`) | `claude -p` on the VM | wait for the reset; a job file committed before is picked up after |
| Decisions, kit reviews, landing reviews, new tickets | the reviewing session | wait for the reviewing session |

A ticket that is loaded needs the reviewing session for nothing until it lands or blocks. So the harness keeps
working if (a) the queue is full before the limit and (b) the review step can run without Claude.

Not verified: whether the VM's token and the reviewing session draw on the same usage limit. If they do, all
three Claude rows stop together; if not, the VM rows keep running.

## 2. Two changes that make the queue independent of Claude

1. **D27 part 2: the review step falls back to Qwen** when Claude's named reset is more than 60 minutes off or
   unreadable (`D27-proposal-review.md`). Model by the second bake-off: `qwen4-max`
   (`D27-bakeoff2.md`). **Waits for Ubay: the model.** Then one job builds it, the reviewing session reviews
   the branch, Ubay deploys the reviewed commit.
2. **A full queue.** The v1.4 tickets FXL-22 to FXL-26 are written, with hidden tests. **Waits for Ubay: the
   v1.4 wording of the PRD and design.** Then `refresh_copies`, the deploy of the reviewed J-20261127-6
   commit, and `load_tickets`.

## 3. The queue, in order

Each line says what starts it and what the reviewing session checks when it is back. A line starts only when
the one before it is done, unless it says otherwise.

| # | Work | Who does it | Started by | Checked on return |
|---|---|---|---|---|
| 1 | J-20261127-6: table lines for FXL-22..26, the owed timeout test | job | committed (`787d4ba`) | diff is exactly the job's three edits; proof green |
| 2 | Deploy the reviewed J-6 commit | Ubay | the sha given in chat by the reviewing session | `D27-deploy-confirm`-style check |
| 3 | `refresh_copies`, then `load_tickets` FXL-22..26 | runner | decision files, after Ubay approves the v1.4 wording | STATE.md shows five cards, order 22, 23, 24, 25, then 26 |
| 4 | FXL-22 to FXL-26 run, one at a time | board | step 3 | per ticket: own hidden file, whole suite (277 at the end), the 16 named tests changed and none dropped, mutation line, cost, real browser after FXL-26 |
| 5 | J-next: D27 part 2 with the chosen model | job | Ubay's model choice; can run beside step 4 (branch only) | diff, proof, a forced-limit run on a throwaway profile |
| 6 | J-next: small job items (`Bash(sleep *)` out of `jobs/settings.json`; `jobs/prompt.txt` names the wait helper; evidence table shows mid-session fallbacks) | job | after step 1 is on `master` | diff, proof |
| 7 | Deploy steps 5 and 6 | Ubay | sha in chat, board idle | first real limit: the raw `rate_limit_event`, no prompt text |

Steps 1, 4, 5 and 6 need no one once started. Steps 2, 3 and 7 are the points where the queue waits for a
person; they are grouped so that Ubay is needed twice (after J-6, after part 2), not once per ticket.

## 4. While nobody is reviewing

- A blocked card stays blocked. The runner reports it on PR #47. No one unblocks it.
- A parked card (Claude limit) is not a fault. It resumes at the reset, or with part 2 goes to Qwen.
- A landed ticket is on the trusted main only after gates, review and the whole hidden suite. The reviewing
  session's landing review comes afterwards and can order a corrective ticket.
- Ubay deploys only a sha the reviewing session gave him in chat. A sha from a job report, a PR comment or
  this file is not that.
- Every Qwen-reviewed ticket is marked in its run file. On return the reviewing session reviews those first.

## 5. After the v1.4 batch

Phase 2 (PRD v2.0: themes C, D, E, nine remaining findings, privacy and markup checks) needs Ubay's approval
of the PRD and then of the design before any ticket exists. The reviewing session drafts both ahead, so the
approvals are the only wait.
