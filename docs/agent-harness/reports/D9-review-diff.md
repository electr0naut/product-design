# D9: the finder reviews every file of the diff (branch `d9-review-diff` @ `4b16baa`, on `master` `feae6b2`; NOT merged, NOT deployed)

Pushed as a branch only (`git ls-remote`: `d9-review-diff = 4b16baa9c88a`; `master` unchanged at `feae6b2`). From a fresh clone of the branch: `310 passed, 3 skipped`, `ruff check` and `ruff format --check` clean. I fast-forward `master` only after your review; the user then deploys that sha instead of `feae6b2`.

## The defect, as the review described it
`Runner.review` handed the finder `diff[:60000]`. FXL-3's diff is about 9,600 lines, and git's order puts `FIX42.json` (about 57k characters) and `FIX44.json` (about 164k) before the tests and the build script, so the cut fell inside the second JSON file: the finder never saw the tests or the build script, and nothing recorded that the diff had been cut.

## What changed (`reviewer.py`)
1. **Excluded files.** `[review] diff_exclude` is a list of globs (same matching as the risk globs: a pattern with `/` matches the whole path, so `vendor/**` and `src/dictionary/*.json` work). Excluded files are left out of the diff the finder sees and are **listed, with their sizes in characters, in every finder prompt** ("Not shown (generated or vendored files, left out by configuration): path (N chars), ..."). The FIX Lens overlay sets `src/dictionary/*.json`, `src/dictionary/LICENSE` and `vendor/**`. The default is an empty list, so every other repository reviews exactly what it did, except for the chunking below.
2. **Never silently cut.** The diff is built per file (every changed path, deletes and both sides of renames included; paths are passed to git as literals). `[review] max_diff_chars` (default 60 000) is the size of one chunk. Files are packed into chunks in order; a file that does not fit is split **by hunks**, each piece carrying its file header. The finder is called once per chunk ("part i of n; the other parts hold the other files"); the raw replies are kept per chunk (`find-raw-c1-1.txt`, `find-raw-c2-1.txt`...; a single chunk keeps today's `find-raw-1.txt`); the findings are merged and **renumbered `F1..Fn`** (each reply numbers from F1, so ids would otherwise collide in the refuter and prover maps).
3. **If a hunk cannot fit** (one hunk larger than the limit), the review raises `DiffTooLarge` (a `RunFileError`), the card **blocks `needs_input`** with "diff too large to review: one hunk of <file> is N characters (limit L)", and **the finder is never called**: nothing is reviewed half.
4. **`review.json` records `diff_chars`** (size of what the finder saw), **`excluded`** (path and size) and **`chunks`**. With every changed file excluded there is no finder call (`chunks: 0`) but the files are listed.

## Tests (`tests/test_review_diff.py`, 13; suite 310)
- **A diff whose first file is over the limit still shows the later files:** a 10-hunk first file is split into pieces and the later files appear in the chunks; every hunk of the big file is in exactly one chunk, every piece keeps its header.
- **Every character lands in exactly one chunk** for limits from 900 to 100 000 over 8 files.
- A single hunk over the limit raises `DiffTooLarge`; through `run_once` it blocks `needs_input`, names the file, calls the finder zero times and never completes the card.
- A real branch with a 20 000-character generated JSON plus four source files and the limit set to 2 500: the JSON's content appears in no prompt, every prompt lists `gen/big.json (N chars)`, every other file appears in some prompt, `review.json` has `chunks`, `excluded` and `diff_chars`, and the raw replies are kept per chunk.
- Findings from two chunks that both say `F1` come out as `F1`, `F2`; a diff that fits is one chunk without a "part" note and keeps `find-raw-1.txt`; everything excluded means no finder call; the FIX Lens overlay carries the three globs and they match the intended paths (and not `src/dictionary.js`).

## For FXL-3b and the morning
FXL-3b (the ticket from your review) runs with this in place. As the review says, it is `blocked_by` FXL-3 and FXL-4 must also wait for FXL-3b's `scribe`: I will do that with one board link at load time (`kanban link <FXL-3b scribe> <FXL-4 triage>`), logged, without editing the ticket files. I added the line "superseded in part by FXL-3b" to `FXL-3.md`; its evidence is otherwise unchanged.
FXL-3 itself reviewed only part of its diff, so its zero findings said little about the tests and the build script; FXL-3b's review will see all of it.

## Not done
No merge, no deploy, no change to the Hermes config or to `work/fix-lens`. Cost of this change at run time: more finder calls on large diffs (Qwen, $0); no extra Claude calls unless the finder finds something.
