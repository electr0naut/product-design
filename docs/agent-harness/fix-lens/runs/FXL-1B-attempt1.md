# FXL-1B: BLOCKED for a human

## FXL-1B · gatekeeper (fix 1) (t_ccbe9210) is blocked
```
  [2026-11-26 15:01] default: BLOCKED: FXL-1B: gates failed: base="f36221cfc647c8981d3b190ced10a95c97d63baf", head="f68ca73113ed41e07ac14f023ed898a18c072b73", base_ids=35, head_ids=35, new_ids=["test/framing-f1b.test.js > FXL-1b: splitMessages interface and boundary rules > test_splitMessages_end_uses_text_lengt, removed_ids=["test/framing-f1.test.js > AC3: 8=FIX inside another field > does not start a message at 8=FIX inside tag 448 value on , valid_tests=["test/framing-f1b.test.js > FXL-1b: splitMessages interface and boundary rules > test_splitMessages_end_uses_text_lengt, missing_acs=["AC0", "AC1", "AC2", "AC3"]

Events (7):
  [2026-11-26 14:50] created {'assignee': 'gatekeeper', 'status': 'todo', 'parents': ['t_8927f6a0'], 'creator_task_id': None, 'tenant': None, 'workspace_kind': 'dir', 'workspace_path': '/srv/lab/agent-harness/work/fix-lens', 'branch_name': None, 'project_id': None, 'skills': None, 'goal_mode': None, 'model_override': None, 'provider_override': None}
  [2026-11-26 14:50] dependency_wait {'reason': 'parent_not_done', 'parent': 't_8927f6a0'}
  [2026-11-26 15:00] promoted
  [2026-11-26 15:00] skipped_nonspawnable {'assignee': 'gatekeeper'}
  [2026-11-26 15:01] [run 289] claimed {'lock': 'ailab:355128', 'expires': 1795703463, 'run_id': 289}
  [2026-11-26 15:01] commented {'author': 'default', 'len': 593}
  [2026-11-26 15:01] [run 289] blocked {'reason': 'FXL-1B: gates failed: base="f36221cfc647c8981d3b190ced10a95c97d63baf", head="f68ca73113ed41e07ac14f023ed898a18c072b73", base_ids=35, head_ids=35, new_ids=["test/framing-f1b.test.js > FXL-1b: splitMessages interface and boundary rules > test_splitMessages_end_uses_text_lengt, removed_ids=["test/framing-f1.test.js > AC3: 8=FIX inside another field > does not start a message at 8=FIX inside tag 448 value on , valid_tests=["test/framing-f1b.test.js > FXL-1b: splitMessages interface and boundary rules > test_splitMessages_end_uses_text_lengt, missing_acs=["AC0", "AC1", "AC2", "AC3"]', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #289 blocked      @gatekeeper  15s  2026-11-26 15:01
        → FXL-1B: gates failed: base="f36221cfc647c8981d3b190ced10a95c97d63baf", head="f68ca73113ed41e07ac14f023ed898a18c072b73", base_ids=35, head_ids=35, new_ids=["test
```

Run files: base.txt, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, readiness.json, repo.txt

## Run summary
Fix pass: pass 1 triggered by gates
- First attempt's gates: {"passed": false, "missing_acs": ["AC0", "AC1", "AC2"], "unmapped": ["t/framing-f1b.test.js > FXL-1b: splitMessages interface and boundary rules > test_splitMessages_missing_checksum_at_line_end_returns_candidate", "test/framing.test.js > AC6: field structure > records tag as number, value as string, and position of tag start"]}; lint True; pass_to_pass True
- Latest gates: {"passed": false, "missing_acs": ["AC0", "AC1", "AC2", "AC3"], "unmapped": ["test/framing.test.js > AC6: field structure > records tag as number, value as string, and position of tag start"]}; lint True; pass_to_pass True

Fix feedback trigger: gates

## Review check (FXL-1B-review.md), read-only

**The cause is not the id format. It is a harness bug: the gate's test collection is silently cut to its last 4000 characters.**
`gates.run_cmd` returns `(proc.stdout + proc.stderr)[-4000:]`, and `collect_ids` reads the test ids from that string.
`vitest list` prints 60 ids (about 9 KB) on the head, so the gate only saw the tail.

Evidence:
- The ids in `implement.json`'s `ac_tests` match `vitest list` on the head **exactly**. I ran `vitest list` on a clean
  archive of `harness/FXL-1B` (f68ca73): all seven `test/framing-f1b.test.js` ids are there, including the four AC0 to AC3
  ids, character for character.
- The gate's counts are not the real ones: `base_ids=35` and `head_ids=35`. Run directly (same command, in a clean
  archive) the base `f36221c` has 53 ids and the head has 60, each file once: dictionary 17, framing-f1b 7, framing-f1 3,
  framing-f2 12, framing 14, helpers 7. Repeated 4 times, always 60.
- The cut lands inside a line. Attempt 1's `unmapped` has the id `t/framing-f1b.test.js > ...`, with the start of
  `test/` cut off. That is the 4000-character boundary.
- So `new_ids` and `removed_ids` are artefacts. The head file and the base file are cut at different places, and the ids
  in front of the cut vanish from each side. That is why `framing-f1.test.js > AC3 ...` shows up as "removed" while
  `git diff f36221c harness/FXL-1B -- test/framing-f1.test.js` is empty: that file is untouched.
- AC0 to AC3 are "missing" because their test ids (file `framing-f1b`, listed early in the output) were in the cut-off
  part of the head's list.

**Models per stage (this attempt):** planner `gpt-6-sol` (openai-codex), 1 call, no fallback row; triage and implementer
(both attempts) `qwen3.7-plus` (alibaba-token-plan). Nothing else has run yet: the reviewer and the spec pass never started,
because the gates blocked first.

**Base tests changed by the fix pass (question 3):** no deletion and no FXL-1 test file change. The implementer *edited*
existing tests, and says so in `modified_existing_tests`: in `test/framing.test.js` and `test/framing-f2.test.js` it
changed `offset` to `position` in field assertions and in hand-built candidate fields, to match the interface the
ticket asks for (AC0 names the `position` key). One test was **renamed** with it:
`... and offset of tag start` became `... and position of tag start` (`framing.test.js`, AC6). That is a base test
changed, so the gate flags `existing_tests_touched`. The change follows from the ticket, but it is the reviewer's call.

**Cost of the bug:** it would hit every ticket whose suite lists more than about 25 ids. FXL-1B is only the first one
that got there, since the suite grew with FXL-1b, FXL-2 and FXL-3. Suggest D11 gets: raise the collect output limit (or
do not cut `collect` output at all, only the tail kept for reports), and block with a clear reason if a collect output
looks cut (for example, if no line was dropped by the regex but the output length equals the limit).

Nothing was unblocked or changed. The driver stopped on the block, as designed. The `*-review.md` watcher is running.
