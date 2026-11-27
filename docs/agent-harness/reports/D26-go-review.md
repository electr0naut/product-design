# D26: Ubay chose option A (instruction)

**Ubay Gonzalez, 2026-11-27, in the reviewing session.** Given the two options of `D26-proposal.md` in a table
(A: jobs run as a separate user with no `sudo` and no Docker, a proof runner for tests, signed decisions built
together with it; B: jobs run as his own user), with my recommendation of A, signed decisions now, and a time
cap plus a budget cap in place of a turn cap, he answered: **"A"**.

I read that as covering the three points as recommended. If he meant only A or B, he will say so; nothing here
is irreversible before his own commands.

## What you build, on a branch from `5b6c863`, in a clone and containers only
1. **The launcher, the proof runner and the units,** as files in the kit: the fixed launcher script, the
   system timer and service for `harness-job`, the proof runner with its own timer for `ubay`, the settings
   file and the fixed prompt, as in your proposal.
2. **Signed decisions.** The runner applies a decision only when the commit that adds or changes the file is
   signed by a key in a host-only list. An unsigned or wrongly signed decision is rejected with a comment, never
   applied and never retried. Say in the report how the reviewing session signs: I work in a cloud container
   and push through GitHub, so say what kind of key it needs and where its public half goes. Until Ubay has
   installed a key for me, the present behaviour must stay available behind one host-only setting that he
   flips, so that the switch is his act and not a side effect of a deploy.
3. **The ledger and the PR comments** for job start and end, written where a job cannot write.
4. **Tests,** in the proof container: the launcher takes the oldest job without a ledger entry and records it
   before running; a job is never run twice; a signed decision is applied and an unsigned one rejected; the
   proof runner takes a commit sha and nothing else.

## What you prepare for Ubay, and do not run
`RULES.md` section 3: `sudo`, a new user, credentials and system units are his. Write **`D26-setup.md`**: the
exact commands in order, each with one line saying what it does and how to undo it:
- create the user `harness-job` without `sudo` and outside the `docker` group;
- install the units and the root-owned launcher;
- create a GitHub credential for it, limited to the two repositories, contents write, no admin: say which kind
  and which settings, without any value;
- log that user in to Claude;
- the branch protection for `master` of `agent-harness`;
- install the reviewing session's public key and switch signed decisions on.
Then the checks he can run to see that the user cannot read `/home/ubay`, cannot use Docker and cannot `sudo`.

**No secret's value is written anywhere,** in the repository, a report, a log or a comment. Names only.

## Not verified, so verify before you rely on it
The flags of the proposed command (`--setting-sources ""`, `--strict-mcp-config`, `--max-budget-usd` with this
login), and whether the unit's protections work on this Ubuntu. Test what can be tested without `sudo`, and
list the rest as checks for Ubay in `D26-setup.md`.

Report as `D26-jobs.md`. The standing session stays until two jobs have run to the end under the new user.
