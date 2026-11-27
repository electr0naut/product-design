# D27 part 1: a Claude usage limit waits and retries (D27-go-review)

`agent-harness` branch `d27-claude-limit`, **head `f3268021af09b06b99720da5258d379f02291982`**, on top of `master` `6ff69fa` (rebased onto your approved home fix). **Not merged, not deployed. For your review.** No new credential, no new model.

## What it does
- **A usage or rate limit:** the card is parked with `hermes kanban schedule` (not blocked; no attempt counted). It is retried no sooner than the named reset (plus 60 s), else after 15 minutes, doubling up to 1 hour. A named reset more than 8 days ahead is not believed. A runner pass unparks it when due, parks it again if something readies it early, and forgets the wait if someone else moves the card.
- **Any other Claude failure** (time-out and a program that will not start included): one automatic retry after 5 minutes, then the block of old. The used retry is remembered across a limit.
- **Where you see it:** `STATE.md` gets "waiting for Claude's usage limit since <time>, next try <time>" under the ticket, rewritten at every new try. One alert when a limit wait starts, one when it passes 6 hours. A fault retry sends no alert.
- **Waits are kept on the host** (`claude-waits.json` beside the trusted folder). A corrupt file raises. If parking fails, the pass fails and nothing lands.
- **The review call** now uses `--output-format stream-json --verbose`, to get the limit events.

## What counts as a limit (failed calls only)
| signal | where it comes from | seen for real? |
|---|---|---|
| a `rate_limit_event` with `rate_limit_info.status` = `rejected`; `resetsAt` is epoch seconds | documented type; the unit from real output of 2.1.332 | **The event, yes, only as `allowed`** (my D26 check runs, `five_hour`). **A `rejected` one, never** |
| `api_error_status` = 429 on the result | documentation; the name is in the program file | no |
| a line **beginning** `You've hit your [session, weekly, Opus, Sonnet, fast, monthly spend, individual spend, individual usage] limit` | the documentation's errors page; `hit your ` occurs in the program file | no |
| a line beginning `API Error: Request rejected (429)` or `API Error: Server is temporarily limiting requests` | the errors page; the program file holds both phrases (the second without a fixed `API Error:` before it in the same string) | no |

The documentation was read by a fetch agent (`code.claude.com/docs/en/errors`, `headless`, the SDK reference), not re-read by me. No usage was burned to produce a limit.
- **`overageStatus` is not used:** real **successful** calls here say `overageStatus: "rejected"`.
- A stop at our own `--max-budget-usd` or turn cap is never a limit. Text is searched only on stderr or on a result marked as an error, never in a review's own words.
- **A reset time written only in a message text is not read** (no time zone): the 15-minute steps apply.
- **The risk:** the refused forms are untested against reality. A limit in a form I do not match is treated as a fault: one retry, then today's block. It stops safely.

## Things to judge
- A retry **runs the whole review again** (refute, spec pass, proofs), so it pays again for steps that had succeeded.
- A parked card does not count as running: a deploy is allowed during a wait.
- By the code, the container notifier's 45-minute stall ping counts only ready and running cards, so it stays quiet during a wait; the 6-hour alert covers a long one. `STATE.md` can also go more than 30 minutes without a rewrite during a wait (gaps reach 1 hour, longer before a named reset): the watcher should read the waiting line as expected.
- One real call through the new path succeeded earlier today ($0.0141). The parking with the real board is **not** shown: the tests use a stand-in board.

## Proof (fresh clone at the head, in the proof container; ruff check and format clean)
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
820 passed, 3 skipped in 90.45s (0:01:30)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 283; started without HOME: 0
```
Each rule broken on purpose, `tests/test_d27.py` (all 16 caught):
```
overage status read as the limit: CAUGHT (5 failed, 51 passed in 4.02s)
rejected event ignored: CAUGHT (3 failed, 53 passed in 3.90s)
429 ignored: CAUGHT (1 failed, 55 passed in 3.87s)
model prose searched: CAUGHT (1 failed, 55 passed in 3.90s)
own budget cap treated as a limit: CAUGHT (2 failed, 54 passed in 3.91s)
retries before a named reset: CAUGHT (5 failed, 51 passed in 4.03s)
gap does not stop at an hour: CAUGHT (1 failed, 55 passed in 3.91s)
a second automatic fault retry: CAUGHT (2 failed, 54 passed in 3.92s)
a waiting card is reviewed anyway: CAUGHT (1 failed, 55 passed in 3.96s)
an early-readied card is not re-parked: CAUGHT (2 failed, 54 passed in 3.92s)
never unparked when due: CAUGHT (6 failed, 50 passed in 3.46s)
the attempt is counted: CAUGHT (7 failed, 49 passed in 3.51s)
no six-hour alert: CAUGHT (1 failed, 55 passed in 3.94s)
an alert on every try: CAUGHT (1 failed, 55 passed in 3.88s)
no STATE.md line: CAUGHT (1 failed, 55 passed in 3.91s)
plain json output again: CAUGHT (1 failed, 55 passed in 3.89s)
```
**One gap found this way and closed:** at first, removing the filter that skips waiting cards failed no test. The added test's first version was itself wrong and failed on unchanged code; the results above are from the run after both were fixed.

**Next:** your review. After it is deployed: `D27-proposal.md` and the free bake-off for part 2.
