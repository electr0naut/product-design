# FXL-2B: BLOCKED for a human

## FXL-2B · gatekeeper (fix 1) (t_936736a8) is blocked
```
Comments (1):
  [2026-11-26 20:13] default: BLOCKED: FXL-2B: the fix pass edited or deleted tests that exist on base (test/helpers.test.js); a person must decide

Events (6):
  [2026-11-26 20:09] created {'assignee': 'gatekeeper', 'status': 'todo', 'parents': ['t_834114ea'], 'creator_task_id': None, 'tenant': None, 'workspace_kind': 'dir', 'workspace_path': '/srv/lab/agent-harness/work/fix-lens', 'branch_name': None, 'project_id': None, 'skills': None, 'goal_mode': None, 'model_override': None, 'provider_override': None}
  [2026-11-26 20:09] dependency_wait {'reason': 'parent_not_done', 'parent': 't_834114ea'}
  [2026-11-26 20:12] promoted
  [2026-11-26 20:12] [run 329] claimed {'lock': 'ailab:391847', 'expires': 1795722179, 'run_id': 329}
  [2026-11-26 20:13] commented {'author': 'default', 'len': 117}
  [2026-11-26 20:13] [run 329] blocked {'reason': 'FXL-2B: the fix pass edited or deleted tests that exist on base (test/helpers.test.js); a person must decide', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #329 blocked      @gatekeeper  9s  2026-11-26 20:12
        → FXL-2B: the fix pass edited or deleted tests that exist on base (test/helpers.test.js); a person must decide
```

Run files: base.txt, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, readiness.json, repo.txt

## Run summary
Fix pass: pass 1 triggered by gates
- First attempt's gates: {"passed": false, "missing_acs": ["AC0", "AC1", "AC4"]}; lint True; pass_to_pass True
- Latest gates: {"passed": true}; lint True; pass_to_pass True

Fix feedback trigger: gates

## Evidence requested by FXL-2B-review.md (read-only; nothing changed, nothing unblocked)

Implementer: **`gpt-6-sol` (openai-codex), first pass and gate fix pass, no fallback.** Codex use so far: implementer 2 sessions, 38 calls, 91,673 in / 8,939 out; planner 1 session, 11 calls, 27,460 in / 3,540 out. No rate-limit or fallback line in either log during this ticket. No review has run yet (no finder).

First head `b36354c6995743212027c29a6f593aa3370873bb` (gates failed: AC0, AC1, AC4 without a valid test), fix head `356ab44656876d55e36d763c8d4f56e89faf361c` (child of the first head; gates passed). Base `7f47748`.

### 1. `test/helpers.test.js`, first head to fix head (in full)
```diff
@@ -1,6 +1,6 @@
 import { describe, it, expect } from "vitest";
 import { buildMessage } from "./helpers/fix.js";
-import { splitMessages } from "../src/framing.js";
+import { checkMessage, splitMessages } from "../src/framing.js";
 
 describe("buildMessage helper", () => {
   it("test_buildMessage_both_delimiters_match_fixed_checksum_vectors", () => {
@@ -8,9 +8,11 @@ describe("buildMessage helper", () => {
     expect(buildMessage(fields, { delim: "\x01" })).toBe(
       "8=FIX.4.4\x019=20\x0135=0\x0134=1\x0149=A\x0156=B\x0110=125\x01"
     );
-    expect(buildMessage(fields, { delim: "|" })).toBe(
+    const pipe = buildMessage(fields, { delim: "|" });
+    expect(pipe).toBe(
       "8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|"
     );
+    expect(checkMessage(splitMessages(pipe)[0], pipe)).toBeNull();
   });
 
   it("builds a message with pipe delimiter by default", () => {
```
Facts for the decision: no expected value changes in this diff; it adds one assertion (`checkMessage` of the pipe vector is `null`). The test it edits did **not** exist on the base: the ticket's first pass added it. The file did exist, and the rule is per file.

**Your expected edit is in the first pass, not the fix pass.** For context, base `7f47748` to first head `b36354c` on the same file: it adds that fixed-vector test, and in an existing test changes `new TextEncoder().encode(msgBefore)` to `new TextEncoder().encode(msgBefore.replaceAll("|", "\x01"))`, so the old assertion of a pipe-byte CheckSum now expects the SOH-byte one.

### 2. Fix head `vitest run` in the container
`git archive` of `356ab44` into a scratch folder (removed afterwards), run as `hermes`: **7 files passed, 65 of 65 tests passed.**

### 3. Hidden suite on the fix head (scratch trusted root)
A bare clone with `main` = `356ab44`, its own history file; the live trusted repo and history are untouched. `acc-check` **9/9**, `acc-framing` 9/9, `acc-dictionary` 1/4, the other four files don't import (features not built); 19/42. On the trusted `main` after FXL-1B it was 15/42 with `acc-check` 5/9. Run while no bake-off implementer was running.
