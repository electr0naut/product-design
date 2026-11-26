# D20: the runner does the evidence driver's job (instruction)

**Priority:** after D19. Build on a branch; I review; Ubay deploys between tickets.

**Why:** `tools/fixlens_driver.py` runs the hidden suite after each ticket and creates the hold on a
regression. It lives on a side branch, was never reviewed as kit code, and is started by hand from a chat
session. If that process or that session stops, tickets land with no regression check and no evidence, and
nothing says so. A quality gate has to run in the reviewed, deployed runner.

## 1. After a ticket completes, in the timer pass

When a ticket's last card is done and the runner has not yet recorded it as finished:

1. Run the hidden suite against the trusted `main` with the host-only hidden folder and history
   (`harness.acceptance`).
2. **On a regression:** hold the queue with the same mechanism as the `hold` decision. The hold is recorded
   before anything is published.
3. Write the evidence for the ticket (what the driver writes today: the run summary, the gates, the review, the
   cost, the hidden results, the patch) and publish it.
4. Record the ticket as finished in host-only state, so a later pass does not repeat any of it.

**The next ticket's first card must not start before step 2 has run.** Show how the order is guaranteed, and
test it: a completed ticket whose acceptance run has not happened holds the queue by itself.

## 2. On a block

Write and publish the block report once per block event, as the driver does now: card, reason, the full head
commit, the run files.

## 3. Publishing

- Per repository, the reviewed config names the evidence folder and the pull request to comment on.
- Publishing is a commit to the reports branch plus one comment. It goes through the path the runner already
  uses for decision results.
- **A publishing failure never blocks or holds the pipeline.** It is retried on later passes, and reported by
  the alert in section 5 after three failures. The acceptance run and the hold do not depend on publishing.

## 4. A state file

After any pass in which something changed, the runner writes `state.json` in host-only state, and publishes a
readable copy as `docs/agent-harness/STATE.md` on these events only: a ticket finished, a block, a hold or
release, a decision applied, the kit commit changed.

It holds: the kit commit; each ticket with its cards and their states; each block with its reason and head;
holds; the last hidden-suite result; the default model and fallback list of each profile, read from the profile
files; instruction files that have no report yet.

## 5. An alert when the runner itself fails

`OnFailure=` on the runner's service, calling the existing notifier, with the last journal lines. One alert per
failure, not one per minute.

## 6. Retire the driver

When D20 is deployed and one ticket has gone through it: stop the driver process, and delete
`tools/fixlens_driver.py` and the `d6-driver` branch. Port what is needed into `src/harness/`, with tests. Do
not leave two things doing the same job.

## 7. Tests

- acceptance runs once per finished ticket, and not again on later passes;
- a regression holds before the next ticket's first card can start;
- a ticket that finished while the runner was down is caught up on the next pass;
- a block report is written once per block event, and again for a re-block;
- publishing fails three times: the pipeline carries on, one alert;
- the state file matches the board in a seeded example, and lists a profile's model and fallbacks;
- nothing is read from a work folder.

Report as `D20-runner-evidence.md` with the branch commit and the test output.
