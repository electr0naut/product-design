# D26, the cloud-session check: accepted. The credential choice goes to Ubay

**Your finding holds.** I had the two pages fetched again and the quotes match yours word for word:
- `authentication`: the `setup-token` token "authenticates with your Claude subscription ... It can only make
  model requests, so it can't establish Remote Control sessions or fetch claude.ai connectors."
- `claude-code-on-the-web`: "`claude --cloud` and `claude --teleport` require sign-in with a claude.ai account",
  with the message "Cloud sessions aren't available with this Console sign-in. They need a claude.ai sign-in.
  Run `claude auth login` ...". Also: "you still need to sign in with `claude auth login`".

So: a Console API key is stated outright to be unable to start a cloud session. For the `setup-token` token it
is strongly implied (it only makes model requests; cloud sessions want a `claude auth login` sign-in) but not
stated.

## What I am putting to Ubay
- **A. `setup-token`, and one check he runs himself at setup** (my recommendation): usage stays on the
  subscription, no per-use bill. At setup, as `harness-job` with only that token, he runs one `claude --cloud`
  command, which must be refused. That turns the inference into a fact on his machine. If it is not refused, he
  ends that session and we go to B.
- **B. Console API key:** stated by the documentation; billed per use; `--max-budget-usd` then means dollars.
- **C. The subscription login, as today:** the route stays open and we rely on detection.

**Write `D26-setup.md` for A, with B as the written fallback,** and leave the credential step marked "waits for
Ubay's choice". Whichever it is: `harness-job` is never logged in with `claude auth login`, the setup gives a
`claude auth status` check, and the token or key goes where only `harness-job` can read it, never into a
repository, a unit file's text or a log.

## Your two tightenings: agreed
- A report's name starts with the job's id and may not contain "review". Good catch; keep it.
- A job no longer edits `HANDOFF.md` and writes a "For HANDOFF.md" section instead. Fine: say in `D26-jobs.md`
  who then applies that section (the runner, copying nothing but that section, or me).

## For `D26-jobs.md`, so I can review it in one pass
- The outbox copy step: the exact rule for what is copied, and tests for each thing it must refuse (a link, a
  path outside `reports/`, a name without the job's id, an existing report of another job, a file that is not
  `.md`, a file over a size cap).
- What a job can read: confirm the bundle holds the review branch only, and that the hidden acceptance tests
  and the host-only state are outside anything `harness-job` can read.
- What happens to a job that is still running when its time is up, and what the ledger then says.
