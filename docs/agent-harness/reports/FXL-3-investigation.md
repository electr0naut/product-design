# FXL-3: the write-root block, investigated read-only (nothing was changed, nothing unblocked)

**Finding: the model's explanation was right, and nothing changed tonight.** `write_file` has always refused paths outside `/opt/data` in this container. Workers get files into `/srv/lab/...` through a workaround; FXL-3's planner did not find it. This is the third decision rule's case (the setting lives in the container's environment, not in a profile or config file), so I stopped and wrote it up.

## 1. Where the variable is set, and since when
- Container environment: `HERMES_WRITE_SAFE_ROOT=/opt/data` (`docker exec hermes env`, and `docker inspect` `Config.Env`, and `/run/s6/container_environment/HERMES_WRITE_SAFE_ROOT`).
- **It comes from the Hermes image itself:** `/srv/hermes/hermes-agent/Dockerfile:492: ENV HERMES_WRITE_SAFE_ROOT=/opt/data` (the line before it sets `HERMES_HOME=/opt/data`). Our `Dockerfile.lab` and `compose.yaml` (both last changed 2026-11-21 01:43) do not mention it.
- **Not in any file the review named:** `0` matches for `WRITE_SAFE` in `/opt/data/.env`, `/opt/data/config.yaml`, every profile's `.env` and `config.yaml`, and the s6 service files (only the s6 environment entry above).
- When: the container was created 2026-11-21 00:49, started 2026-11-24 09:04; the gateway has run since 2026-11-25 20:53; `config.yaml` last changed 2026-11-25 20:51 (the gatekeeper switch-on). Hermes reports version `0.0.0` (source checkout `fcc26fbd9f16`).

## 2. Why FXL-1's planner succeeded and FXL-3's did not (planner `state.db`, read-only)
- FXL-1's planner (session `483bd38a…`, 01:00): `write_file` into `/srv/lab/...` was denied, so it wrote a short script with `write_file` into `/opt/data/profiles/planner/cache/scratch/write_plan.py` (inside the safe root) and ran it with the **terminal** tool: `wrote /srv/lab/agent-harness/work/runs/FXL-1/plan.json (5174 bytes)`.
- FXL-3's planner (session `dfef03a1…`, 01:39): `write_file` to `/srv/lab/.../FXL-3/plan.json` → `Write denied: ... outside HERMES_WRITE_SAFE_ROOT (/opt/data)`; `execute_code` → refused ("blocked in single-query mode"); then **`kanban_block`** with the plan finished but unwritten. It never tried the scratch-script route.
- **"Planners wrote to `work/runs/<KEY>/` every night until now": true, but through that workaround.** Counting `write_file` results containing "outside HERMES_WRITE_SAFE_ROOT" per profile since 2026-11-25 18:41: planner has them in 6 sessions (25th 18:43, 20:57, 23:39, 23:49; 26th 01:00, 01:39), triage 6, implementer 6, scribe 6; the other profiles none. Nearly every worker session hits the wall once; most recover; this one blocked.

## 3. What Hermes says
`agent/file_safety.py`: `get_safe_write_roots()` reads the variable as an **`os.pathsep`-separated list** (`:` on Linux) and `write_file`/`patch` deny any path outside every root. The image sets it as a default. The source comment says the file tool restriction is "Defense-in-depth, not a security boundary; the terminal tool can still bypass". Env files are loaded with `override=True` (`env_loader.py`), so a profile `.env` entry would take precedence over the image default. I have not tried that.

## 4. Was it our lockdown?
No. The denial pattern predates it (first denial 25th 18:41; the lockdown ran at about 00:30 on the 26th), the message names only the safe-root rule, and the failing path's directory is writable (`work/runs/FXL-3` is `ubay:ubay 775`).

## Why this is a harness defect, not a model slip
Every stage card says **"Write files with the file-writing tool, never with shell redirection or heredocs."** For `/srv/lab` paths the file-writing tool cannot do that, so each worker has to rediscover a workaround. FXL-1 and many D4/Phase C sessions did; FXL-3's planner did not.

## Options (I did none; (a) and (b) are for you or the user)
**(a) Fix the card text (kit change, no Hermes change, no wider access). Recommended first.** Replace the line with the real rule: "`write_file` only works under `/opt/data`. To create a file elsewhere (the work folder), write a short Python script into `/opt/data/profiles/<your profile>/cache/scratch/` with `write_file` and run it with the terminal tool. Never use `execute_code`." I can build this as D8 on a branch (loader card text, a test that every stage card carries it), reviewed and deployed like D7.
**(b) Widen the safe root for the worker profiles.** Add `/srv/lab/agent-harness/work` as a second root, either:
 - per profile, in `/opt/data/profiles/{triage,planner,implementer,scribe}/.env`: a line `HERMES_WRITE_SAFE_ROOT=/opt/data:/srv/lab/agent-harness/work`, then one gateway restart. Undo: delete the line, restart. **I did not edit these files:** the variable is not set in any of them today, so the review's second rule (change it where it is already set) does not apply, `.env` files hold secrets, and I have not verified that a worker process honours the override; or
 - at the container level (`/srv/hermes/compose.yaml`: `environment: - HERMES_WRITE_SAFE_ROOT=/opt/data:/srv/lab/agent-harness/work`, then recreate). Undo: remove the line, recreate. **This is the user's step** (container environment change).
Either way, workers get the file tool on `work/` only, never on `/srv/lab` as a whole, and they already write there through the terminal tool.
**(c) FXL-3 itself** (needs a human decision; the planner card never ran its stage): unblock `FXL-3 · planner` (`t_702a1690`) once, or archive and reload FXL-3 alone. With (a) or (b) in place first, the retry will not hit the same wall.

## State
Board: `FXL-1 · reviewer (fix 1)` and `FXL-3 · planner` are `blocked`; no card is running, so nothing on the board moves until one of them is answered. Trusted `main` of `fix-lens` is still the operator's initial commit `544c8c5`. `work/fix-lens` untouched.
