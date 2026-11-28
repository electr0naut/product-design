# Planner and implementer to `gpt-6.2-sol` (user approved, 26 November: "do it")

This follows `MODELS-review.md`. Run that check first; this file applies only to its result.

**If `gpt-6.2-sol` answered through `openai-codex`:**

1. **When:** only at a moment when no planner card and no implementer card is running. Check the board first. If
   one is running, wait for it to finish.
2. **Change:** in the `planner` and `implementer` profiles, the default model `gpt-6-sol` becomes `gpt-6.2-sol`,
   same provider. Nothing else: the fallback lists, the delegation settings and every other profile stay as they
   are. Back up each `config.yaml` first. The diff against each backup must be one line.
3. **Verify:** one tiny call on each profile, and `state.db` shows `gpt-6.2-sol` on `openai-codex` for both. No
   restart unless the change needs one; if it does, say so and do it between cards.
4. **Record** in `D6-morning.md`: old and new values, the two backup paths, the undo (copy the backups back), and
   the check results. Comment on PR #47.

**If `gpt-6.2-sol` did not answer:** change nothing, including not switching to `gpt-6.1-sol`. Report the exact
error and wait.

**Bake-off round 2 is not affected:** leave its runs and its `gpt-6-sol` reference as they are, and name the model
each run used in `BAKEOFF-round2.md`.
