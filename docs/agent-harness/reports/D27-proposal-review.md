# D27 part 2: review of the proposal and of the first bake-off

Read: `D27-proposal.md`, `D27-bakeoff.md`. I did not rerun the bake-off or read the raw replies.

## Your two questions
1. **When to switch: with a threshold.** If the limit's named reset is 60 minutes away or less, wait for
   Claude. If it is further off, or no reset time can be read, switch. The number goes in config.
2. **The second bake-off, on the spec pass and prove: yes, start it.** It is inside what I may order (free,
   throwaway profiles, nothing live). Same rules as the first: no `fallback_providers`, every session checked
   for the model it ran on, profiles deleted at the end. Cases: FXL-1 and FXL-1B (proven bugs) and at least
   four clean reviews from v1.2. Report, per model: which proven bugs the spec pass found, what it reported on
   the clean ones, whether the prove step's test fails for the right reason on the buggy state and passes on
   the fixed one, malformed answers, time, and every tool call. The hidden acceptance tests never go into a
   prompt or a pack.

## On the proposal
- **Agreed:** the review starts again from the first Claude step, one reviewer per review; a new profile with
  no fallbacks; high-tier tickets wait for Claude; any fault waits for Claude and lands nothing; the model of
  each API call decides independence, and a ticket waits where that cannot be established; the fallback is
  named in `review.json`, the evidence, `STATE.md` and the landing comment.
- **Tools:** try for a session with no tool at all first, and say in the build report what Hermes allows. If
  the to-do list and the tool search cannot be removed, the check you propose stands: read the session, and
  any other tool message discards the answer.
- **The size limit of the spec pass:** name the number in the build report, with the largest prompt the
  bake-off sent.
- **A direct provider call:** not now, as you say. It would be a new handling of a credential, which waits
  for Ubay.

## On the bake-off
- It supports `qwen4-max` over `qwen3.7-plus` for the refute step: same verdict as Claude on 30 of 32, no
  change on repeat, a worst call of 90 s against 358 s, and eligible on FXL-16 where `qwen3.7-plus` is not.
- It does not settle the choice. Refuting is the easy step; three of FXL-1B's four proven bugs came from the
  spec pass. All three models refuted three findings I called true, so agreement with Claude is not the same
  as being right.
- I will bring the model to Ubay after the second bake-off, not before. Part 2 is not built until he answers.
