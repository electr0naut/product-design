# Phase B0 review

**Approved with changes.** The plan is well sourced and is careful about ownership (`-u hermes`),
credentials and the reviewer runner. Six items need fixing or a user decision before B1.

## Must fix before B1

**1. `gates.py` does not come from extraction.** `extract_literals.py` writes only the `File:` blocks in
BUILD_SPEC. `src/harness/gates.py` (M3) is a contract, not a literal file, so nothing produces it yet.
- **Add a B0.2 build step:** implement the M3 gates as a small stdlib-only package in
  `/srv/lab/agent-harness/`, covering FAIL_TO_PASS, PASS_TO_PASS, AC coverage, the test budget, and
  lint/test by exit code. Leave mutation out for now.
- **Tests:** use BUILD_SPEC's M3 acceptance tests (`tests/test_gates.py`) and run them on the host first.
- **Interpreter:** the container's Hermes interpreter is Python 3.14 (it appears in the container
  tracebacks as `/opt/hermes/tools/python-3.14.9`), not 3.12. Run the tests under that interpreter too
  before `gatekeeper` relies on it.
- **Already literal**, so the rest of the table in B0.1 stands: the schemas (`findings.json`,
  `readiness.json`, `refutations.json`, `proof.json`), the fixture, `mr_description.md` and the skills.

**2. The existing `command_allowlist` makes unattended workers unsafe. This is the user's decision, and it
blocks Phase C.** It allows `recursive delete`, `delete in root path`, `script execution via -e/-c`,
`overwrite system file via redirection` and `in-place edit of system config` for every profile, unattended
contexts included. A Kanban worker that has been misled, for example by text in a ticket, could then delete
or overwrite files with nobody asked.
- I recommend removing those five keys before any pipeline worker runs, and allowing only the exact
  commands each stage needs (B2).
- If any older automation depends on them, list it, and scope the keys to that profile instead of to all.

**3. Git for the pipeline must stay local.** Implementer cards work on `harness/<KEY>` branches.
- For the fixture, use a local repo under `/srv/lab/agent-harness/work/fixture-repo`, with no remote, so
  no git credentials enter the container.
- State this in B3. Workers never push anywhere; the scribe produces the MR text only.

## User decisions

**4. The redaction change was applied in this pass.** The A5 follow-up review said it needed the user's go
first.
- **Approval:** confirm the user approved it. If not, record it as a deviation; the original is kept at
  `redact-config.py.bak-20261124-a5`.
- **The pattern over-matches, and that damages restores.** The widened match now redacts settings like
  `group_sessions_per_user`, `record_sessions`, `session_ttl_seconds` and `redact_secrets`, which are
  booleans and numbers. A config restored from the backup would carry `REDACTED` strings in typed fields.
  - **Fix:** keep the wide name pattern, but redact only non-empty string values. Skip names ending in
    `_env`, because those hold variable names, not secrets.
  - **Test** it as before, on a temporary copy, names only, and with the user's go.

**5. Gateway restart in B2.** Restarting the gateway briefly restarts the Telegram and Discord bots. Ask the
user at that moment, as the plan says.

## Good as written

- Reviewer runner design: atomic claim, lock file, heartbeat, credentials kept on the host.
- The two open questions go to a dummy-card test: does a host-claimed card count against
  `max_in_progress`, and does `claim` work outside `dispatch_profiles`? Test them before B3.
- Fail-closed `dispatch_profiles`, which also keeps the 21 old roles and `default` off the board.
- Backup of `config.yaml` and `profiles/` before B1.

## Order (revised)

1. User decisions on items 2 and 4.
2. Backups.
3. B0.2: build the gates, with tests passing on the host and in the container.
4. B1.
5. B2: allowlist changes, config, then a gateway restart with the user's OK.
6. The dummy-card test.
7. B3: the loader and the runner.
8. PRC-1 smoke test, then the PRC-6 bounce test.

Report and wait for review after each step.
