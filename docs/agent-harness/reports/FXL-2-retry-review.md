# FXL-2: the finder fails twice on the same diff, so switch the finder model for this card

The one retry (run 263) failed again in the finder call, and the attempt rule then blocked the card (run 264).
Two failures on the same prompt, together with the first one's "runaway repetition loop", point to Qwen looping
on this particular review prompt, not to the provider being down (your 09:02 `pong` shows it's up). Retrying
Qwen a third time is likely to fail the same way.

## Decision (as the user's delegate; reversible)

1. **Read the run 263 error, read-only:** a subprocess timeout, a non-zero exit, or the same "Stream cut" in the
   reviewer session. Put one line in `FXL-2.md`. If it's **not** a loop or timeout of the Qwen call (for example
   a harness exception), stop and report instead of doing step 2.
2. **Switch the finder for this one card.** Set the `reviewer` profile's default model to `deepseek-flash`, the
   next model in its own fallback chain, with the same provider settings it already has for that fallback.
   - Record the old value.
   - Remove `t_4d479ff8` from the reviewer attempts file, and unblock it **once**.
   - The refuter and the prover stay on Claude, so the review is still cross-lab.
3. **Afterwards, whatever the result, set the `reviewer` default model back to `qwen3.7-plus`.** Record both
   changes and the revert in `FXL-2.md`, and say which model the finder ran on.
4. **If DeepSeek also fails,** leave the card blocked for the user.

Approved here: one profile config change and its revert. No gateway restart is needed if `hermes -p reviewer`
reads its config on each call. If it does need a restart, stop and report instead.

## Backlog (D10, next harness change)

1. **Retry and fall back.** When the finder call fails or hits the "Stream cut" guard, retry the **next model in
   the profile's fallback chain** once, inside the same runner attempt. Hermes doesn't treat a cut stream as an
   error, so the profile's own fallback never triggers. Record the models tried in `review.json`.
2. **A transient block retries itself once,** after a delay, as `FXL-2-review.md` says.
