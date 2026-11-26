# FXL-2 landed: a FIX bug every check passed, and why (self-consistent test oracle)

FXL-2 landed. The finder ran on DeepSeek for this card, the revert is recorded, Claude refuted nothing, and the two
medium notes were left as notes. Reading `checkMessage` in the patch, **CheckSum is computed over the raw text**,
so a `|` counts as byte 124. TR-002 says `|` is treated as SOH **before** the checksum. The test helper
(`test/helpers/fix.js`, from FXL-1) makes the same mistake, so the helper and the checker agree, and every test
passes.

**What it means in practice:** almost every real log pasted with `|` would be reported as a CheckSum error. For
example, `8=FIX.4.4|9=20|35=0|34=1|49=A|56=B|10=125|` is valid FIX (125 is the sum over SOH), but the code
expects `095`.

## Why the harness missed it

The tests use a helper written by the same implementer, built on the same misreading. That's a **self-consistent
oracle**:
- the gates (fail-to-pass, AC mapping) can't see it;
- mutation testing can't see it;
- a finder reviewing the diff against criteria phrased as "a wrong CheckSum is detected" can't see it.

Only a fixed external reference value catches it. The fix for us is the ticket writer's: domain rules need
**fixed reference vectors** in the acceptance criteria, computed outside the implementation. I've now done that
for CheckSum.

## For the agent (approved; a board change on unstarted tickets only)

- **Load `docs/agent-harness/fix-lens/tickets/FXL-2b.md`** right after FXL-1b and before FXL-3b. It's
  `blocked_by` FXL-2 and FXL-1b.
- **If FXL-1b has already started,** don't touch it: load FXL-2b to follow it, and reload FXL-3b and the rest so
  they wait on FXL-2b's `scribe`.
- **Log the commands** in `D6-morning.md`.

## Backlog (harness)

**Triage check for domain rules.** For each acceptance criterion that states a computation (checksums, lengths,
mappings), triage should flag it unless the ticket gives at least one fixed input and output pair. That turns
this lesson into a check before planning.
