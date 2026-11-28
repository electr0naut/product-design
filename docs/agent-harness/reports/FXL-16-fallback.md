# Why FXL-16's implementer ran on a fallback (FXL-16-landed-review). The planner did too.

Read-only, from the Hermes profile logs. Times are local (+01:00) on 2026-11-27.

## Cause: the Codex plan's usage limit
**Planner** (card 15:29:43 to 15:33:02):
```
15:30:07,327 INFO  Rate-limit backoff level 0: cooldown 6076 s (101.3 min, backoff#1, provider reset)
15:30:07,406 INFO  Fallback activated: gpt-6.2-sol → qwen3.7-plus (alibaba-token-plan)
```
(preceded by a `RateLimitError` warning from `openai-codex` at 15:30:07)

**Implementer** (card 15:33:46 to 15:38:51):
```
15:33:52,880 WARNING API call failed (attempt 1/3) error_type=RateLimitError provider=openai-codex model=gpt-6.2-sol summary=HTTP 429: The usage limit has been reached
15:33:52,882 INFO    Rate-limit backoff level 0: cooldown 5850 s (97.5 min, backoff#1, provider reset)
15:33:52,894 INFO    Fallback to alibaba-token-plan/deepseek-v4.1-flash-1017: attached fallback credential pool
15:33:52,983 INFO    Fallback activated: gpt-6.2-sol → deepseek-v4.1-flash-1017 (alibaba-token-plan)
```
Each went to the **first** entry of its approved fallback list.

## ⚠ FXL-16's plan was mostly written by `qwen3.7-plus`
The planner made calls 1 to 3 on `gpt-6.2-sol` and **calls 4 to 15 on `qwen3.7-plus`** (log lines `API call #4` to `#15`, `model=qwen3.7-plus`). Your review says every other v1.2 ticket ran on the primary and names only the implementer for FXL-16. **The evidence table is why:** `fix-lens/runs/FXL-16.md` shows the planner's session as `gpt-6.2-sol`, 15 calls. It puts a whole session under the model it started with, so **a switch in the middle of a session does not show.** I have not rechecked the other tickets' sessions for such a switch. In today's planner and implementer logs, my search for usage-limit, 429 and backoff lines found only these two events.
**For the next kit change:** the model table should count calls per model actually used (or flag a fallback in the ticket's window).

## The state of the plan's window, as far as the logs show it
- Both cooldowns say `provider reset` and point to the same moment: 15:30:07 + 6076 s and 15:33:52 + 5850 s are both **about 17:11:22**.
- **Not in the logs:** which window it is (short or weekly), how much of it was used, or when it filled. I found no usage percentages or window headers in any profile's log.
- Primary calls before the limit today: implementer 240 (00:42 to 15:15), planner 132 (02:34 to 15:30). Other uses of the same plan outside these profiles would not show here.
- The many `credential pool: no available entries (all exhausted or empty)` lines are **not** the cause: they appear from 12:15 on, at times when primary calls were succeeding. I do not know what they mean.

**For FXL-18:** by the provider's own reset time, a card that starts before about 17:11 should be expected to fall back. I made no model call to test it, and changed no model or fallback list.
