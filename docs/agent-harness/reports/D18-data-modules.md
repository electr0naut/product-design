# D18: generated .js dictionaries leave the review only when proved to be data (FXL-8-review2.md)

Branch `d18-data-modules` in agent-harness, on top of master `3a0ec24`, at **`0f8acf41f0e5d76549c02f0a80ced235bee91bdc`**. Not merged, not deployed. Nothing unblocked; the work tree, ledger and board were not touched.

## Change
- **`[review] data_modules`:** exact paths. `repos.effective` (where overlays are applied) refuses globs, a leading `/`, `..`, non-strings and a non-list. `fix-lens` lists `src/dictionary/fix42.js` and `fix44.js`. `diff_exclude` is unchanged.
- **`review_diff`:** for a changed path in the list, `data_only` reads the file **from the commit** (`ls-tree`, then `git show --no-textconv <head>:<path>`, as bytes) and accepts only: stripped text = `export default ` + one JSON object or array + at most one `;`. Then it is left out of the chunks and listed under `excluded` with its size and `"data_only": true`, so the finder and spec prompts name it like the other excluded files. Otherwise it is treated like any other file (reviewed, or too large and blocking), and the journal says which check failed.
- **Stricter than the text, on purpose (each means "review it"):** a symlink or executable file at a listed path (a symlink's blob text is not the code a page would load); bytes that are not UTF-8; `NaN` and `Infinity`, which Python's `json.loads` accepts but JSON does not; nesting too deep to parse; a BOM.

## One limit to know
"Data only" means no code can run from the file. It is not "same meaning as JSON": in a JavaScript object literal a `"__proto__"` key sets the object's prototype instead of adding a key. That cannot execute anything, and the check lets it through as the text asks. If you want it reviewed instead, it is a few lines (an `object_pairs_hook` that refuses that key). Whether the data is **correct** is still the job of the reproducibility test and the hidden dictionary tests.

## Tests
Fresh clone: **441 passed, 3 skipped**; ruff check and format clean. `tests/test_d18.py`:
```
.........................................                                [100%]
41 passed in 1.11s
```
Covered: valid modules left out and listed; 20 non-data texts kept (second statement, call, function, comment before, after or inside, import, comma expression, bare string or number, `NaN`, `Infinity`, unquoted key, other prefix, BOM, very deep nesting); non-UTF-8; symlink; a too-large non-data file still blocks, a large data module no longer does; a deleted listed path is a normal change; content comes from the commit (a differing worktree changes nothing, both ways); an unlisted path is unaffected; globs and bad values refused at load; the fix-lens config.

## Dry check on the blocked head (scratch bare clone, no model call)
Base `8db74fc`, head `e721f31`, with the branch's config: both `.js` modules are `data_only`; reviewed files are `src/dictionary.js`, `src/render.js`, the three tests and `tools/build-dictionary.mjs`, **one chunk of 16,487 characters** (limit 60,000).

After your approval the user runs `harness-deploy <sha>`, then your decision file retries `t_fec12d61` once.
