# D26 setup fix: `ProtectHome=read-only` (D26-setup-review2)

`agent-harness` branch `d26-home-fix`, **commit `6ff69fa581344afabd67d07a0dc72628a03bc6f0`**, one commit on `master` (`25a315e`). **Not merged, not deployed.** Two files: the unit and its test.

- `harness-job@.service`: **`ProtectHome=read-only`**; `ReadWritePaths` and `InaccessiblePaths` unchanged. The comment now says that `strict` does not cover the home, and `ProtectHome` does. My D26 comment and report assumed it did.
- `test_d26.py`: the unit must hold `ProtectHome=read-only` (and `ProtectSystem=strict`). **With the line removed by hand, the test fails** (1 failed, 81 passed).
- Fresh clone in the proof container (ruff and format clean):
```
SKIPPED [1] tests/test_mutation.py:301: mutmut is installed in the container's .venv-mutation only
SKIPPED [1] tests/test_mutation.py:511: Stryker is exercised inside the container (node 26), not on the host
SKIPPED [1] tests/test_mutation.py:563: Stryker is exercised inside the container (node 26), not on the host
762 passed, 3 skipped in 86.49s (0:01:26)
-- files at the live paths:
identical: 68 files, 50 folders, same checksums before and after
-- live paths read, written or named to a child process: 0
-- python processes logged: 282; started without HOME: 0
```
**Not shown by any test:** that the unit, once installed, keeps the home read-only. Ubay's run showed the three settings do it in a transient unit; step 9 checks the installed setup.

## `D26-setup.md` (already updated on the branch; no code needed)
- A new section, **"After the home fix"**: stop the timer; one clean-up line (the cloud-check folders, `.probe`, `.probe2`, `.probe3`, `.claude`, `.claude.json`, `.claude.json.lock`); repeat the unit install and `daemon-reload`; probe again.
- Step 9: `-p ProtectHome=read-only` in the probe line, and the command inside the unit that must succeed.
- **Added by me:** step 3 explains an `auth status` that exits 1 (the variable is not set) and gives names-only checks, with the stray file; `oauth_token` is no proof the token works. Step 4b is marked **on hold**, says never to sign in if asked, to use a never-used home, and **first proves the token with one tiny model call:** with a broken token everything is refused, and the check would "pass" for the wrong reason.

## One more fact for `D26-cloud-result-review.md`
The journal shows **two** `--cloud` runs, both reusing `cloud-check-home`: **17:36:38, ran 31 s,** and **17:45:21, ran 3 s,** both ending with success. The second finished a few seconds before I pushed `D26-setup-check.md`, which therefore names only the first. One reading, **not shown:** a sign-in during the 31 s stored a full login in that folder, which the second run used. **If so, that login is still in the job user's home, which a job can read:** the clean-up line removes the folder, and the session should also be signed out in the Claude account.
**At 17:47 the dispatch timer was still enabled and active.** The queue was empty at 17:45.
