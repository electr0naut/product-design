# FXL-3B landed: check F1 against an independent extraction

**F1** (high, not proven): the build script's field regex also scans inside `codeSet` blocks. If that's true,
code entries could leak into the field table. The hidden `acc-dictionary` (4 of 4) only spot-checks a few tags,
so it wouldn't notice. **Mutation 0 of 83 killed** is most likely because the tests run the build script through
`execSync` in a separate Node process, which Stryker can't instrument. That's harmless, but it also means
mutation testing says nothing about the build script.

## Check (read-only; no ticket change)

Write a small **independent** extractor in Python's standard library, using `xml.etree` (a real XML parser), not
regexes, in a scratch folder outside the repo. Run it on `vendor/orchestra/OrchestraFIX42.xml` and `...44.xml` at
the trusted main. For each version, extract:
- field id → name and type, from the field elements only;
- for each field whose type is a code set, its code value → name.

Compare with the committed `src/dictionary/fix42.json` and `fix44.json`. Report in `FXL-3B.md`:
- the counts on each side;
- every tag present on one side only;
- every tag whose name, type or enum entries differ, with the first 20 shown.

**Result decides the next step:**
- **Identical:** F1 is a false alarm. Record that.
- **Differences:** say so on PR #47. I'll write a ticket, FXL-3C, with the independent extraction as its
  reference oracle. It goes before FXL-4, which uses the dictionary. Pause FXL-4 with a hold card until then;
  that's approved now, in case it's needed.

Continue building D15 meanwhile.
