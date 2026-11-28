# Implementer fallback: `qwen4-max` in place of `qwen3.7-plus` (approved by the user, 2026-11-26)

Change the `implementer` profile's fallback chain to `gpt-6-sol`, then `qwen4-max`, then `deepseek-flash`. The
default model stays `gpt-6-sol`.

- Do it **when no implementer card is running** (between tickets, or while FXL-8 waits on its gate).
- Back up the profile config, change only the fallback list, and verify with one tiny call that the default still
  answers on `gpt-6-sol`. Check `qwen4-max` is reachable through the configured provider with one tiny call on a
  throwaway profile, as in the bake-off.
- Record the old and new values and the undo in `D6-morning.md`, and comment on PR #47.
