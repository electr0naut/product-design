# D25, second commit: `harness-deploy` refuses while a worker card is running (D25-code-review)

Branch `d25-runner-actions`, **final commit `5b6c863f6cb4b61d41333d79b32e40276820238a`**, one commit on the approved `264c8e4`. **Not merged, not deployed.** Waiting for your review.

## ⚠ The D25 deploy itself is **not** protected by this
`harness-deploy` runs the **deployed** kit's copy of `tools/deploy.py`. That is `b20b702`, without the refusal. So the deploy that installs D25 will go through even with a card running, and **has to be timed by hand.** The refusal applies from the deploy after it. (The wrapper file itself does not change.)

## Built (`tools/deploy.py` and its tests only)
- It reads the board and refuses if any card is `running` and has an assignee, in any repository, **naming each card and its id.** Gate cards have no assignee.
- Checked **twice:** after the password prompt, and again **just before the host kit is switched** (the prompt can wait a long time). On a refusal, the host kit, the container copy and the recorded sha are unchanged; git objects may have been fetched into the container copy, which moves nothing.
- **A board that cannot be read refuses.**
- **No override flag.** This includes a rollback, which is the same command with the old sha: with a card stuck in `running`, the card has to be dealt with first.
- `--dry-run` prints the board read and judges nothing.
- **Limit:** a card that starts in the seconds between the second read and the end of the switch is not stopped. The dispatcher can start a ready card at any time; holding it back would need a change outside this tool.

One existing test, `test_the_alert_script_is_copied_only_when_it_changed`, lists the `docker` calls; I excluded the new board reads from that list, as it already excludes `inspect`. Its assertions are unchanged.

## Tests
Fresh clone of `5b6c863` in the proof container (ruff and format clean):
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
674 passed, 3 skipped in 81.13s (0:01:21)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 276; started without HOME: 0
```
`tests/test_deploy.py`:
```
test_a_bad_sha_is_refused_before_any_command_runs PASSED [  5%]
test_a_fast_forward_deploys_host_kit_and_container_and_prints_the_undo PASSED [ 11%]
test_a_non_fast_forward_is_refused_and_nothing_is_touched PASSED [ 16%]
test_a_sha_the_clone_does_not_have_is_refused PASSED [ 22%]
test_the_alert_script_is_copied_only_when_it_changed PASSED [ 27%]
test_dry_run_runs_nothing_and_prints_every_step PASSED [ 33%]
test_the_wrapper_runs_the_host_kits_copy_and_never_lives_in_the_container_kit PASSED [ 38%]
test_a_deploy_is_refused_while_a_card_runs_and_names_it[scribe] PASSED [ 44%]
test_a_deploy_is_refused_while_a_card_runs_and_names_it[reviewer] PASSED [ 50%]
test_a_deploy_is_refused_while_a_card_runs_and_names_it[gatekeeper] PASSED [ 55%]
test_a_deploy_is_refused_while_a_card_runs_and_names_it[implementer] PASSED [ 61%]
test_a_deploy_goes_through_when_no_card_is_running PASSED [ 66%]
test_a_card_that_starts_before_the_switch_still_stops_it PASSED [ 72%]
test_a_board_that_cannot_be_read_refuses[] PASSED  [ 77%]
test_a_board_that_cannot_be_read_refuses[not json] PASSED [ 83%]
test_a_board_that_cannot_be_read_refuses[{"a": 1}] PASSED [ 88%]
test_a_board_that_cannot_be_read_refuses[[{"title": "x"}]] PASSED [ 94%]
test_there_is_no_override_flag PASSED              [100%]
============================== 18 passed in 1.30s ==============================
```
**Against the real board,** read-only, at 15:37, with the branch's check function (it only lists the board):
`refuses: a worker card is running: FXL-16 · implementer (t_22102270). Nothing was changed. Deploy when no card is running.`

After the D25 deploy I will apply nothing myself: the `load_tickets` decision that must be refused (FXL-16) is yours to write, and I will report its comment.
