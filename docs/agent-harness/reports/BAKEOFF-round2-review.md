# Bake-off round 2: a scorer that can tell the models apart

Round 1 is clean work, and your caveat is right: `acc-framing` is saturated, so nine runs tie with Codex and nothing
is ranked. What it does show: `qwen3.8-max` is out (one run of 28 minutes, one timeout), `glm-5.3` is slow and
verbose, and `qwen4-max`, `qwen3.7-max` and `deepseek-v4-pro` are worth a second round.

## Round 2: FXL-5 as first written, scored by the 14 hidden timeline tests

FXL-5 is the ticket where a first pass went wrong in ways the hidden suite now measures: the event `kind` values, a
GapFill losing its SequenceGap, a Logon with 141=Y and no 34, NewSeqNo 0, and the empty-string direction key. A
model that reads the design gets them right; one that guesses doesn't.

- **Candidates:** `qwen4-max`, `qwen3.7-max`, `deepseek-v4-pro`, and `gpt-6-sol` (Codex) as the reference, under the
  same conditions. Two runs each, no fallbacks, throwaway profiles, scratch clones, as in round 1.
- **Ticket:** `FXL-5.md` **as it was before AC11 to AC15 were added** (`git show 25a216c^:docs/agent-harness/fix-lens/tickets/FXL-5.md`).
  The later version spells the edge cases out, which would hide the difference.
- **Base:** the trusted main FXL-5's first attempt started from (FXL-4 landed, FXL-5 not).
- **Design:** readable, at the path the card names, as in the live pipeline now. This is the condition the
  pipeline will run under from here on.
- **Plan:** none. Each candidate plans and implements in one session from the ticket and the design. Say in the
  report if a model can't work that way.
- **Score:** `harness.gates` first time, then the hidden `acc-timeline.test.js` (14 tests) in the no-network
  container, and list the failing tests by name per run. No Claude.

Report as `BAKEOFF-round2.md`: one row per run (gates, timeline tests passed out of 14, failing test names,
minutes, tokens) and one line per model. Don't change the live implementer profile.
