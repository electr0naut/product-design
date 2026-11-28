# D11: full test collection, one bad card never stops the runner, one key pattern, stall alerts, attempt reset (branch `d11-robustness` @ `0ae59d0`; NOT merged, NOT deployed)

Pushed as a branch only, on `master` `386315c` (a fast-forward of it, checked). From a fresh clone of the branch:
`356 passed, 3 skipped` (`338` before, 18 new tests in `tests/test_d11.py`), `ruff check` and `ruff format --check` clean.
Nothing on the host, in the container or on the board was changed for this. FXL-1B stays blocked, the driver is stopped.

## 1. Test collection keeps the whole output
- New `gates.run_collect` runs the `collect` command and keeps **all** of its output. Over `[gates] max_collect_bytes`
  (default 5,000,000; set in `harness.toml` and `harness.host.toml`) it raises a `HarnessError` (the runner exits 2 and
  the card blocks with the reason): it never parses a clipped list. `collect_ids` uses it; a timeout is still `124`.
- Tests: 500 ids (about 70 KB, the old code kept about 30) are all seen, in order; an output over the limit is a harness
  error naming `max_collect_bytes`; the limit is in both config files.
- **Audit of every other parse of `run_cmd`'s clipped output:** none found. The other callers read only the exit code or a
  file: `gates` test_one (exit code), `_step` (exit code; the 1000-character tail goes in a report only), `score`
  (JUnit XML; the output only fills an error message), `reviewer` proof runs (exit code and XML), `gatekeeper`
  (exit code and `gates.json`). `mutation` already used `run_full`. `collect_ids` was the only parser.

## 2. One bad card never stops the runner
- New `reviewer.pick_card`, used by both `run_once` (reviewer) and `run_gatekeeper_once`: it goes through the ready
  cards in order, blocks each one whose title has no readable key (`needs_input`, reason `... cannot read the ticket
  key from card title '...'`) and carries on with the first good one. A run file or branch problem was already a
  `needs_input` block of that card (`RunFileError`); unchanged.
- Tests: a card titled `FXL-1b · gatekeeper` ahead of a valid card is blocked and the valid card is processed in the
  same pass (gatekeeper and reviewer); with only bad cards the pass blocks them and returns normally.

## 3. One key pattern, enforced at load
- New `src/harness/keys.py` defines the key pattern once (`[A-Z][A-Z0-9]*-[A-Z0-9]+`), the card-title match, the
  branch pattern, and `check_key`, whose message names the allowed form. Imported by the loader, `reviewer`,
  `gatekeeper` (its own copy is gone), `trusted` and `specs`. A test greps the package: no second copy of the pattern.
- The loader rejects a ticket key **and every `blocked_by` key** that the runner can't read:
  `key 'FXL-1b' is not allowed: use an upper-case prefix, a dash, then upper-case letters or digits (for example FXL-1B)`.
- Side effect, on purpose: `specs` accepted lower-case after the dash before; it now refuses it, like everything else.
  One existing test used `FXL-2b`; it now uses `FXL-2B`.

## 4. Stall alerts
- `tools/harness_notify.py` is the new version of the container script `/opt/data/scripts/harness_notify.py` (the
  "Harness kanban alerts" no-agent cron, every 2 minutes, to Telegram). The blocked-card and finished-ticket lines are
  unchanged and the old state file (a bare list) still loads. New:
  - one ping when no card has changed state for 45 minutes while any card is `ready` or `running` (the clock is a
    signature of every card's id and status; one ping per stall; any change re-arms it);
  - one ping when the host runner has failed 5 passes in a row. The container can't see systemd, so
    `harness.reviewer.main` now writes `work/runner-status.json` after each pass (`ok`, `consecutive_failures`,
    `failing_since`, last message; a skipped pass because another one is running records nothing; a good pass resets
    the count). The script reads that file. It is a report only: nothing in the harness reads it.
- Limit: a crash before `main` runs (for example an import error) writes no status; the stall alert still catches it
  within 45 minutes.
- Tests: 44 minutes is silent, 45 pings once; a state change re-arms it; a board with nothing ready or running never
  pings; 5 failures ping once per streak, a good pass resets, a new streak pings again; the old state format loads;
  the runner records failures, a skip and a success. I also ran the real script once against a fake `hermes`.

## 5. A recorded attempt reset
- `tools/reset_attempt.py KEY --reason "..." [--base SHA | --repo NAME]`. It appends
  `{"key", "reset": true, "base", "reason", "at"}` to `fix-ledger.json`. Without `--base` it uses the trusted `main` of
  `--repo` (default `fix-lens`), which is what a reload will use. It refuses: no reason or a blank one, a base that
  isn't a 40-character sha, a key that isn't allowed; a refused reset writes nothing.
- `fixloop.attempt_entries` (which `kind_used` and the stored-proof reruns use) counts only the passes after the latest
  reset with the same key and base. A pre-D7 entry with no base counts against every base, and a reset clears it for
  the reset's own base only (it still counts against other bases: fails safe). Pass numbers still count every pass ever
  written (`passes_used` ignores resets), so card titles and stored proofs never clash.
- Tests: passes before a reset don't count and passes after do; a reset touches only its key and base; a reset needs a
  reason and a real base; the tool writes the entry (run as a subprocess against a throwaway trusted repo).

## Things to know
- Nothing in D11 touches FIX Lens tickets or the gates' decisions apart from the collection fix, so the **landed
  tickets** (FXL-1 to FXL-3) are exactly as the instruction describes: possibly gated on a partial list, covered by the
  review and the hidden suite. I did not re-gate them.
- After the deploy, FXL-1B's reset needs the base that the old passes recorded. The old attempt's base is
  `f36221cfc647c8981d3b190ced10a95c97d63baf`, the same as the trusted `main` today (nothing landed since), so the default
  works; I will pass `--base` explicitly and print the ledger entry.

## The lines for the user (in this order; nothing is deployed; after your review fast-forwards `master` to `0ae59d0`)
1. **Host kit** (undo: the same line with `386315c9692596abf96bfeb9dc0d6f1cf3343743`):
```
cd ~/dev/agent-harness-d11 && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/deploy_host_kit.py 0ae59d0809692efa9bb17033ef69b25d761ef79f
```
2. **The container's copy** (bundle, hardened flags; the last line prints the sha; undo: `sudo git -C /srv/lab/agent-harness reset --hard 386315c`):
```
git -C ~/dev/agent-harness-d11 bundle create /tmp/kit.bundle d11-robustness
sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false fetch -q /tmp/kit.bundle refs/heads/d11-robustness && sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false merge --ff-only FETCH_HEAD && sudo git -C /srv/lab/agent-harness rev-parse HEAD
```
3. **The alert script** (the container's copy; the old one is kept; undo: copy the `.bak-d11` back):
```
docker exec hermes cp /opt/data/scripts/harness_notify.py /opt/data/scripts/harness_notify.py.bak-d11
docker cp ~/dev/agent-harness-d11/tools/harness_notify.py hermes:/opt/data/scripts/harness_notify.py
docker exec -u root hermes chown hermes:hermes /opt/data/scripts/harness_notify.py
```
Then I run the reset, archive FXL-1B's cards, move its run folder aside and reload FXL-1B, FXL-2B, FXL-3B and FXL-4 to FXL-7 in one call, as `D11-review.md` says. The runner picks up the new kit on its next timer tick.
