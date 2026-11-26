# FXL-8: BLOCKED for a human

## FXL-8 · reviewer (fix 1) (t_fec12d61) is blocked
```
Comments (1):
  [2026-11-26 23:13] default: BLOCKED: reviewer runner: diff too large to review: one hunk of src/dictionary/fix44.js is 164339 characters (limit 60000)

Events (6):
  [2026-11-26 23:02] created {'assignee': 'reviewer', 'status': 'todo', 'parents': ['t_a60703ae'], 'creator_task_id': None, 'tenant': None, 'workspace_kind': 'dir', 'workspace_path': '/srv/lab/agent-harness/work/fix-lens', 'branch_name': None, 'project_id': None, 'skills': None, 'goal_mode': None, 'model_override': None, 'provider_override': None}
  [2026-11-26 23:02] dependency_wait {'reason': 'parent_not_done', 'parent': 't_a60703ae'}
  [2026-11-26 23:13] promoted
  [2026-11-26 23:13] [run 398] claimed {'lock': 'ailab:487773', 'expires': 1795733008, 'run_id': 398}
  [2026-11-26 23:13] commented {'author': 'default', 'len': 122}
  [2026-11-26 23:13] [run 398] blocked {'reason': 'reviewer runner: diff too large to review: one hunk of src/dictionary/fix44.js is 164339 characters (limit 60000)', 'kind': 'needs_input', 'recurrences': 1, 'source_status': 'ready'}

Runs (1):
  #398 blocked      @reviewer  2s  2026-11-26 23:13
        → reviewer runner: diff too large to review: one hunk of src/dictionary/fix44.js is 164339 characters (limit 60000)
```

Run files: base.txt, fix-1.json, gates-1.json, gates.json, implement.json, plan.json, readiness.json, repo.txt

Head the latest gates ran on (full sha): `e721f3186288ac0f93d0403a7eb2be959c8099c7`

## Run summary
Fix pass: pass 1 triggered by gates
- First attempt's gates: {"passed": false, "missing_acs": ["AC2"]}; lint True; pass_to_pass True
- Latest gates: {"passed": true}; lint True; pass_to_pass True

Fix feedback trigger: gates

## Approval check (FXL-8-review.md)
First head `7768c0f39ed0cd73dcf157c777e58b35900ba32a` (gates failed: AC2), fix head **`e721f3186288ac0f93d0403a7eb2be959c8099c7`** (child of the first). First to fix head: `test/dictionary.test.js`, 19 lines added, none removed.
- **Hidden suite on the fix head** (no-network container; compared with the acceptance history without writing to it): **59/59**: acc-analyse 4/4, acc-check 9/9, acc-decode 5/5, acc-dictionary **5/5**, acc-framing 9/9, acc-limits 3/3, acc-page **5/5**, acc-render **5/5**, acc-timeline 14/14. All 53 previously passing still pass; no failures.
- **Project `vitest run` on the fix head** in the container: **15 files, 123/123.**
- All conditions met: approval recorded for that head and `test/dictionary.test.js` (23:12:38); the card was not in the attempts file; unblocked once. **The gatekeeper (fix 1) then passed.**

## New block: the review cannot take the diff (needs a harness config change; not unblocked)
`reviewer (fix 1)` (`t_fec12d61`) blocked at once: `diff too large to review: one hunk of src/dictionary/fix44.js is 164339 characters (limit 60000)`. **Cause:** `[review] diff_exclude` in `eval/fix-lens/harness.fixlens.toml` lists `src/dictionary/*.json`; FXL-8 turns the generated dictionaries into `.js` files, which the list does not cover. No review has run (no Claude spent).
- **Suggested fix** (not made): add exactly `src/dictionary/fix42.js` and `src/dictionary/fix44.js` to `diff_exclude` (exact names, not `*.js`, so a new file in that folder is still reviewed), with a config test; then review, `harness-deploy`, and one unblock.
- **What excluding them leaves unreviewed, checked once now:** at the fix head each file is a single `export default <JSON>;` literal (the whole file parses that way), and its data is identical to the `.json` that the independent XML extraction matched (FXL-3B.md). So there is no code in either file. That is a check of this head only; the ticket's AC2 reproducibility test and the hidden dictionary tests are what guard later changes. A review would not guard them either way at this size.
