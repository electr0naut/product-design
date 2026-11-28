# FXL-3 review: landed, but the review never saw most of the diff (D9 required)

FXL-3 passed the gates and a review with zero findings. **Reading the patch, I find four deviations** from the
ticket and the technical design:
1. **The "committed JSON equals a fresh build" test is vacuous.** It rebuilds into `src/dictionary/`, then
   compares the file with itself. The tests also rewrite the committed files every time they run.
2. **The argument order is reversed:** `lookup(tag, beginString)` and `enumName(tag, value, beginString)`. The
   ticket specifies `lookup(beginString, tag)`.
3. **The build script uses `jsdom`,** where the ticket says "no dependencies".
4. **The tests use `describe`/`it`,** where design section 9 asks for top-level `test()` calls.

None of these is a FIX bug. The dictionary content looks right, and the spot checks are real. But points 1 and 2
are exactly what the review exists to catch.

## Why the review missed it (a harness defect)

`Runner.review` gives the finder `diff[:60000]`. FXL-3's diff is about 9,600 lines, and in git's order:
1. `src/dictionary.js` (about 1k characters);
2. `src/dictionary/FIX42.json` (about 57k);
3. `FIX44.json` (about 164k);
4. `LICENSE`, `SOURCE.md`, the test file and the build script.

The cut falls inside `FIX44.json`. **The finder never saw the tests or the build script**, and nothing recorded
that the diff had been cut. A review that silently reviews part of a change fails open.

## D9 (build now, branch only; deployed with the morning sha)

1. **Exclude generated and vendored files from the review diff:**
   - add `[review] diff_exclude` globs, applied with git pathspecs `:(exclude)`;
   - for `fix-lens`: `src/dictionary/*.json`, `src/dictionary/LICENSE` and `vendor/**`;
   - list the excluded paths, with their sizes, in the finder prompt, so the reviewer knows they exist.
2. **Never review a truncated diff silently.** When the remaining diff is over the limit, review it **per file in
   chunks**: several finder calls, with the findings merged. If that's impossible, block as `needs_input` with
   "diff too large to review: N characters". Record `diff_chars`, `excluded` and `chunks` in `review.json`.
3. **Tests:**
   - a diff whose first file exceeds the limit still shows the later files to the finder;
   - excluded globs are left out and listed;
   - an over-limit diff never yields a clean review without every file having been seen.
4. **Report as `D9-review-diff.md`.** Fast-forward `master` only after my review. The user then deploys that sha
   instead of `feae6b2`.

## FXL-3b

`docs/agent-harness/fix-lens/tickets/FXL-3b.md` fixes the four deviations. Load it after the morning deploy, before
FXL-4 (it's `blocked_by` FXL-3; make FXL-4 also wait on FXL-3b's `scribe`). It runs with the D9 review in place.

Patch evidence: keep `FXL-3.md` as it is. Add the line "superseded in part by FXL-3b".
