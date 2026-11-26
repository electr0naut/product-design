# Implementer on Codex from FXL-2B (approved by the user, 2026-11-26)

**Change (reversible Hermes profile config):** the `implementer` profile's default model becomes `gpt-6-sol`
(openai-codex), with `qwen3.7-plus` then `deepseek-flash` as fallbacks, the same chain the planner uses.

## Timing (never change the harness under a running ticket)

- Make the change **only when no implementer card is running.** FXL-1B's fix pass, if one starts, stays on the
  current model: wait until FXL-1B has landed or blocked.
- If FXL-2B's implementer card is already `ready` when you change it, that's fine, as long as it hasn't started.

## Steps

1. Back up the implementer profile's config, with a timestamp.
2. Set the default model and fallbacks with `hermes -p implementer config set ...`, the same way as the planner.
3. Check with one tiny implementer call that `gpt-6-sol` answers with no fallback (from `state.db`).
4. Find out whether Hermes needs a gateway restart to pick it up. If it does, do the one documented restart, but
   only between tickets.
5. Record the old and new values, plus the undo, in `D6-morning.md`.

## Reporting from now on

For each ticket, include in `FXL-<n>.md`:
- **The implementer's model,** and whether it fell back. A fallback is reported prominently, never silently.
- **Codex usage:** calls, tokens, and any rate-limit messages.
- **For comparison with FXL-1 to FXL-3:** first-attempt gate result, fix passes, spec findings, hidden-suite
  failures.

## Stop rule

If Codex hits a rate limit, let the fallback carry on: the ticket continues on Qwen. Report it. Don't switch
back by hand.
