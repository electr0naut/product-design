# D26: the cloud route (D26-cloud-result-review, "for you"). Read-only; no call that starts a session.

## 1. Does creating a cloud session use another host than model requests? **No, as far as I can tell**
**From the CLI's program file (2.1.332):** its configured base is `BASE_API_URL:"https://api.anthropic.com"` (one occurrence), and the session paths are joined to **that** base: `...BASE_API_URL}/v1/code/sessions` (and `/v1/code/sessions/...`), `...BASE_API_URL}/v1/environment_providers/cloud/create`. I found no session-creation path on a `claude.ai` host name (the only `https://claude.ai/api/...` strings are desktop-app downloads).
**From the docs** (read by a fetch agent, not re-read by me): `network-config` gives `api.anthropic.com` as "Claude API requests...", the model host. For `--cloud` the pages say only that it "creates a new cloud session on claude.ai" and **name no API host.** I read that as the product's name, not the host.

**So an allow list by host name cannot close the route:** a job must reach `api.anthropic.com` for the model.
**How sure:** high that this program joins session paths to the model host. **Not shown** by watching traffic that `--cloud` takes exactly these paths: I made no call.

**What it would take instead** (for your judgement; **not a proposal to install anything**): separating by **path**, which means whatever sits between the job and the host must see inside the connection. The shape that avoids breaking TLS: the job has **no direct network** to the host; model requests go in plain HTTP to a root-owned gateway on this machine, which forwards only the model paths. If that gateway also **held the credential**, the job would have no token to use elsewhere, or to leak into a report. **I do not know** whether this CLI works that way with a `setup-token` (the docs say a gateway set through `ANTHROPIC_BASE_URL` exists, and do not describe subscription tokens through it), or whether the account's terms allow it. It is a real piece of software to write and review.

## 2. From a clone of `agent-harness`, could a session reach `product-design`? **The docs do not rule it out**
From `claude-code-on-the-web`, `cloud-environments` and `web-quickstart` (fetch agent; `cloud-environments` only partly read verbatim):
- `--cloud` "clones your current directory's GitHub remote at your current branch", and "works with a single repository at a time".
- What it **can** be given depends on how the account connected GitHub: with the **GitHub App**, "private repositories that the Claude GitHub App is installed on"; with **`/web-setup`**, "**Any repository your `gh` token can access**".
- GitHub **API** requests are served only "for the repositories attached to the session"; others get a 403 (source archives too).
- **Pushes:** "the proxy rejects branch deletions and pushes of anything other than a branch... **It doesn't limit which branches a push can update.** To do that, use branch protection rules or rulesets on GitHub." So in an attached repository a session can push **any** branch the connection can write, `master` and the review branch included, unless GitHub's own rules stop it. `agent-harness` has none (the plan does not allow them).
- **The pages do not say** whether plain `git clone` or `git push` to a repository that is **not** attached is refused, or whether a session started from the terminal can add repositories (the browser flow can have several).

**One fact from this project:** your own sessions are cloud sessions of Ubay's account that push to `product-design`. So that account's GitHub connection **does** reach it. **For Ubay:** which way is GitHub connected (App, with which repositories installed, or `/web-setup`)? With `/web-setup`, a session of his account could be given anything his `gh` token reaches.

**So I would not count on "a session started from `agent-harness` cannot reach `product-design`".** Treat a job that can create a session as a job that may be able to write the review branch.
