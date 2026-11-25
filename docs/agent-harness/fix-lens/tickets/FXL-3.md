+++
key = "FXL-3"
title = "Generate the FIX 4.2 and 4.4 dictionaries from the Orchestra files"
rank = 3
blocked_by = []
labels = []
+++
Following technical design section 5. The Orchestra files are already vendored in `vendor/orchestra/` with
`LICENSE` and `SOURCE.md` (pinned commit) by the operator before this ticket starts; this ticket does not use
the network.

Add `tools/build-dictionary.mjs` (no dependencies) that writes `src/dictionary/fix42.json` and
`src/dictionary/fix44.json`, and `src/dictionary.js` with `lookup(beginString, tag)` and
`enumName(beginString, tag, value)`.

Acceptance criteria
- AC1: The build script reads only `vendor/orchestra/OrchestraFIX42.xml` and `OrchestraFIX44.xml` and records the
  pinned commit from `SOURCE.md` as a constant.
- AC2: Running the build twice gives byte-identical output, and the committed JSON equals a fresh build.
- AC3: Spot checks: in both versions tag 35 is `MsgType`, tag 8 is `BeginString`, tag 150 is `ExecType`; 35=`A`
  is `Logon`; 35=`j` is `BusinessMessageReject` in 4.4 and in 4.2; 150=`F` exists in 4.4 and not in 4.2.
- AC4: Each entry has a name and a type; enum symbolic names appear only for fields with a code set. The JSON
  contains no description text (no field longer than 80 characters).
- AC5: `lookup` returns `null` for an unknown tag; `enumName` returns `null` for a value missing from the code set,
  and for a BeginString other than `FIX.4.2` or `FIX.4.4`.
- AC6: The licence (and any NOTICE) is present in `vendor/orchestra/` and also in `src/dictionary/`, next to the
  generated files, with a `SOURCE.md` there naming the pinned commit; a test checks they exist.
