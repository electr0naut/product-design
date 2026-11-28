# D27: a Claude usage limit must not stop the queue (order for part 1; part 2 waits for Ubay)

**Ubay, 2026-11-27: "will the development ever stop if claude runs out of credits? I want a fallback for
that".**

## What happens today (read from the code at `25a315e`)
The pipeline calls Claude in one place: the review (`reviewer.make_claude`: `claude -p`, model `sonnet`, the
`ubay` subscription login). If that call fails for any reason, a usage limit included, `review_card` blocks the
card as `transient` ("reviewer runner failed: ..."). Nothing retries it ("a transient block retries once" is
still on the backlog). So the ticket waits for an unblock decision, and with one ticket at a time the queue
waits behind it. It stops safely: nothing lands without its review.

## Part 1, build now on a branch after D26 is deployed (no new credential, no new model)
1. **Tell a usage limit from a fault.** From `claude -p`'s JSON result and its stderr: the limit and rate-limit
   forms (say which exact fields and texts you match, from the CLI's documentation and from any real result you
   have in the logs; do not burn usage to produce one).
2. **On a usage limit, the review card is not blocked. It waits and is tried again.** Keep the card where a
   runner pass picks it up again; retry no sooner than the reset time when the result names one, else after 15
   minutes, then with a growing gap up to an hour. No attempt is counted against the card for a limit.
3. **Say so where a person looks:** `STATE.md` gets "waiting for Claude's usage limit since <time>, next try
   <time>" under the ticket, and one alert goes out when a wait starts and one if it lasts more than 6 hours.
   Not one per try.
4. **Any other Claude failure keeps today's block,** and gets the backlog's single automatic retry after 5
   minutes before it blocks.
5. Tests with a stand-in `claude` for each case: limit with a reset time, limit without one, a fault, a limit
   that clears on the second try, a wait longer than 6 hours; and that a waiting card never lands.

## Part 2, do not build yet: what reviews while Claude is out. Ubay chooses
- **A. Only wait** (part 1 alone).
- **B. The same reviewer through a pay-per-use key** when the subscription is at its limit.
- **C. Another lab's model** for the refute and prove steps, marked in the evidence, and not for high-risk
  tickets.
Prepare nothing for B or C until his answer is quoted in a review file.
