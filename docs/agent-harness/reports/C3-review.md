# C3 review (`agent-harness@e043d5f`)

**Approved.** Verified in the reviewing session: `112 passed in 47.83s`, and ruff is clean.

- **Backup:** the 03:00 run on 2026-11-25 succeeded and pushed, and the redaction held (names-only scan).
  That closes the A4 follow-up.
- **`relink_bounced`:**
  - only acts when the bounced ticket's `triage` is blocked and the next ticket's `triage` is still `todo`;
  - leaves dependent tickets waiting;
  - keeps the order by re-linking to the nearest earlier `scribe`;
  - logs every change.

  A ticket's direct `blocked_by` links stay as they are, so the dependency rules still hold.
- **`copy_nofollow`:** with `O_NOFOLLOW` component by component, the symlink race is closed, and there are
  tests for both ends.

## Small hardening (with the next kit change)

`work/cards/queue.json` is in `/srv/lab`, so the container can write it. A worker could edit it to make the host
runner re-link cards in another order. The worst case is reordered or blocked tickets: the approval checks
(lineage, and base == trusted `main`) still stop bad code reaching `main`. Even so, write the queue file next to
the trusted repo in the host-only state folder, `~/.local/state/agent-harness/`, and read it from there.

## Design answer: deterministic gatekeeper

**Keep the card graph as it is.** Treat `gatekeeper` the way `reviewer` is treated:
1. Remove `gatekeeper` from `kanban.dispatch_profiles`, so no model ever works the card.
2. The host runner's pass also takes one ready `gatekeeper` card:
   - claim it;
   - validate the run files (`read_run_files`, then base == trusted `main`);
   - run `harness.gates` **inside the container**, through a `gates_cmd` template like `prove_cmd`
     (`docker exec --user hermes ... -m harness.gates ...`, failing closed if it isn't set);
   - read `gates.json`;
   - **complete** the card with the report as metadata on exit 0, or **block** it on exit 1, with the failing
     fields in the reason; exit 2 is a `transient` block.
3. **Order of each pass:** relink, then gatekeeper, then reviewer. The one-attempt rule applies to gatekeeper
   cards too.
4. **Tests:**
   - pass, fail and harness error each map to complete, block and transient;
   - a missing `gates_cmd` fails closed;
   - a card is never claimed when its run files are invalid.

This removes the model from the only stage that should be purely mechanical, and keeps the board readable.

## User decision (asked separately)

The Telegram alerts as a Hermes no-agent cron script create a cron job and a script in the Hermes data folder,
so they need the user's go.
