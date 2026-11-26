# FXL-8 review block: exclude the generated `.js` dictionaries only when the runner proves they are data (D18)

**The approval check is accepted:** 59/59 hidden, 123/123 project, on `e721f3186288ac0f93d0403a7eb2be959c8099c7`.
Stopping at the new block was right. Leave `t_fec12d61` blocked.

**Not the suggested fix as written.** A path in `diff_exclude` that ends in `.js` is a file the page executes and
no reviewer reads, for every later ticket too. The check you ran covers this head only. The runner has to make
that check itself, every time.

## D18 (kit change: branch, my review, then the user runs `harness-deploy`)

1. **New key** `[review] data_modules`: a list of exact paths, no globs. For `fix-lens`:
   `["src/dictionary/fix42.js", "src/dictionary/fix44.js"]`. Leave `diff_exclude` as it is.
2. **In `review_diff`,** for a changed path listed in `data_modules`:
   - read the file from the commit, `git show <head>:<path>`, never from the worktree;
   - it is **data-only** when the whole text, stripped, is `export default ` followed by text that `json.loads`
     accepts as an object or array, followed by an optional `;`. Nothing else: no comment, no second statement,
     no import.
   - **Data-only:** leave it out of the chunks and list it under `excluded` with its size and
     `"data_only": true`, so the prompt shows it like the other excluded files.
   - **Not data-only, or not present at the head:** treat it as any other file. It is reviewed, or it blocks as
     too large, as today. Log which check failed.
3. **Tests:**
   - a valid data module is excluded and listed;
   - JSON followed by a second statement is kept;
   - `export default` of a call or a function is kept;
   - a comment before or after the literal is kept;
   - a path in `data_modules` that the diff deletes is kept (listed as a normal change);
   - the content comes from the commit: a worktree file that differs from the head changes nothing;
   - a path matching no entry is unaffected, and globs in `data_modules` are refused at config load.
4. **Report** as `D18-data-modules.md` with the branch sha and the test output. Nothing is deployed or unblocked
   by you. After the user deploys, I push the decision file that retries `t_fec12d61` once.

## Not part of D18

Don't touch the fix-lens work tree, the ledger or the board for this. Bake-off round 2 and the fallback change
(`FALLBACK-review.md`) carry on as they are; the fallback change is still only for a moment when no implementer
card is running.
