# Model availability check (read-only; change no configuration)

**Lower priority than D18.** Do this when D18 is pushed for review, or while you wait on anything.

Independent leaderboards (Vals AI, 19 and 21 November 2026, one harness for all models) show two newer models
than the ones configured. Before the user decides anything, check whether they are reachable here.

1. **`gpt-6.2-sol` and `gpt-6.1-sol` through the `openai-codex` provider.** On a throwaway profile with no
   fallbacks, as you did for `qwen4-max`: one tiny call each. Report the model and provider recorded in
   `state.db`, or the exact error. Delete the profile.
2. **`deepseek-v4.1-flash-1017` through `alibaba-token-plan`.** Same check.
3. **What `deepseek-flash` resolves to today:** the provider and the model name the provider reports back.

Report the three results in `D6-morning.md` and comment on PR #47. Do not change any profile, fallback list or
cron job. The user decides on any switch after reading the results.
