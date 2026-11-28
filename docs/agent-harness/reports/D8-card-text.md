# D8: the card text states the real write rule (branch `d8-card-text` @ `feae6b2`, on top of `666cb30`; NOT merged, NOT deployed)

Pushed as a branch only (`git ls-remote`: `d8-card-text = feae6b206ba9`; `master` still `666cb30`). From a fresh clone of the branch: `297 passed, 3 skipped`, `ruff check` and `ruff format --check` clean. One deploy in the morning, as the review set out: this branch is stacked on D7, so its sha carries D7 too; the user deploys that single sha and then runs the ledger migration.

## What changed
The line every stage card carried, **"Write files with the file-writing tool, never with shell redirection or heredocs."**, is gone from both places that produced it (`loader.stage_body` for all six stages, and the fix-pass implementer card in `fixloop`). In its place, one helper `loader.write_rule(profile)`:

> Writing files: `write_file` works only under /opt/data. To create or change a file under /srv/lab/agent-harness/work, write a short Python script into /opt/data/profiles/<stage>/cache/scratch/ with `write_file` and run it with the terminal tool (the script writes the file). Never use `execute_code`, shell redirection or heredocs.

`<stage>` is the card's own profile (triage, planner, implementer, gatekeeper, reviewer, scribe; the fix-pass card says `implementer`), so a worker is pointed at a scratch folder it can really write to. The rule follows the review's wording: `write_file` only under `/opt/data`; scratch script plus terminal for `/srv/lab/agent-harness/work`; never `execute_code`, redirection or heredocs. Cards already loaded keep their old text (accepted: the morning's reruns reload them). The safe root is **not** widened.

## Tests (3 new in `tests/test_loader.py`)
Every one of the six stage bodies carries the rule with its own profile's scratch path and none carries the old line; the fix-pass body carries it with `implementer`, without the old wording; the rule's scratch path is inside `/opt/data`, which is what the safe root allows.
**A slip while building it:** a `sed` on a line number overwrote the wrong line of `write_rule` (the numbers had moved after an earlier edit) and 3 tests failed; I saw it in the next command, restored the line, and the suite passed. Nothing broken reached a commit.

## The other things in this report
- **D7-morning.md corrected** (an erratum at the top): its plain `sudo git fetch origin` line is wrong, as the follow-up review said (root has no GitHub login; it also lacked the hardened flags). I will not give the user a container-copy line myself; the reviewer will. For the bundle I will build it from the approved sha once `master` is fast-forwarded.
- **FXL-3 was unblocked once**, as approved (`kanban unblock t_702a1690`, 01:52). Its planner completed in 98 s (run #229) on a plan that was already on disk, and the implementer is running. **A correction to my own diagnosis:** the first planner session did not give up for good: after blocking itself it found the terminal route and wrote `plan.json` at 01:45, about a minute after I checked and wrote "never written". Both statements are corrected in `FXL-3.md`.
- FXL-3's evidence driver is running again; FXL-1 stays blocked and untouched.

## Not done
No merge, no deploy, no change to the Hermes config or the safe root, no change to `work/fix-lens`.
