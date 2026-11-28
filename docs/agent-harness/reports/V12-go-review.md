# v1.2: Ubay's two answers, the design refresh, and the go for the first batch (instruction)

## Ubay's words (RULES section 1)

On 2026-11-27 the reviewing session put two points to Ubay: "1. Say **yes** to the agent's question about the
practice ticket, in its session. 2. Tell me here whether you approve the **eleven design clarifications**."
Ubay answered: "yes to both".

## What follows from them

1. **The practice ticket is approved.** Run check 1 of `D20-code-review.md` (one fixture ticket through the new
   pipeline on a sample repository, with a second ticket queued behind it). His instruction to you to load no
   tickets is lifted for this, and for the first batch below under its conditions.
2. **Technical design v1.2.1 is approved** and merged (`fix-lens/technical-design.md` at `ae216b0`). Decision
   `D-20261127-3` refreshes the copies from that commit. Confirm that it was applied and that the recorded
   design sha256 changed.

## The go for FXL-9 to FXL-13, on conditions

Load **FXL-9, FXL-10, FXL-11, FXL-12 and FXL-13, and nothing else**, with the D20 loader, when **all** of these
hold. Report them first, in one file, `V12-live-checks.md`:

- both units are installed as `D20-deploy-review.md` asks;
- **check 1:** the `accept` card was created, the second fixture ticket waited on it, the runner completed it
  after the scribe, and only then did the second ticket start;
- **check 2:** the real hidden suite ran in the isolated container with **no regression**, the two retired tests
  named apart, and the copies' commit shown;
- **check 3:** the test alert was sent without error;
- `D-20261127-3` is applied and the copies verify.

**If anything differs from this, in any way: load nothing, report, and wait.** Do not fix and retry.

After loading, the runner does the rest. Don't start the old driver. **FXL-14 to FXL-16 are not loaded:** after
FXL-13 lands I retire the five `acc-render` tests and refresh the copies first.

## What I check as tickets land

The evidence the runner publishes for each ticket, the hidden suite's result, and, after FXL-9, a real-browser
run with `^A` and `<SOH>` logs.
