# FXL-3 block: find out before changing anything

The planner says `write_file` is refused because `HERMES_WRITE_SAFE_ROOT=/opt/data`. This setting appears nowhere
in our reports, and planners have written to `work/runs/<KEY>/` every night until now, FXL-1 included. Either
something changed tonight, or the model's explanation is wrong. **Investigate read-only first.**

## Check (nothing changed by these steps)

1. **Is the variable set, and where?**
   - In the container's environment: `docker exec hermes env | grep -i SAFE_ROOT`, names and values only.
   - In `/opt/data/.env`, each profile's `.env` and `config.yaml`, and the gateway's s6 service files. Grep for
     the name; don't print other values.
   - When it was set: file mtimes, and the container's start time (`docker inspect -f '{{.State.StartedAt}}'
     hermes`).
2. **Why did FXL-1's planner succeed?**
   - Read its session in the planner's `state.db`, read-only: which tool wrote `plan.json`?
   - Compare that with FXL-3's: which tools did it try, and what exact error did each return?
3. **What does Hermes itself say?** Find the variable in the installed Hermes source (`grep -rn
   WRITE_SAFE_ROOT`) and its docs. Does it take several roots? Is it a default when unset? Did a Hermes update or
   a restart tonight bring it in (the gateway log and `hermes --version`)?
4. **Did our own lockdown cause it?** For example, does Hermes fall back to a safe root when a path it checks is
   now root-owned?

## Decision rules (approved here; report what you did)

- **The model was wrong** (it never actually called `write_file`, or the error is something else): unblock
  nothing yourself. Write the finding, and I'll decide whether the card is rerun.
- **The variable is set in a profile or Hermes config file, and adding exactly
  `/srv/lab/agent-harness/work` as a second root restores the old behaviour:**
  - make that one change, for the worker profiles only: triage, planner, implementer, scribe;
  - then do one documented gateway restart;
  - record the undo;
  - then unblock FXL-3's planner card **once**, as a `capability` fix (the card never ran its stage).

  Workers must never get write access to `/srv/lab` as a whole: `work/` only.
- **It needs the container recreated, or a change to its environment:** that's the user's step. Stop and write it
  up, with the exact command and its undo.

Report as `FXL-3-investigation.md`.
