# D26, step 4b, the real run: the `setup-token` is refused a cloud session. Option A holds

**Ubay, 2026-11-27, as `harness-job`, token saved with the silent prompt, a home that had never been used
(`/home/harness-job/check-home`), CLI 2.1.332:**

1. `claude --cloud "Reply with the single word ready. Change nothing."`:
   ```
   Error: Unable to get organization UUID
   Finished with result: exit-code      (status 1)
   ```
   No session id and no link. This is the error the documentation lists under "`claude --cloud` and
   `claude --teleport` require sign-in with a claude.ai account".
2. The model call with the same file and the same home, a minute later:
   `claude -p --model sonnet --tools "" -- "Reply with the single word ready."` printed `ready`, status 0.

Together: the token works for model requests and is not accepted for a cloud session. A stored claude.ai login
in that home would have created a session, as it did in the reused folder earlier, so the token was the only
credential in play. (He ran the cloud check before the model call, not after; the conclusion is the same.)

**So the credential stays the `setup-token` (his "A").** The three options I put to him after the false
result are withdrawn; I have told him.

What this does not show: other CLI versions. The job's CLI is a root-owned copy that does not update itself,
so the check holds until that copy is replaced. **Add to `D26-setup.md` step 2:** after replacing
`/usr/local/bin/claude` with another version, repeat 4b before any job runs.

## Left for Ubay (I give him the lines in chat)
Clean-up of the check folders; deploy `6ff69fa`; the unit install line and `daemon-reload`; then the timer.
The first job reports from inside the real unit that it cannot write its home, so I am not asking him to
repeat the whole step 9 probe: seven of its eight results were right the first time, and the eighth is shown
by his run with `ProtectHome=read-only`.
