# C2 review: run 2 blocked on a malformed finder reply

Good stop: the runner blocked instead of treating the reply as "no findings", and nothing was worked round.

## Likely cause (check it when you save the raw reply)

The finder prompt pastes the findings **JSON Schema** into the prompt, and `parse_json_object` returns the
**first** balanced `{...}` in the reply. If Qwen restates the schema, or adds any example object before its
answer, the parser picks that object: `{"type": "object", ...}` has no `findings` key. That fits the error.

## Decisions (answers to your two questions)

1. **A malformed reply never counts as "no findings".** That would fail open, so a broken model reply would
   approve code.
2. **Fix, with tests:**
   - **Parsing:** walk *all* balanced JSON objects in the reply and take the first that **validates** against
     the findings schema. Skip anything that doesn't.
   - **Save the raw reply:** write it to `work/runs/<KEY>/find-raw-<n>.txt` for every attempt.
   - **One re-ask:** if nothing in the reply validates, ask Qwen once more, quoting the validation error and
     "reply with only the JSON object, no schema, no prose". If the second reply also fails, block the card as
     `transient`, as today.

     The re-ask happens inside the same runner attempt, so the one-attempt-per-card rule stays as it is. It
     costs no Claude: Qwen is on the token plan.
   - **Tests:**
     - a reply with the schema echoed first and the real answer second parses the answer;
     - a reply with no valid object triggers exactly one re-ask, and then blocks;
     - the raw replies are written for both attempts.

## Continue run 2 (approved; the user approved Phase C, and this is a technical fix inside it)

After the fix is pushed with its tests:
1. Clear PRC-3's reviewer card from `work/reviewer-attempts.json`, and unblock the card so the runner picks it up
   again.
2. Let run 2 continue. Don't restart it: PRC-1 and PRC-2 are valid, and the trusted `main` is clean.
3. Post the kit commit on PR #47. I'll review the code while the run continues. If I find a problem, we decide
   whether the affected review needs repeating.

Report in the final run-2 report: what the raw reply actually contained, and whether the re-ask was needed.
