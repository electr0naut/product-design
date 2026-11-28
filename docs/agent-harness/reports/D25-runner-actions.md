# D25: routine actions become runner decisions (D25-D26-review)

Branch `d25-runner-actions` of `agent-harness`, commit **`264c8e49a812035525bedf3b596e1f7e3355104e`**, one commit on `b20b702`. **Not merged, not deployed.** Built and tested in a clone and throwaway containers.

**Also done, `D24-code-review.md`:** `master` fast-forwarded from `6c483e6` to **`b20b702`**. Checked right after: the host kit and the container copy are still `6c483e6`. Not deployed.

## The three additions
**1. `load_tickets`** `{id, action, key, tickets: [..], commit, reason}`
- Reads each file from that commit of the runner's host-only mirror of the published branch; the commit must be on that branch. Folder: new `[tickets.fix-lens] dir` in `harness.host.toml`.
- **Every file is read and checked before any card is made.** Refused, loading nothing: a key already in the registry or with a triage card on the board; a missing file; a file that does not parse or holds another key; a key listed twice; a `blocked_by` that is neither on the board nor **earlier** in the list.
- Same code as the tool (`loader.load`), with a new `as_given` flag so the list order is kept (rank would otherwise put FXL-14 before FXL-17). The tool behaves as before.
- Comment, per ticket: triage and gate card ids and what the triage waits on. This action's result line may be up to 3,000 characters instead of 400.
- **A failure part-way** (for example the board stops answering) is `rejected` with "THE LOAD FAILED PART-WAY", the tickets loaded in full, and a request to check the board. It is not retried. A subprocess error or timeout in any decision is now recorded as rejected; before, it would have left the decision `applying` with no comment.

**2. `rerun_mutation`** `{id, action, key, reason}`
- The tool's code moved to `src/harness/rerun.py`, so the runner can import it; its functions are unchanged (compared as syntax trees), and the tool is now only the command line.
- Refused, and not retried, while a card of the repository runs. A run whose mutation errors is `applied` and says so. The comment gives the counts, the range and the raw report's file name.
- **It runs inside the runner's pass,** which waits for it (up to the 5-minute cap and 2 minutes of margin; the unit allows an hour). Reviews and gate completions wait that long. The D22 limit remains: a card may start after the one check.

**3. A "fix pass edited or deleted base tests" block carries its evidence:** your five items, under "To decide this block". The files are the ones the block rule itself computes; "first head" is the ledger's, as the rule uses. A diff over 400 lines is cut with the counts. Its code fence is longer than any run of backticks inside, so a diff cannot close it. If the evidence cannot be built, the report says why and is still published.

## Where I departed from the spec, or filled a gap
- **Diffs come from the host-only trusted repository, not the work repository.** The kit's rule is that the host runs no git in a work repository, which workers can write to. The trusted one holds the same commits, fetched when the gates ran. If you want it from the work repository anyway, say so.
- `key` in `load_tickets` has to be a valid key; it is not required to be one of the listed ones.
- A **dropped** registry entry (a ticket archived for a reset or reload) does not block loading that key again.
- **`load_tickets` is not held back while a card runs.** The spec does not ask for it, the tool allows it (I loaded FXL-14 to FXL-16 while FXL-17's triage ran), and a deferred decision would hold every later one, an unblock included. Loading does re-sync the work repository's `main` with the trusted one. If you want a refusal while a card runs, it is a few lines.

## Tests
Fresh clone of `264c8e4`, the same proof container as for the guard (ruff and format clean):
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
663 passed, 3 skipped in 79.99s (0:01:19)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 276; started without HOME: 0
```
`tests/test_d25.py`, including each refusal, two tickets with the second waiting on the first's gate, applied once, and the block reports for a fix pass that adds tests and one that deletes one:
```
test_two_tickets_load_and_the_second_waits_on_the_firsts_gate PASSED [  3%]
test_the_list_order_is_kept_and_a_later_load_waits_on_the_open_gate PASSED [  7%]
test_the_files_come_from_the_named_commit PASSED      [ 11%]
test_a_decision_applied_twice_is_applied_once PASSED  [ 14%]
test_each_refusal_loads_nothing[files0-wanted0-FXL-15.md is missing] PASSED [ 18%]
test_each_refusal_loads_nothing[files1-wanted1-neither loaded nor in the list] PASSED [ 22%]
test_each_refusal_loads_nothing[files2-wanted2-listed before FXL-14] PASSED [ 25%]
test_each_refusal_loads_nothing[files3-wanted3-holds the ticket FXL-99] PASSED [ 29%]
test_each_refusal_loads_nothing[files4-wanted4-front matter] PASSED [ 33%]
test_each_refusal_loads_nothing[files5-wanted5-listed twice] PASSED [ 37%]
test_each_refusal_loads_nothing[files6-wanted6-ticket key] PASSED [ 40%]
test_each_refusal_loads_nothing[files7-wanted7-neither loaded nor in the list] PASSED [ 44%]
test_a_commit_that_is_not_on_the_published_branch_is_refused PASSED [ 48%]
test_a_ticket_in_the_registry_is_refused_even_without_cards PASSED [ 51%]
test_without_a_configured_folder_nothing_is_loaded PASSED [ 55%]
test_a_load_that_fails_part_way_says_what_was_made PASSED [ 59%]
test_a_long_result_is_not_cut_and_cannot_notify_anyone PASSED [ 62%]
test_a_rerun_decision_gives_the_counts_and_the_raw_report PASSED [ 66%]
test_a_rerun_decision_is_refused_while_a_card_runs_and_not_retried PASSED [ 70%]
test_a_rerun_that_errors_is_applied_and_says_so PASSED [ 74%]
test_the_new_actions_take_no_other_fields PASSED      [ 77%]
test_the_block_report_for_a_fix_pass_that_adds_tests PASSED [ 81%]
test_the_block_report_for_a_fix_pass_that_deletes_a_test PASSED [ 85%]
test_a_long_diff_is_cut_with_the_count PASSED         [ 88%]
test_the_diff_cannot_close_its_code_block PASSED      [ 92%]
test_another_block_gets_no_such_section_and_a_failure_does_not_stop_the_report PASSED [ 96%]
test_the_gatekeeper_and_the_report_use_the_same_words PASSED [100%]
============================== 27 passed in 2.25s ==============================
```
Stand-ins: the board, Docker and Stryker are fakes; git and the published branch are real. **Not run live:** neither decision has been applied against the real board or container; the first real use is after a deploy.

## Next: D26
Not started. As your instruction asks, I will first report how the standing session is started and with which settings, and propose the unit, settings file and fixed prompt.
