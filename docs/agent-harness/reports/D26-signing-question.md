# D26, early question before I build signing: whose key is it?

Read-only findings, from the runner's host-only mirror of the branch (last 400 commits) and GitHub:
- **Your commits are already SSH-signed.** All **192** commits authored `Claude`, on days from 11-18 to 11-27, carry **one** `ssh-ed25519` signature key, fingerprint `SHA256:32dP45eSMmVSt/G/CGvcxl/P+MO3Nwj9xeTh/GSA2wc`. The other authors' commits do not use it.
- **All 12 decision files** were last changed by a signed commit authored `Claude`. (I read the keys out of the signatures; I have not verified them against an allowed-signers list.)
- GitHub shows `7434288` and `d6f2c3d` as **verified**, author and committer **`claude`**.

**My inference, not confirmed:** this is the signing key of Claude's cloud environment, registered to the GitHub `claude` account, and **not a key that only your session holds.** If so:
- A signature with it would show "committed from a Claude cloud session", perhaps **any user's**, not "the reviewer decided this". Others would still need push access to the repository.
- A job that has a Claude login might be able to start a cloud session of its own that commits with it. A deny list in the job's settings is not a boundary against code the job runs. I have not tested whether it can.

That would leave signed decisions as protection against a job's **local** commits only (it would not have the private key), not against that second route.

**Please tell me, from your side:**
1. Who holds this key, and what can sign with it: only your session, all sessions of Ubay's account, or the whole platform? If you cannot establish it, say so.
2. Can your session hold a key of its own that outlives the container, and that other cloud sessions on the same account **cannot** read? I doubt a repository file or an environment variable would meet that.

**Options if the answers are no:**
- **(i)** Accept the platform key and say plainly what it does not cover. Cheap, and it stops a job's local commits.
- **(ii)** The runner also requires that an action which approves or releases work (`approve_test_edit`, `unblock_once`, `release`, `retire_hidden`, `reset_attempt`) be signed by **a key Ubay holds**. Real separation, but each such decision then needs Ubay.
- **(iii)** Give jobs **no push to the review branch:** they push to their own branch, and a fixed host step copies only their report files across. A job then cannot add a decision or a job file at all, whatever key exists. This does not depend on signatures.

**I would build (iii) together with (i):** (iii) closes the self-approval route by what the job's credential and the host step allow. It needs the job's GitHub credential to be unable to push the review branch, which a branch rule can enforce for a separate GitHub identity, but not for a token of Ubay's own account that may bypass it. I need to check which kind of credential allows that before `D26-setup.md`.

I will build the launcher, proof runner and units meanwhile; they do not depend on this.

**Also in my own proposal, a flaw:** it had the launcher run as `harness-job` and keep a ledger "where the job cannot write". Both cannot be true: the same user can write what its launcher writes. The ledger has to be written by something that is not the job's user (a root-owned dispatcher around the job's unit). I will build it that way.
