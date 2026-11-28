# D26 home fix (`d26-home-fix` @ `6ff69fa`): approved

**Approved. Fast-forward `master` to `6ff69fa581344afabd67d07a0dc72628a03bc6f0`.** Fresh worktree at that
commit: `762 passed, 3 skipped in 81.10s`; `ruff check` and `ruff format --check` clean. The difference from
`25a315e` is the one unit line `ProtectHome=read-only` with its comment, and one assertion in
`tests/test_d26.py`; with the line removed that test fails here (`1 failed, 73 passed`). Ubay's probe on the
machine already showed the line does what it should (`D26-setup-review2.md`).

## Deploy (Ubay; I give him the line in chat once `master` is there)
```
harness-deploy 6ff69fa581344afabd67d07a0dc72628a03bc6f0
```
Then he repeats the unit install line and `daemon-reload`, and all of step 9. The timer stays off until the
probe passes and the credential question is settled.

## The setup notes
- **Your token proof before the cloud check is right** (one tiny model call that must answer `ready`); I had
  left it out of what I gave Ubay and have added it.
- **Step 3 still tells him to use `sudoedit`.** That is how the token was lost. Replace it with the silent
  prompt I gave him, and keep the `grep -o` check right after it:
  `sudo bash -c 'read -rsp "Token: " T && printf "CLAUDE_CODE_OAUTH_TOKEN=%s\n" "$T" > /etc/harness-job/claude.env'; clear`
- The step 3 login check writes `.claude` files into the job's real home. Run it with a throwaway home instead
  (`-E HOME=` a new folder under the job's home), so nothing is left to clean.

## `D26-cloud-route.md`: accepted
- A host allow list cannot close the route: session creation is on the model host. Noted; no gateway is to be
  built. The idea that a root-owned gateway could **hold** the credential is worth keeping for later, because
  it would also keep the token out of a job's reach; not now.
- "Treat a job that can create a session as a job that may be able to write the review branch": agreed, and
  that is how I put it to Ubay.
- The real 4b has still not run (`D26-setup-review3.md`). Until it has, nothing is known about the token.
