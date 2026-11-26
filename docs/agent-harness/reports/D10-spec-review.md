# D10: the spec-conformance pass and the hidden acceptance suite (branch `d10-spec-review` @ `2057626`, on `master` `4b16baa`; NOT merged, NOT deployed)

Pushed as a branch only. From a fresh clone of the branch: `335 passed, 3 skipped` (`310` before, 25 new tests), `ruff check` and `ruff format --check` clean. `master` is unchanged; the branch is a fast-forward of `4b16baa` (checked). Files: `src/harness/specs.py`, `src/harness/acceptance.py`, `schemas/spec_findings.json`, `tools/record_tickets.py`, changes in `reviewer.py`, `loader.py` and the FIX Lens overlay, and tests `test_spec_pass.py` and `test_acceptance.py`.

## 0. The hold before FXL-4 (done now, board only)
FXL-1b, FXL-2b and FXL-3b run on untouched. Commands, 09:58:
- `hermes kanban create "HOLD: D10 deployed" --body-file work/hold-d10.md --idempotency-key hold:d10 --json` → `t_01fb15de` (unassigned, so nobody works it);
- `hermes kanban link t_01fb15de t_1b78b35c` (FXL-4's `triage`; its other parents are unchanged: FXL-3's and FXL-1's scribes, and FXL-3b's).
FXL-4 triage shows `todo` with the hold among its parents. I complete the hold card once the user says D10 is deployed.

## 1. The spec pass (in `Runner.review`, after the finder, before the refuter)
- **Inputs, all host-only.** `loader.load` now records each ticket's whole file under `~/.local/state/agent-harness/tickets/<KEY>.md`, next to `labels.json` (atomic write; a key must look like `FXL-2b`, so no path tricks). Spec documents come from `[review] spec_docs` in the overlay; for `fix-lens`: `~/.local/state/agent-harness/specs/fix-lens/technical-design.md`. A path must be absolute (`~` allowed) and not inside the kit folder (which the container mounts). Missing or empty ticket text, or a missing/empty spec document, blocks `needs_input` **before any paid call**. The diff is D9's chunks plus the excluded list; Claude gets Read on the trusted worktree.
- **The call:** one `claude -p --json-schema` call, same model and budget settings as the refuter, schema = the findings schema plus a required `spec_ref` (`schemas/spec_findings.json`). The prompt asks only for deviations from quoted text (interfaces, names, design rules, reference values, which it must work through the code) and never style.
- **Quote check:** `spec_ref` must appear in the ticket or a spec document, word for word, whitespace runs aside (a quote that wraps over lines still matches); shorter than 12 characters counts as no quote. Failures are dropped and listed in `review.json` under `spec_pass.dropped`, with `spec_pass.ran` and `spec_pass.docs`.
- **After that:** spec findings (`"source": "spec"`) are appended to the finder's, everything is renumbered, and the same filter, refuter (its prompt now says to judge a finding with a `spec_ref` against that quote, not only the acceptance criteria), prover and `decide` run. A proven spec finding starts the review-triggered pass exactly as today; the feedback carries the `spec_ref`. Unproven critical/high ones are `blocking_unproven`.
- **Budget:** exactly one spec call per review; its cost is in `cost_usd`. If the card budget would be exceeded the run blocks `transient` (it is not skipped); a diff over `[review] spec_max_chars` (default 400000) blocks `needs_input`. A bad reply blocks `transient`.
- **Off by default.** Only `[repos.fix-lens]`'s overlay sets `spec_pass = true`; other repos and the container config are unchanged (a test checks it).

## 2. The hidden acceptance suite
- `src/harness/acceptance.py` (`python -m harness.acceptance --repo --hidden --history --ticket [--markdown]`) runs the whole hidden folder against the trusted `main` through `harness.score` (inside the container, as before), compares every test with a host-only history of tests that ever passed, and reports per file `passed/total`, newly passing tests and **regressions** (a test that passed before and does not now, including one that vanished). The history is not shrunk by a regression, so it stays flagged until it passes again; a corrupt history or an empty hidden folder is an error. Exit 4 on a regression.
- `tools/fixlens_driver.py` (branch `d6-driver`, `8da312e`; the driver is operator tooling, not deployed code) now runs it after every ticket, appends it to `FXL-<n>.md`, and on a regression creates `HOLD: acceptance regression after FXL-<n>` linked to the next ticket's triage, comments on PR #47 and stops. It says "not enabled" until the host folder exists. **The acceptance folder `docs/agent-harness/fix-lens/acceptance/` does not exist yet** (you write it); the driver stays inert until you do and the copy below is run.

