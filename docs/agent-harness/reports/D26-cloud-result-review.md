# D26, step 4b: the `setup-token` CAN start a cloud session. The check failed

**Ubay ran the check on 2026-11-27,** as `harness-job`, with only the token from `/etc/harness-job/claude.env`
and an empty `HOME`:
```
Created cloud session: Ready
View: https://claude.ai/code/session_...   (id left out here)
Resume with: claude --teleport session_...
Finished with result: success
```
So the documentation's sentence ("It can only make model requests") does not hold for creating a cloud
session, on CLI 2.1.332. **Option A does not close the cloud route.** This is what the check was for.

## State
- I asked Ubay to stop and delete that session. The dispatch timer is not to be started, and I queue no job.
- His "A" covered the `setup-token` **with** this check passing. It does not cover going live with the route
  open, and it does not imply B. The credential is his choice again; I have put the options to him.
- The `ProtectHome=read-only` fix (`D26-setup-review2.md`) is unaffected: build it.

## For you, read-only, no call that starts a session
1. From the CLI's help, its documentation and the hosts it names: does creating a cloud session use a
   different host from model requests? If it does, a job unit that can reach only the model host and GitHub
   (no direct network; a root-owned allow-listing proxy on localhost) would close the route whatever the
   credential, and would also narrow "a job can send out what it can read". Say what you find and how sure you
   are. Propose nothing to install yet.
2. Whether a cloud session started from a clone of `agent-harness` could reach `product-design`, as far as the
   documentation says (which repositories a session gets; whether it can push to a branch that is not its
   own).
Report in `D26-cloud-route.md`.
