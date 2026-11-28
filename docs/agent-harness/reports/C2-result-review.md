# Phase C run 2 review

**Close to the target, and the safety checks worked.** 19/22 hidden tests pass, and all 19 are on code that went
through the full pipeline and was approved into the trusted `main` in order (PRC-1, PRC-2, PRC-3, PRC-4).
PRC-5's 3 tests are missing only because approval *correctly refused* a stale base. The baseline is 22/22,
with 0 false blocks. The three mid-run fixes are fine:
- `9b497cb`: the finder's first reply was confirmed to be an echoed schema, so taking the first object that
  validates was the right fix;
- `632bdc7`: the gatekeeper card text;
- `bd64da6`: per-file scoring that counts modules it can't import as failures.

## Design answer: stale base, so serialize tickets (option b)

The goal is tickets delivered **one by one, in order**. `max_in_progress: 1` limits *cards*, not *tickets*, so the
stages of PRC-4 and PRC-5 interleaved. The work was still serial, so interleaving bought no speed. It only
created stale bases. Serializing tickets therefore costs almost no wall time.

- **Loader:** in queue order, chain every ticket's first card (`triage`) to the **last card (`scribe`) of the
  previous ticket**, in addition to its `blocked_by` parents. A ticket then starts only after the previous one
  has finished, so its base is always the current trusted `main`.
- **Blocked tickets:** a blocked ticket now holds the queue. That's intended: the user's flow is "in order".
  For PRC-6-style triage bounces, the loader may chain later tickets to a bounced ticket's *triage* card
  instead, so a vague ticket doesn't hold up good ones that don't depend on it. Implement it like this:
  - chain to the previous ticket's `scribe` card if a later ticket `blocked_by` it;
  - otherwise chain to its `triage` card, which still keeps the order, because a ticket that passes triage
    completes before the next one starts its own triage.

  Tests:
  - two independent tickets never overlap;
  - a triage-bounced ticket doesn't block an independent later one;
  - a dependent ticket waits for its blocker's `scribe` card.
- Rebasing on the host (option a) adds a merge step that would need review. Don't add it.

**Finish run 2:** re-run **PRC-5 only**, from the current trusted `main`, after archiving its cards. Then score.
The expected result is 22/22. That's the Phase C result.

## Other items

1. **The finder ran code.** The `reviewer` profile used its terminal tool (`verify_ac.py`) during a review. The
   finder should only read the diff. Disable terminal and file-writing tools for the `reviewer` profile. Find
   the profile's toolset setting with `hermes config` or the docs, and report what you set. That keeps the
   finder read-only, like the Claude refuter.
2. **Gatekeeper reliability.** The gatekeeper is meant to be mechanical, yet a model has to copy a command
   exactly, and today's stray-dot block shows that's fragile. Move the gate run into deterministic code:
   - **either** run the gates from the host runner, as the reviewer runner does, but inside the container
     through `prove_cmd`-style `docker exec`;
   - **or** make it a Hermes no-agent script.

   This can come after Phase C.
3. **Weak test.** In `test_gatekeeper_command_has_no_stray_trailing_argument`, the second assert is always
   true (`or "--report" in body`). Assert the exact command string instead.
4. **The report needs** the models per stage and the DeepSeek cost, read from the per-profile `state.db` (a
   small read-only extraction script), so the final Phase C report and the Confluence page can state them.

## Next

Make the serialization change and the reviewer-profile tool restriction, with tests. Push, then re-run PRC-5
and score. Then write `C2-final.md`: the score, a per-ticket table including models and cost, and the totals
against DESIGN section 12.
