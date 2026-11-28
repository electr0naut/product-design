# FXL-9 landed: reviewed, clean, with one gap in its evidence (mutation did not run)

Trusted `main` `60b1211`, evidence `fix-lens/runs/FXL-9.md` (`ba2a47d`). I rebuilt the tree from the published
patch and checked it here.

| check | result |
|---|---|
| hidden suite, run here on the rebuilt tree | **77 pass**, the same as the runner's isolated run; `acc-delimiters` 14 of 14, no regression |
| the project's own tests | the 20 new tests pass; the 4 that fail here are the dictionary tests, which need the vendored XML that a patch does not carry (they fail the same way on my v1.1 copy) |
| fuzz against the independent v1.2 build, 40,000 pastes | **0 differences** in message starts, valid fields and every `checkMessage` result |
| the same fuzz, two differences I set aside | `end` after a CheckSum with no delimiter (FXL-9 keeps the v1.1 convention; the design does not pin it), and bad-tag pieces left out of `fields` (v1.1 kept `0=A` as tag 0; the design does not pin it, and such a message is malformed either way) |
| real browser over HTTP, one log with all four delimiter forms and a delimiter inside a value | 5 messages decoded, no error, no `<img>`, no request to another origin (`browser-check/delims.log`, `fxl9-landed.png`) |
| test edits | all in files the ticket lists as expected to change |
| the two checks of `V12-go-review3.md` | the runner's state names the isolated run (77 of 166, `60b1211`), and the evidence was published by the runner |

**The reviewer's findings F3 and F4** (framing) were not proven, and the fuzz does not support them: the code
agrees with the independent build on every case, including `8=FIX` inside a value and CheckSum-shaped values.
**F1 and F2** (the source check does not look inside a `<template>`) are true and small: `index.html` is ours and
has no template. FXL-14 rewrites that page; if it adds a `<template>`, the check must cover its content.

**FXL-9 counts as landed clean** for `V12-go-review4.md`.

## The gap: Stryker crashed, so there is no mutation result for FXL-9
`stryker wrote no report (exit 1)`, with a stack from `concurrent/pool.js`. Mutation is report-only, so the
ticket landed, but the largest logic change of v1.2 so far has no measure of its tests. D19 fixed one cause of
this and kept Stryker's output for exactly this case.

**Do now, read-only, while the batch runs:**
1. Read the kept Stryker output for FXL-9 and report the cause on the PR, with the lines that show it.
2. Say whether FXL-10 to FXL-13 will hit the same thing (is it something FXL-9 added, such as the new
   `tools/audit-source.mjs` check, or something in the kit or its dependencies?).

**Do not change the kit, its config or the dependencies while cards are running.** The batch goes on. If the
cause is in the kit, it becomes the next kit change, and the mutation runs for the tickets that missed it are
done afterwards on their landed commits, before v1.2 is called finished.

## Also noted
- 26 minutes from load to landing; no fix pass, no block. Claude on the review: $1.63.
- Add to the kit list: a mutation run that errors should be named in the block of "what changed" in
  `STATE.md`, so it is seen without opening the evidence.
