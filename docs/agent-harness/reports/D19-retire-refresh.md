# D19: retire hidden tests by decision, refresh the host copies from a named commit (D19-review.md)

Branch `d19-retire-refresh` in agent-harness, on master `0f8acf4`, at **`76b094f690289ea55e6e48de58b349f27c161ef6`**. Not merged, not deployed. No ticket loaded, no live state changed.

## Test output (fresh clone)
```
479 passed, 3 skipped in 32.67s
ruff check: All checks passed!      ruff format --check: 84 files already formatted
tests/test_d19.py: 38 passed in 2.21s
```

## Read this before deploying
**After this deploy, every `fix-lens` review and acceptance run refuses until a `refresh_copies` decision has been applied** ("no record of the host copies"). Today's copies were made by hand and nothing records them, so I treat them as unverified rather than trusting them. The order after the deploy, matching your suite README:
1. `refresh_copies` (the commit to take),
2. `retire_hidden` for the first two tests,
3. only then load (and only after D20, per HIDDEN-suite-review).

The old evidence driver would also get the refusal and hold; it is stopped.

## `retire_hidden` `{id, action, key, tests, reason}`
All or nothing: every id must be in the history's `passed` list, written exactly. An unknown id, a glob or a repeat rejects the whole decision. The ids leave `passed`; `{id, tests, reason, at}` is appended to `retired`. The acceptance summary and its markdown name retired ids that are not passing **apart from** regressions; any other vanished test is still a regression. A retired id that passes again is back in `passed`.
- **An ordering trap that follows from that last rule:** if an acceptance run happens while a retired test's old file is still in the host folder and the test still passes, it returns to `passed`, and the later refresh that removes it is then a regression. Your order (retire, delete, refresh, then load) is safe because runs happen only after a landing.

## `refresh_copies` `{id, action, key, commit, reason}`
- Reads blobs from the host-only bare mirror at exactly `commit`, which must be an ancestor of the fetched branch head. A missing or non-regular file, or an empty hidden folder or design, rejects it with nothing changed.
- Paths come from the new `[copies.fix-lens]` table in `harness.host.toml`. Only files matching `*.test.js` are taken from the folder (not the README). The hidden folder is replaced whole, so a file deleted in the repository disappears.
- **Order:** read everything; write the workers' reading copies; swap the host copies; write the record **last**. A failed reading copy rejects the decision and leaves host copies and record as they were. A crash after the swap leaves copies that don't match the record, which blocks.
- **Reading copies** go to the four paths I listed on the PR (`work/specs`, the `hermes` user's home, the implementer's and planner's `~`). They are written **inside the container as `hermes`**, never from the host: those folders belong to workers, and a planted link must not redirect a host write. Nothing is enforced from them. A new profile that needs the design has to be added to the list.
- **While a card of the repository is `running`** (matched by the card's workspace path), the decision is not recorded and is tried again on a later pass. **Later decisions wait behind it,** to keep id order; so a `fix-lens` unblock queued after a refresh waits too. It is logged each pass, not posted. As written it looks at `running` only: a card that is `ready` could be claimed during the second or so the refresh takes.

## Verification
`copies.verify` checks the design and **every** hidden file against the record: a changed, missing, extra or symlinked file, no record, or a corrupt record all fail.
- **Review:** checked before any model call. A failure blocks `needs_input`. With the spec pass on, every `spec_docs` entry must be the recorded copy, so an extra unrecorded document also blocks. `review.json` gets `copies: {commit, design_sha256, hidden_files}`.
- **Acceptance:** when `--hidden` is the configured host folder, it is checked first (exit 2 if it fails), and the summary and markdown carry the commit and file count. Any other folder is a scratch run and is reported as having no recorded copy.

## Mutation
- `data_modules` paths are left out of the mutation ranges.
- The engine's whole output (up to 5 MB) is now written to `mutation-output.log` in the run folder, and named in the gate field; a fix pass keeps the first run's log as `mutation-output-<n>.log`. The write replaces the file, so a link planted in the worker-writable run folder is not written through. (Stryker only; mutmut is unchanged.)
- **Why Stryker exited 1 on FXL-8: not the size of the files.** I reproduced it in a scratch folder with the container's code on head `e721f31`. Stryker's unmutated first run failed one test, `test_dictionary_temp_build_matches_committed_without_src_writes` (`expected false to be true`), **with the data modules in the ranges and also with them left out**. The cause was our setting `disableTypeChecks: true`: Stryker then adds `// @ts-nocheck` to the files it copies, so a byte-for-byte comparison with the committed file fails. With it `false` (data modules left out), the first run passed all 42 tests and mutation completed in 13 s: **39 killed, 12 survived, 8 without tests**. The setting is now off. These are plain JS files, so there are no type checks to disable.
  - The scribe had noted this during FXL-8, in its own skill file. I did not check whether the same setting explains FXL-3B's "0 killed of 83".

## D18 test id
`pytest.param(..., id="deep-nesting")`.

## Tests (`tests/test_d19.py`)
Retire: removed and logged, applied once; one bad id (unknown, glob, partial name, repeat) rejects all; non-lists refused; another vanished test still regresses; a retired id that passes again is a pass.
Refresh: content from the commit while the worktree differs; an older ancestor works and replaces the whole folder; a non-ancestor and an unknown commit are rejected; missing design or hidden files change nothing; a repository symlink is refused; a failed reading copy changes nothing; deferred while a repository card runs, with the later id waiting; another repository's card doesn't defer.
Verification: six kinds of tampering and a symlinked copy are refused; the acceptance check; the real reviewed config agrees with the overlay; through the real reviewer, `review.json` records the commit and sha, and a tampered, unrecorded or extra document blocks `needs_input` with no model call.
Mutation: data modules excluded and `disableTypeChecks` false; whole output kept; a planted link replaced.
One D15 test changed its expected wording ("list of paths" to "list of strings").

## Checked beyond the unit tests
- On the real review branch (head `13a9ffa`), a refresh into a **scratch** state folder took the design (sha256 `4de073a8…`) and 17 hidden files, and they verified.
- The container writer wrote a probe file under `/tmp` in the container; removed afterwards.
- Real stage cards carry `workspace_path` `/srv/lab/agent-harness/work/fix-lens`, which the running-card check matches.
- **Not run live:** either new decision through the deployed runner, and the reading copies at their four real paths.

## Created and deleted in this job
Deleted: the scratch folder `work/scratch-d19-mut`, the scratch state `/tmp/d19-scratch-state`, the container probe folder `/tmp/d19-probe-dir`.
