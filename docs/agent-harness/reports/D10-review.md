# D10: spec-conformance review, a hidden acceptance suite, and a hold before FXL-4 (instruction)

**Why:** all three landed FIX Lens tickets had defects that only a human found, by reading each patch against
the ticket, the design and the FIX rules:
- the review checks code against the acceptance criteria, not the whole spec;
- the tests' helper shared the checksum misreading.

D10 moves that human review into the pipeline, and adds a test oracle that the implementers never see.

## 0. Now: hold the queue before FXL-4 (approved; a reversible board change)

Let FXL-1b, FXL-2b and FXL-3b run on as they are. They're corrective, and I review each one myself. Before FXL-4
starts:
- create an unassigned hold card, `HOLD: D10 deployed`;
- link FXL-4's `triage` card to it, in addition to its current parents;
- log the commands.

The hold is released after the user deploys D10.

## 1. The spec-conformance pass (kit change; branch, then my review, then the user deploys)

In `Runner.review`, after the finder and before the refuter:
1. **Inputs, all host-only.** Nothing comes from `work/` or the run folder:
   - **The full ticket text.** The loader records each ticket file's content in host-only state at load time,
     next to `labels.json`, as `tickets/<KEY>.md`. Missing means block `needs_input`.
   - **Spec documents** listed per repository: `[review] spec_docs = ["<host-only path>"]` in the overlay. For
     `fix-lens`, that's a host-only copy of `docs/agent-harness/fix-lens/technical-design.md` from the
     product-design repo, under `~/.local/state/agent-harness/specs/fix-lens/`. The deploy step copies it there.
   - **The diff** as D9 builds it (chunks and the excluded list), plus Read access to the trusted worktree.
2. **The call:** Claude, using the same model and budget settings as the refuter, through `claude -p
   --json-schema` with the findings schema plus a required `spec_ref` field. `spec_ref` quotes the exact ticket
   or design sentence the code deviates from. The prompt asks only for deviations from the quoted text:
   interfaces, names, the rules in the design, reference values in the ticket. Never style.
3. **What happens to its findings:** they join the finder's findings, renumbered, and go through the same
   refuter and prover.
   - A deviation proven by a failing test blocks or starts a fix pass, exactly as today.
   - Unproven critical or high findings are `blocking_unproven`, as today.
   - A finding without a verbatim `spec_ref` (the quote must appear in the inputs) is dropped and logged.
4. **Budget:** at most one spec pass per review, and its cost goes into `cost_usd`. If the budget would be
   exceeded, block `transient`. A ticket is never passed without its spec pass.
5. **Tests:**
   - missing ticket text blocks;
   - a finding whose `spec_ref` isn't in the inputs is dropped;
   - spec findings go through refute and prove;
   - a proven spec finding triggers the review pass;
   - the spec docs are read from the host path only, so an edited copy under `work/` changes nothing.

## 2. The hidden acceptance suite (no kit change: it uses `harness.score`)

The reviewer writes the tests in `docs/agent-harness/fix-lens/acceptance/`, in the product-design repo. Workers
never see that repo.
- **Before deploying D10, copy the folder to host-only state:** `~/.local/state/agent-harness/acceptance/fix-lens/`.
- **After every FIX Lens ticket completes,** the evidence driver runs `harness.score` with `--hidden` on that
  folder against the trusted `main`, inside the container as usual. It writes the per-file results into
  `FXL-<n>.md`.
- **Expected:** files for features that haven't been built yet fail on import. That's fine. What matters is that
  **a hidden test that passed before never fails later.** If one does, the driver reports it as a regression,
  and the queue holds (block the next ticket's `triage` with a hold card).

## 3. Report

Report D10 as `D10-spec-review.md`, with the branch sha, the tests, and the exact deploy lines for the user, in
the same shape as `MORNING-2026-11-26-review.md`. Use bundle-and-fetch for the container copy, plus the spec doc
and acceptance copies.
