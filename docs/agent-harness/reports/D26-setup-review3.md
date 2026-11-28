# D26 setup: what Ubay's four commands showed. Your reading in `D26-setup-check.md` was right

From Ubay's output, 2026-11-27 (names and states only):
- **`/etc/harness-job/claude.env` is 0 bytes** (`-r--r----- root harness-job`). The token was never saved. No
  other file is in that folder, so there is no stray copy.
- **`/home/harness-job/cloud-check-home/.claude/.credentials.json` exists (17:36).** `claude auth status` in that
  home reports `authMethod: claude.ai`, `storedClaudeAiLogin: true`, subscription `max`. So the first 4b run
  signed in through the browser, and the cloud session of the second run was made by **that stored login**.
- **Nothing is known yet about what a `setup-token` can do.** My "the token can start a cloud session" was
  wrong and is corrected in `D26-cloud-result-review.md`. Option A stands untested; the credential options I
  put to Ubay are withdrawn until the real check has run.
- The dispatch timer is disabled again (`Removed .../timers.target.wants/harness-job-dispatch.timer`).

## What I have asked Ubay to do
1. Log that stored login out and delete the two check homes and the probe files.
2. Save a new token without an editor (a silent prompt writing the one line), then check: the variable's name
   by `grep -o`, and `auth status` in a home that has never been used, which must say `oauth_token`.
3. Repeat 4b in that same unused home.

## For `D26-setup.md` (with the `ProtectHome` commit)
- **Step 3 writes the token with a silent prompt, not an editor,** and checks the file is not empty
  (`grep -o '^[A-Z_]*='` must print the name). The editor route lost the token without a sign.
- **Step 4b must not be able to pass or fail on another credential.** Before it: `auth status` in the very home
  4b will use must say `oauth_token`, and `.credentials.json` must not exist there; if the CLI offers a sign-in
  during 4b, the answer is to stop, not to sign in. Say that in bold where he reads it.
- The step 3 check line "must show `oauth_token`" stays, with your finding beside it: any value gives
  `oauth_token` and exit 0, so it shows the variable is set, not that the token is valid.
