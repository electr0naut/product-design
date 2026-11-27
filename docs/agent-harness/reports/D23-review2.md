# D23: accepted so far; add the raw report to the rerun tool, then I review the final commit (instruction)

`D23-static-mutants.md` is accepted, with your correction: the automated review gets no mutation data, so no
prompt changes. I read the diff of `9e04d00` against `0dee234`: the count, the summary line and the evidence
line are what was asked.

**Add to the same branch, as you propose:** `tools/rerun_mutation.py` saves Stryker's raw `mutation.json`
beside its record in the host records, with a test. Nothing else. Report the new commit on the PR; I review
that one and write the deploy line for it.

## FXL-9's survivors: I have classified them (`FXL-9-survivors-classified.md`)
Each of the 70 applied to the landed code and compared on 12,015 generated pastes:
- **28 change behaviour and nothing catches them,** neither the project's tests nor the hidden suite;
- 7 change behaviour and only the hidden suite catches them;
- 35 make no observable difference.

So the official rerun is no longer needed to decide: FXL-9's tests have real gaps, and so has my hidden suite.
What follows, none of it for you to act on now:
- **Hidden tests:** I add the missing cases in the commit that retires the `acc-render` tests after FXL-13.
- **The project's tests:** a tests-only follow-up ticket for the framing rules, after FXL-16.
- **The harness:** a mutation result that nobody and nothing reads is evidence only on paper. FXL-9 landed
  green with 28 behaviour-changing mutants alive. This goes to Ubay as the main finding of the batch.

Still run `tools/rerun_mutation.py FXL-9` after the deploy, as `D22-code-review.md` says: it makes the record
official and exercises the tool on the real kit.
