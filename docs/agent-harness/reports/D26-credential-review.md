# D26, the job user's Claude credential: Ubay chose A

**Ubay, 2026-11-27, in answer to the three options of `D26-cloud-review.md` (A `setup-token` with one check he
runs at setup, B Console API key, C the subscription login as today): "A".**

So `D26-setup.md` is written for A:
- `harness-job` authenticates with a token from `claude setup-token` and nothing else. It is never logged in
  with `claude auth login`.
- **Ubay creates the token and puts it in place himself.** The setup notes give the commands and say where the
  value goes (readable by `harness-job` only; not in a repository, a unit file's text, a shell history or a
  log). Nobody else handles the value, and no report prints it, not even masked beyond its name.
- **The check he runs, once, as `harness-job` with only that token:** one `claude --cloud` command, which must
  be refused. Give him the exact command, what a refusal looks like, and what to do if it is not refused (end
  the cloud session it started, stop the setup there, tell the reviewer; the fallback is B, which is then his
  choice again and not implied by this "A").
- Also give the `claude auth status` check and what it must show.

B stays in the notes as the written fallback only. Nothing in this file changes anything live; the setup steps
wait for Ubay to run them.
