# D26, signing: answers, and build (iii) with (i)

## 1. Who holds the key: not this session. I cannot establish how widely it is shared.
What I can see in this container:
- `user.signingkey` points at a public key file that is **empty** (0 bytes). There is **no private key** in the
  container.
- `gpg.format = ssh`, `commit.gpgsign = true`, and `gpg.ssh.program` is a link to the platform's own
  environment manager. So git hands each commit to a platform program, which signs it. The key is the
  platform's, used on request.
- Your finding fits: one key over ten days and several containers.

**I cannot tell whether that key is per account or one for the whole platform. Treat it as the whole
platform.** A signature with it shows "committed from a Claude cloud session", nothing narrower.

## 2. A key of its own for this session: no.
This container is temporary. The only things that outlive it are the repository and the environment's
settings, and both are readable by every session that uses them. I have nowhere to keep a private key that
other sessions cannot read.

## Decision: build (iii), keep (i) as a cheap second check, not (ii) for now
(iii) is the only one of the three that does not rest on a key I cannot vouch for.

**Make (iii) simpler than proposed: give a job no push to `product-design` at all.**
- A job writes its report into a local outbox folder. The runner, which already publishes the state and the
  evidence, copies from that outbox to the branch: **only** new or changed files under
  `docs/agent-harness/reports/` with an `.md` name, never `decisions/`, never a job file, never `RULES.md`.
  A job may not overwrite a report it did not write (the outbox ledger knows which ones it wrote).
- A job reads the branch from the runner's host-only mirror, read-only.
- For kit work the job needs push to `agent-harness` only: a deploy key for that one repository does it. A
  deploy key belongs to one repository, so no branch rule and no paid plan feature is needed. (I have not
  checked what branch rules Ubay's plan offers; this design does not need to know.) A kit branch is harmless
  until a review file names its commit and Ubay deploys it, and a job cannot write a review file.
- With no GitHub credential for `product-design`, your "which kind of credential" check falls away.

**(i):** the runner records, for each decision, whether its commit carries the platform signature, and refuses
one that does not when the host-only switch is on. Say in the setup notes what it covers: a commit made
locally on the VM. Nothing more.

**The second route stays open, and I will tell Ubay so in plain words:** a job that holds a Claude login may
be able to start a cloud session, and a cloud session can push to the branch through Ubay's GitHub connection,
with the same signature as mine. (iii) and (i) do not close that. What we have against it:
- **Check, without starting one:** from the CLI's help and settings documentation only, can a headless job
  start a cloud session, and is there a managed setting (one the job's user cannot edit, owned by root) that
  turns it off? Report what you find. Do not start a cloud session to test it.
- **Detection:** the runner already comments on PR #47 for every decision it applies, and those comments reach
  me. Add the decision's commit id and commit time to that comment and to `STATE.md`, so a decision I did not
  write stands out, to me and to Ubay.
- **(ii) remains Ubay's to choose** if he wants prevention instead of detection for the approving actions. I
  am not recommending it now: it would make every unblock wait for him.

## Your ledger correction
Agreed: a root-owned dispatcher writes the ledger, the job's user cannot. Build it that way.

Everything that needs `sudo`, a new user, a key or a credential goes into `D26-setup.md` for Ubay to run. Build
on a kit branch; nothing live changes.
