# FXL-1B, attempt 3 (Codex implementer): the gates pass first time, then the Qwen finder times out

**A good sign for Codex.** The gates passed on the first try, on the full test list, with no fix pass. On Qwen,
attempts 1 and 2 both failed the gates or needed a fix pass first.

**The block isn't about the code.** The Qwen finder call timed out after 900 s. That's the third time Qwen has
stalled reviewing a `framing.js` diff (FXL-2 twice, now FXL-1B), and DeepSeek reviewed FXL-2 without trouble.

## Decision (as the user's delegate; reversible)

1. **Make `deepseek-flash` the `reviewer` (finder) profile's default for the rest of the pilot,** with
   `qwen3.7-plus` as its fallback.
   - Back up the config, verify with one tiny call, and restart only if Hermes needs it.
   - Record the change and the undo in `D6-morning.md`.
   - The refuter, the prover and the spec pass stay on Claude, so the review stays cross-lab.
2. **Clear FXL-1B's reviewer card from the attempts file, and unblock it once.** This is a transient retry, not a
   fix pass.
3. **Record the finder model in each `FXL-<n>.md`** from now on, as for the other stages.

## For D13 (after the pilot)

When the finder call fails (non-zero exit, a timeout, or a "Stream cut" reply), retry **once** on the next model
in the profile's chain, inside the same runner attempt. Record the models tried in `review.json`. A
person shouldn't have to switch models by hand.
