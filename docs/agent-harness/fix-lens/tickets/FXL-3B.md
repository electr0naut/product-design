+++
key = "FXL-3B"
title = "Bring the dictionary API, build script and tests in line with FXL-3's spec"
rank = 3
blocked_by = ["FXL-3"]
labels = []
+++
FXL-3 landed with four deviations from its ticket and technical design section 5. Fix them without changing the
generated dictionary content.

Acceptance criteria
- AC0: A test imports `lookup` and `enumName` from `src/dictionary.js` and calls them with exactly these
  argument orders: `lookup("FIX.4.4", 35)` and `enumName("FIX.4.4", 35, "A")`.
- AC1: `src/dictionary.js` exports `lookup(beginString, tag)` and `enumName(beginString, tag, value)`, in that
  argument order, as the FXL-3 ticket specifies; the existing behaviour (null for an unknown tag, a missing enum
  value, or an unsupported BeginString) is unchanged and tested with the new order.
- AC2: The reproducibility test builds into a temporary folder (the build script takes an output folder argument,
  defaulting to `src/dictionary/`) and compares that output byte for byte with the committed files; running the
  test suite never modifies files under `src/`.
- AC3: `tools/build-dictionary.mjs` uses no dependencies (no `jsdom`): a small XML reader in the script extracts
  the `field` and `codeSet`/`code` elements' attributes. Its output is byte-identical to the committed
  `FIX42.json` and `FIX44.json`.
- AC4: Tests in `test/dictionary.test.js` are top-level `test()` calls (technical design section 9).
- AC5: The generated files are named `src/dictionary/fix42.json` and `src/dictionary/fix44.json` (lower case, as
  the FXL-3 ticket and technical design section 5 name them); no upper-case copies remain, and every import and
  test uses the lower-case names.
