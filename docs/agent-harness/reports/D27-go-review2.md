# D27 part 2: Ubay chose C, another lab's model reviews while Claude is at its limit

**Ubay, 2026-11-27, in answer to the three options of `D27-go-review.md` (A only wait, B the same reviewer
through a pay-per-use key, C another lab's model): "C".** What I had put to him for C, and so what is approved:
a Qwen model does the review while Claude is out, it is marked in the evidence, and high-risk tickets still
wait for Claude.

Part 1 (wait and retry on a usage limit) stands and comes first. Part 2 builds on it.

## The rules of the fallback
1. **Only on a usage limit,** as part 1 detects it. Never on a fault, a timeout or a budget stop, and never to
   save cost.
2. **Not for the high tier.** A high-tier ticket waits for Claude (part 1).
3. **The fallback must be independent of this ticket's other models.** It may not be the model that found the
   findings, nor any model that planned or implemented this ticket, **counting the models actually used**, a
   mid-session fallback included (`FXL-16-fallback.md`). If no Qwen model is left that meets this, the ticket
   waits for Claude.
4. **It replaces the Claude steps one for one** (the spec pass, refute, prove), with the same schemas, the same
   read-only reach for refuting and the same confinement for proving. A result that does not fit the schema is
   a fault, and the card waits for Claude; it does not land on a malformed review.
5. **It is visible:** the evidence file, `STATE.md` and the landing comment say "reviewed on the fallback
   model <name>, Claude at its usage limit since <time>". I review those landings first.
6. **No new credential and no new host:** the existing Alibaba token plan. No change to any live profile's
   model or fallback list. If the fallback needs a profile of its own, it is a new one, named in the deploy
   note so that Ubay sees it before he deploys.

## Before building: a short proposal and a bake-off (throwaway profile only)
- **Proposal** (`D27-proposal.md`, one page): how the three steps run on a Qwen model with the same reach and
  confinement as the `claude -p` calls have today, and what cannot be made equal.
- **Bake-off, free, on recorded cases, nothing live:** replay the findings of past reviews from the records
  (all of FXL-9 to FXL-18, and the earlier tickets where a review led to a fix pass) through `qwen4-max` and
  `qwen3.7-plus`. For each finding compare the verdict with Claude's recorded one and with what happened (my
  landing reviews say which findings were wrong: all five of FXL-16, for one). Report, per model: agreements,
  findings it would have let through that Claude stopped, findings it would have blocked that Claude cleared,
  malformed answers, and time per call.
- **The model is not chosen yet.** I put the bake-off result to Ubay with a recommendation; the model's name
  goes live only with his answer quoted.

Build order: part 1, review, deploy; then the proposal and the bake-off; then part 2.
