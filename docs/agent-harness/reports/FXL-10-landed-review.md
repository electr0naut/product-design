# FXL-10 landed: reviewed, clean

Trusted `main` `80116ec`, evidence `fix-lens/runs/FXL-10.md`. Rebuilt here from the published patch.

| check | result |
|---|---|
| hidden suite, run here on the rebuilt tree | **88 pass**, the same as the runner's isolated run; `acc-events` 11 of 11; no regression |
| the project's own tests | the 10 new tests pass (the same 4 dictionary tests fail here for want of the vendored XML) |
| `executionKind` against the independent v1.2 build | 840 combinations of version, ExecType and ExecTransType: **0 differences** |
| timelines against the independent build, 20,000 random logs | **0 differences** once the reference is corrected in one place, where FXL-10 was right: a first message of a direction that is a Logon with 141=Y makes no gap (design section 7, step 2). My reference build had that wrong; no hidden test depends on it |
| the block | one, for the fix pass's test edit; approved after reading the diff (`D-20261127-4`), unblocked once (`D-20261127-5`) |
| reviewer | no findings |

**FXL-10 counts as landed clean** for `V12-go-review4.md`.

## The five "survivors" are not survivors (read-only question)
The evidence lists 5 surviving mutants, all in the `ORDER_NAMES` table of `src/timeline.js`, with no covering
tests. Applied by hand here (`ORDER_NAMES = {}`), **9 tests of `test/timeline.test.js` fail**, so the tests do
kill it. These look like Stryker's static mutants (code that runs once at import), which it cannot attribute
to a test with `ignoreStatic` on, and which the kit then counts as `survived`.

**Do now, read-only:** in FXL-10's mutation report, give for those five mutants `status`, `static`,
`coveredBy`, `killedBy` and `testsCompleted`. Say how many of the 72 survivors of your FXL-9 trial run have the
same shape. If they are static, propose the smallest change that counts them apart ("static: not measured")
instead of as survivors. Do not build it yet, and change nothing while cards run.

It matters because survivors go to the reviewer and into the evidence as a measure of the tests. A count that
includes mutants the tests do kill makes good tests look weak, and hides the real ones.
