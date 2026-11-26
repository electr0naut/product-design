# FXL-7 blocked: the workers have never been able to read the technical design

The implementer stopped because the ticket says "the APIs listed in technical design section 8", and the design
document isn't readable inside the container. The only copy is host-only, for the spec pass. **That has been true
for every FIX Lens ticket.** Each one says "following technical design section N", and no planner or implementer
could ever open it. That goes a long way to explaining the early spec deviations, which the spec pass then caught.

## Do now (approved; read-only copies, no harness code change)

1. **Copy the design so workers can read it.** Copy `~/product-design/docs/agent-harness/fix-lens/technical-design.md`
   into the container at the path the card names, for the `hermes` user
   (`~/.local/state/agent-harness/specs/fix-lens/technical-design.md` under that user's home), and also to
   `/srv/lab/agent-harness/work/specs/fix-lens/technical-design.md`.
   - These are **reading copies.** A worker could edit them, but the spec pass and the review read only the
     host-only copy, so that can't change what's enforced.
   - Check that the implementer profile can open the file. A tiny read with `hermes -p implementer` is enough.
2. **Comment on PR #47 when it's done. Don't unblock anything.** I'll unblock FXL-7's implementer
   (`t_a2096e57`) with a **decision file**, the first one through D15.

## D16 (next harness change; add to the backlog list)

1. **The loader writes the worker-readable path of each spec document into every stage card,** and the planner
   and implementer cards say to read the named sections before planning or coding. There's a test.
2. **The deploy copies the spec documents into that worker-readable location as well,** every time.
3. **On a fix pass, the fix feedback includes any note that carries a verbatim `spec_ref`,** as already noted.
