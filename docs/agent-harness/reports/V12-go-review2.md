# D20 live checks so far: accepted; one ticket change before the first batch is loaded (instruction)

`D20-live-checks.md` (partial) is accepted: both units are installed, the hidden suite ran in isolation with no
regression (67 of 166, the two retired tests named apart), and the test alert was sent. The undo-line finding
and the deploy tool's two flaws go to the next kit change, as you list them.

## The ten tests newly in `passed`: your question

Good catch. I went through all ten. Nine check things that hold at every step from v1.1 to v1.2 (they also pass
on the independent v1.2 build), so they are safe to protect from now.

**One was a trap:** `acc-presentation.test.js` > `no dynamic import, no setAttribute, and no attribute-like
property is assigned anywhere in src`. It enforces a design rule (section 8.4) that the tickets FXL-9 to FXL-13
did not state and the project's own check did not yet test. A worker could have written `field.value = ...`
within its ticket and held the queue.

**Fixed in the tickets, not by loosening the test** (commit below):
- **FXL-9** gains AC12: the source check is extended now, with every rule of section 8.4.
- **FXL-10 to FXL-13** state the rule in their text.
- **FXL-14** AC15 now says the extended check still passes.

## Loading the first batch

The conditions of `V12-go-review.md` stand, with one more: **load the ticket files from this commit or later**
(`git log -1 --format=%H -- docs/agent-harness/fix-lens/tickets/FXL-9.md` must show the commit that adds AC12).
If you have already loaded FXL-9 to FXL-13 from an older commit, say so at once and stop: do not reload by
yourself.

The fixture ticket: Ubay's yes is quoted in `V12-go-review.md`.
