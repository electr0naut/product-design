# D23: static mutants counted apart; and FXL-9's 70 real survivors (instruction)

`FXL-10-static-survivors.md` is accepted. The cause is shown from Stryker's own fields: the five are static,
were run against one page test only, and "Survived" there says nothing about the tests that do kill them.

## Build D23: the counting change, as you propose
On a branch from `0dee234` (so that one deploy carries D22 and D23). In a clone only; nothing live changes.
- `Survived` with `static == true`, while `ignoreStatic` is on: counted as `static_not_measured`, kept out of
  `survived` and out of the survivors list.
- The evidence line and the review input show the count, in words: `static (not measured) N`.
- `Killed` and `Timeout` static mutants stay as they are.
- Tests: this shape, a static kill, a non-static survivor, and the evidence line.

I accept the cost you name (a static mutant that no test catches also shows as not measured). Do not switch
`ignoreStatic` off: untimed, and the cap is already half used on FXL-9.

Report as `D23-static-mutants.md`. After my review, Ubay's deploy line names the D23 commit instead of
`0dee234`.

## FXL-9: the 70 survivors that are not static (read-only, from your trial report)
That is the number that matters: FXL-9's gates were green with no mutation result, and the trial says its tests
leave 70 mutants of `src/framing.js` alive, 32 timed out and 25 untested. My fuzz against the independent build
found the code right, so this is about the tests, not a bug. I want to see it before the official rerun.

Push `FXL-9-trial-survivors.md` with, from the trial's raw report, for `src/framing.js` only:
- every `Survived` non-static mutant: line, the original line, the replacement, the mutator, and how many
  tests covered it;
- the same for the 25 `NoCoverage` mutants;
- the 32 `Timeout` mutants as a count per line.

From that I decide between a follow-up ticket for the tests and accepting equivalent mutants. No ticket is
loaded from this; it is a list.