## Things to know
- **My slip, already repaired:** my first run of the new tests wrote four `PRC-1` entries into the live fix ledger (the new test file imported fixtures without the autouse ledger redirect). They were mine (all 10:01, a fake key); I removed exactly those four entries (a copy of the ledger before the cleanup was kept) and `proofs/PRC-1`; the ledger is back to its 8 entries, and the file now imports the redirect. `test_loader.py` also redirects `risk.TRUSTED_ROOT`, so a test load can no longer write `labels.json` or `tickets/` into live state; a check after the full suite shows the live state untouched.
- Tickets loaded before D10 (FXL-1b, FXL-2b, FXL-3b, FXL-4 to FXL-7) have no recorded text, so their reviews would block until `tools/record_tickets.py` is run (step 4).
- One spec call with the whole diff and the design (about 60k characters for FIX Lens) can cost more than the refuter's per-call limit of $0.75; if `claude -p` reaches its own budget cap the call fails and the card blocks transient. I did not raise any limit.

## The lines for the user (in this order; nothing is deployed yet; after your review fast-forwards `master` to `2057626`)
1. **Host kit** (undo: the same line with `4b16baa9c88a`'s full sha from `git -C ~/dev/agent-harness rev-parse 4b16baa`):
```
! cd ~/dev/agent-harness-d10 && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/deploy_host_kit.py 20576261b34a089b0a4a8828dde3bf3cfa00117f
```
2. **The container's copy** (bundle, hardened flags; the last line prints the sha; undo: `sudo git -C /srv/lab/agent-harness reset --hard 4b16baa`):
```
! git -C ~/dev/agent-harness-d10 bundle create /tmp/kit.bundle d10-spec-review
! sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false fetch -q /tmp/kit.bundle refs/heads/d10-spec-review && sudo git -C /srv/lab/agent-harness -c core.hooksPath=/dev/null -c core.fsmonitor=false merge --ff-only FETCH_HEAD && sudo git -C /srv/lab/agent-harness rev-parse HEAD
```
3. **The design document, host-only** (from the reviewed product-design repo; the review reads only this copy):
```
! mkdir -p ~/.local/state/agent-harness/specs/fix-lens && cp ~/product-design/docs/agent-harness/fix-lens/technical-design.md ~/.local/state/agent-harness/specs/fix-lens/technical-design.md
```
4. **Ticket text for the tickets already loaded** (host kit, after step 1):
```
! cd ~/.local/share/agent-harness/kit && for t in FXL-1b FXL-2b FXL-3b FXL-4 FXL-5 FXL-6 FXL-7; do cp ~/product-design/docs/agent-harness/fix-lens/tickets/$t.md /tmp/$t.md; done && PYTHONPATH=src /srv/lab/agent-harness/.venv/bin/python tools/record_tickets.py /tmp/FXL-1b.md /tmp/FXL-2b.md /tmp/FXL-3b.md /tmp/FXL-4.md /tmp/FXL-5.md /tmp/FXL-6.md /tmp/FXL-7.md
```
5. **The hidden suite, once it exists** (host-only copy; run again when the folder changes):
```
! mkdir -p ~/.local/state/agent-harness/acceptance/fix-lens && cp ~/product-design/docs/agent-harness/fix-lens/acceptance/*.test.js ~/.local/state/agent-harness/acceptance/fix-lens/
```
Then I restart nothing (the runner picks up the new kit on its next timer tick; the driver already has the code), complete the hold card `t_01fb15de`, and FXL-4 starts under the spec pass. Note for FXL-1b/2b/3b: if one of their reviews starts after step 1 and before step 4, it blocks `needs_input` for missing ticket text, so run 3 and 4 together.
