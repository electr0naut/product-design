# D6: set up FIX Lens and run its tickets (instruction)

**Inputs:**
- **PRD v1.1**, approved at Gate 3 by the user (Confluence page 557109).
- **Technical design v1.1**, approved under the user's delegation (Confluence page 1409027, "FIX Lens - Technical
  Design"). Read it; it's the source of truth for the tickets.
- **The tickets:** `docs/agent-harness/fix-lens/tickets/FXL-1.md` to `FXL-7.md` in this repo. Copy them; don't
  edit them. If one is wrong, say so on PR #47.

**Order:** do D5's deploy and D5.1 first. The tickets start only after the user has run the D5.1 `sudo` lines and
you've verified the renames are refused. Before that, do the setup steps below and stop.

## Setup (approved here; all reversible)

1. **Repository:** create `/srv/lab/agent-harness/work/fix-lens`, a local git repo with branch `main`. Its
   initial commit, which you make as the operator, holds:
   - `package.json`: `"type": "module"`, with exact-version dev dependencies `vitest`, `jsdom`,
     `@stryker-mutator/core` and `@stryker-mutator/vitest-runner` (10.x). Use the versions D4 used where they
     overlap;
   - `.gitignore` with `node_modules` (no trailing slash, as in D4);
   - `vendor/orchestra/`: `OrchestraFIX42.xml` and `OrchestraFIX44.xml` from
     github.com/FIXTradingCommunity/orchestrations, folder `FIX Standard`, at the **current commit of its default
     branch**, plus the repository's `LICENSE` (and `NOTICE`, if there is one), and a `SOURCE.md` naming the
     commit sha and the file paths;
   - a one-line `README.md`.
2. **Dependencies:** install them into the D5.1 layout, at `/srv/lab/agent-harness/deps/fix-lens/node_modules`.
   It's root-owned once the user runs the lockdown. Install before the lockdown if you can; afterwards, a
   reinstall needs `sudo`, which is a stop.
3. **Overlay:** add `[repos.fix-lens]` with its own overlay file in the kit, as `fixture-js-repo` has, with
   `test_dir = "test/"` and `deps_dir` pointing at the folder above.
   - That's a kit change: commit it, post it on PR #47 for review, and deploy the reviewed sha to the host kit
     (and to the container copy) as D5 describes.
   - Overlays come from the code root now, so an unreviewed overlay never reaches the host.
4. **Load the tickets** into the queue in rank order, with their `blocked_by` links. Don't start the dispatcher
   on them until the order line above is satisfied.

## The run

- **Settings:** every stage runs live, with nothing played by hand. `[fixloop]`, `[risk]` and `[mutation]` (in
  the container) stay on.
- **After each ticket completes, put its evidence in this repo:**
  - write `git format-patch` of the ticket's approved commits (from the trusted `main`) to
    `docs/agent-harness/fix-lens/runs/FXL-<n>.patch`;
  - add a short `FXL-<n>.md` next to it with the models, cost, tier, gates, findings and proofs, mutation
    survivors, and whether a fix pass ran;
  - push, and comment on PR #47. I review each ticket from the patch while the next one runs.
- **When a ticket blocks for a human** (needs_input), the queue holds, as designed. Write the block reason and
  the run files' summary into `FXL-<n>.md`, comment on PR #47, and wait. Don't unblock it yourself. I'll answer
  with a review file, or the user will.
- **Nothing is changed by hand** in the `fix-lens` repo or its trusted `main` during the run.

## Done means

All 7 tickets are completed on the trusted `main`. Then:
- **The full suite:** the trusted `main`'s whole Vitest suite passes when run in the container.
- **The page works:** `index.html` is served from a static server in the container (for example
  `npx http-server` from `deps`, or `python -m http.server`) and loaded with Playwright, if it's available
  there. Check:
  - the CSP meta tag is present;
  - a sample log decodes;
  - a `<script>` payload in a field value shows as text.
- **Report** as `D6-fixlens.md`: a per-ticket table and the totals.
