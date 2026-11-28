# Implementer fallback chain: `deepseek-v4.1-flash-1017` first (Ubay approved)

**Approval (RULES section 1 and 3).** The reviewing session recommended, on 2026-11-26 after
`BAKEOFF-round2.md`: "make the implementer's fallback chain `deepseek-v4.1-flash-1017`, then `qwen4-max`, then
`deepseek-flash`", and asked Ubay to say yes. Ubay answered the same day: "agreed on all points."

**Change, in the `implementer` profile only:**

- default model: unchanged (`gpt-6.2-sol`, `openai-codex`);
- fallbacks, in order: `deepseek-v4.1-flash-1017` (`alibaba-token-plan`), `qwen4-max` (`alibaba-token-plan`),
  `deepseek-flash` (`deepseek`).

Follow RULES section 5: only while no implementer card runs; back up `config.yaml`; the diff against the backup
is only the fallback list; one small call on the profile still answers on `gpt-6.2-sol`; record old value, new
value and undo in `HANDOFF.md` (the "Models now" line) and comment on PR #47. Nothing else changes: not the
delegation settings, not any other profile, not the finder.

A live failover is still untested. Don't provoke one.

## Also noted from `BAKEOFF-round2.md`

Accepted. `deepseek-v4-pro` and `qwen3.7-max` are out. Round 2 cannot rank the four models that scored 14 of 14.
