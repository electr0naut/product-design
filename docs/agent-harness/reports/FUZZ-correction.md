# Correction: my comparisons against the independent build used a faulty random generator

**What was wrong.** The scripts I used to compare landed code with the independent v1.2 build drew their random
choices from a generator I wrote badly: a 31-bit multiply in JavaScript numbers, which loses its low bits. For a
list with an even number of entries it almost always chose the first one (measured: of 8,000 draws from 8
choices, 7,965 were the first). So "40,000 generated pastes" for FXL-9 were nearly all `|`-delimited, and the
FXL-12 comparison I had just run contained **no fill at all**. I found it when that comparison reported zero
fills. The reviews of FXL-9, FXL-10 and FXL-11 quoted results from it, and so did the first version of
`FXL-9-survivors-classified.md`.

**What I did.** Replaced the generator in every script (a standard 32-bit one, spread checked), and reran all of
them.

| ticket | rerun | result |
|---|---|---|
| FXL-9 | 40,000 pastes, now across all four delimiter forms | **0 differences** from the independent build in message starts, valid fields and every `checkMessage` result (the two set-aside differences are unchanged: `end` after a CheckSum with no delimiter, and bad-tag pieces in `fields`) |
| FXL-10 | 840 kind combinations; 100,000 random logs | 0 differences in kinds. In timelines, 0 differences once the independent build is corrected in **two** places where the design says FXL-10 is right (step 1 of section 7: a first message of a direction makes no gap; a PossDup Logon with 141=Y does not reset). The second one is new |
| FXL-11 | 60,000 random logs, 19,810 with groups of three or more messages | the same groups and members; `findOrder` the same; the only difference is the order of two ids inside one message, as reported |
| FXL-12 | 100,000 random logs, 15,937 with fills and 46,032 with unmatched reports | **one difference in reading, in a place the design does not pin** (see `FXL-12-landed-review.md`); 0 differences once the independent build takes FXL-12's reading |
| FXL-9's surviving mutants | all 70 reclassified | 44 change behaviour, not 35; the hidden suite as it was caught 5, not 7; the file is regenerated |

**What stands.** The verdicts: FXL-9, FXL-10 and FXL-11 landed clean. The hidden-suite results never depended on
this. The forward checks (landed modules inside the independent build, all later hidden tests passing) never
depended on it either.

**What it cost.** The first classification under-counted behaviour-changing mutants, and my new hidden tests
missed one rule (a delimiter followed by `=` with no digits), now added.
