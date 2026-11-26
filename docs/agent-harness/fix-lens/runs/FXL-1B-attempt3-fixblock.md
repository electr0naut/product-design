# FXL-1B: BLOCKED for a human

## FXL-1B · gatekeeper (fix 3) (t_11abf68b) is blocked
```
  [2026-11-26 19:15] default: BLOCKED: FXL-1B: the fix pass edited or deleted tests that exist on base (test/framing-f1.test.js, test/framing.test.js); a person must decide

Events (7):
  [2026-11-26 19:10] created {'assignee': 'gatekeeper', 'status': 'todo', 'parents': ['t_d5b909cc'], 'creator_task_id': None, 'tenant': None, 'workspace_kind': 'dir', 'workspace_path': '/srv/lab/agent-harness/work/fix-lens', 'branch_name': None, 'project_id': None, 'skills': None, 'goal_mode': None, 'model_override': None, 'provider_override': None}
  [2026-11-26 19:10] dependency_wait {'reason': 'parent_not_done', 'parent': 't_d5b909cc'}
  [2026-11-26 19:14] promoted
  [2026-11-26 19:14] skipped_nonspawnable {'assignee': 'gatekeeper'}
  [2026-11-26 19:14] [run 320] claimed {'lock': 'ailab:381743', 'expires': 1795718698, 'run_id': 320}
  [2026-11-26 19:15] commented {'author': 'default', 'len': 142}
  [2026-11-26 19:15] [run 320] blocked {'reason': 'FXL-1B: the fix pass edited or deleted tests that exist on base (test/framing-f1.test.js, test/framing.test.js); a person must decide', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #320 blocked      @gatekeeper  16s  2026-11-26 19:14
        → FXL-1B: the fix pass edited or deleted tests that exist on base (test/framing-f1.test.js, test/framing.test.js); a person must decide
```

Run files: base.txt, find-raw-1.txt, findings.json, fix-3.json, gates-3.json, gates.json, implement.json, plan.json, proofs.json, readiness.json, refutations.json, repo.txt, review-3.json

## Run summary
Fix pass: pass 3 triggered by review
- Latest gates: {"passed": true, "unmapped": ["test/framing.test.js > AC6: field structure > records tag as number, value as string, and position of tag start"]}; lint True; pass_to_pass True

## Evidence requested by FXL-1B-review5.md (read-only; nothing changed, nothing unblocked)

Models this attempt: planner `gpt-6-sol` (openai-codex); **implementer `gpt-6-sol` (openai-codex), both the first pass and the fix pass, no fallback seen**; finder `deepseek-flash`; spec pass, refuter and prover on Claude. Review cost $3.6803 (card budget 5.0, no proofs skipped).

Heads (by git): first head `3bb9a7e` (gates passed first time, no fix pass needed for the gates), fix head `7f47748` (child of the first head). The `head` field in `gates.json` and `gates-3.json` is labelled the other way round; the commit order above is from `git merge-base --is-ancestor`.

### 1. The review that triggered the pass (`review-3.json`)
Decision: blocking F1, F2, F3, F4; blocking_unproven none; all four proven.

| id | where | claim (short) | proof test | spec_ref |
|----|-------|---------------|------------|----------|
| F1 | src/framing.js:387 | extra prefix rejection (`prev === "="`, `/^\d+=/`) drops `1=yes 8=FIX...` and `session=8=FIX...` | `test/f1-prefix-equals.test.js > F1 delimiter-free prefix containing '=' > keeps a message whose prefix starts with digits and '='` | none |
| F2 | src/framing.js:387 | same rule from the spec side: the start is rejected after `=` or a `digits=` prefix | `test/f2-prefix-equals.test.js > F2: message start after a non-digit with no delimiter on the line > finds 8=FIX preceded by '=' or by a prefix starting with digits and '='` | "a candidate starts at `8=FIX` when the character before it is not a digit and the line before it contains no delimiter (design section 3, step 2)" |
| F3 | src/framing.js:363 | new filter on what follows `8=FIX` (only `.`, `T`, `\|`, SOH, line end, end of text); the design has no such condition (`8=FIXCLIENT` etc. dropped) | `test/framing-f3.test.js > F3: no condition on what follows 8=FIX > returns a candidate when a digit follows 8=FIX` | "Inside a candidate that hasn't reached its CheckSum, `8=FIX` starts a new candidate only right after SOH." |
| F4 | src/framing.js:52 | `checkMessage` ignores `candidate.end`, so a cut-off candidate is checked against the next message's fields | `test/f4-candidate-bound.test.js > F4: checkMessage respects the candidate boundary > reports missing_checksum for a candidate cut off by the next message` | "A candidate with no CheckSum is still returned ... so FXL-2 can report it" |

### 2. Diff of the two base test files, first head to fix head (in full)
```diff
--- test/framing-f1.test.js  (3bb9a7e -> 7f47748)
   it("does not start a message at 8=FIX inside the first field on a line", () => {
-    expect(splitMessages("58=resend 8=FIX.4.2|10=042|")).toEqual([]);
+    expect(splitMessages("35=0|58=resend 8=FIX.4.2|10=042|")).toEqual([]);
   it("does not start a message at 8=FIX inside tag 448 value on a line", () => {
-    expect(splitMessages("448=8=FIX.4.2|10=042|")).toEqual([]);
+    expect(splitMessages("35=0|448=8=FIX.4.2|10=042|")).toEqual([]);
   it("does not start a message at 8=FIX inside tag 8 value on a line", () => {
-    expect(splitMessages("8=8=FIX.4.2|10=042|")).toEqual([]);
+    expect(splitMessages("35=0|8=8=FIX.4.2|10=042|")).toEqual([]);

--- test/framing.test.js  (AC7)
     expect(splitMessages("")).toEqual([]);
-    expect(splitMessages("8=FIXCLIENT\n35=0")).toEqual([]);
+    expect(splitMessages("8=FIXCLIENT\n35=0")).toHaveLength(1);
```
What the edits do, without a verdict:
- **framing-f1.test.js:** the three inputs are not flipped to "a candidate starts". A `35=0|` is put in front of each so the line now has a delimiter before `8=FIX`, and the expectation stays `[]`. The old no-delimiter-prefix inputs (`58=resend 8=FIX...`, `448=8=FIX...`, `8=8=FIX...`) are no longer asserted anywhere in the two edited files.
- **framing.test.js AC7:** `8=FIXCLIENT\n35=0` now expects one candidate instead of none, which matches F3 (no condition on what follows `8=FIX`).
- The earlier edit on this file, `offset` to `position` (FXL-1B's AC0), was already in the first head (`3bb9a7e`) and is not part of this diff.

### 3. Fix head `7f47748`: `vitest run` in the container
Exported with `git archive` to a scratch folder (removed afterwards), run as `hermes` with the root-owned dependency folder: **Test Files 6 passed (6), Tests 61 passed (61)**. (The stored proof tests are not in the branch, so they are not in this count.)

State: gatekeeper (fix 3) card `t_11abf68b` is blocked for a person; the reviewer (fix 3) card is `todo`. Nothing unblocked, nothing edited in `work/fix-lens`.
