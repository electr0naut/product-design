# D26: can a job start a cloud session? (D26-signing-review, "check without starting one") and part 2

No cloud session was started and no model call was made for this.

**Sources.** The CLI's `--help` (2.1.332), read here. The documentation pages `cli-reference`, `claude-code-on-the-web`, `routines`, `ultrareview`, `authentication`, `permissions`, `settings`, `settings-reference` and `managed-settings` under `code.claude.com/docs/en/`, **read by a fetch agent; I have not re-read them.** Quotes below are the ones it reported verbatim.

## Answer: with a claude.ai login, **yes**
- `--help`: `--cloud [description|session_id|url]`, "Create a cloud session with the given description, or attach to an existing one"; also `ultrareview` ("Run a cloud-hosted multi-agent code review") and `--environment` (a new cloud session on a self-hosted environment).
- Without a person at the keyboard, the pages show: `claude ultrareview` "from CI or a script without an interactive session"; `claude -p ... --environment <id>`; and `claude -p "message" --cloud <session-id>`, which **posts into an existing cloud session**. They do **not** say whether `-p --cloud "<task>"` creates one. Treat it as possible.

## Can a root-owned setting turn it off? **I found no such setting**
- The agent read the whole settings index and found no key that disables cloud sessions or routines (`disableRemoteControl` is about Remote Control, which the docs call unrelated). It did not read the `env-vars` or server-managed-settings pages. `allow_remote_sessions` is an organisation admin policy for plans that have one.
- `--restricted` "refuses to create cloud sessions", but it is a flag on one invocation (and by default removes the tools that run commands). Code the job runs can start `claude` without it.
- Managed deny rules bind the tool calls, not programs: the permissions page says a Bash rule "isn't a security boundary around the program".

## What would close it: **the kind of credential the job user holds**
| login | cloud sessions, per the pages |
|---|---|
| claude.ai subscription | yes |
| **Console API key** | **"Cloud sessions aren't available with this Console sign-in. They need a claude.ai sign-in."** (`claude-code-on-the-web`) |
| `claude setup-token` | "It can only make model requests, so it can't establish Remote Control sessions or fetch claude.ai connectors." (`authentication`). **It does not say "cloud sessions";** that it cannot is an inference |

**Recommendation: give `harness-job` a Console API key as its only Claude credential.** It is the one case the documentation states outright, and it closes the route by what the key is, not by a rule the job's code can walk around. It also gives `--max-budget-usd` a meaning in dollars. **What it costs, for Ubay to weigh:** job usage is billed per use instead of coming out of the subscription, and it is a new secret. A `setup-token` would stay on the subscription but rests on the inference above. Either way the job user must **never** be logged in with `claude auth login`; `D26-setup.md` will say so and give a check (`claude auth status`). **This choice is Ubay's** (`RULES.md` section 3).

## Part 2 of D26 is built (branch `d26-jobs`, `20a72c5`; not for review until `D26-jobs.md`)
Per your signing answer: a job gets the branch as a git bundle and its clone has no remote; reports leave through an outbox that the runner reads only after the job has ended, following no link; each decision's commit, time and signature are recorded and shown in its comment (and in `STATE.md` for applied ones; refused ones stay out of "What changed", as before).
**Tighter than you asked, say if you object:** a report's name must start with the job's id, and may not contain "review". Otherwise a job could write `X-review.md`, which is what your instructions look like to whoever reads this branch.
**A consequence:** a job can no longer edit `HANDOFF.md`; it writes a "For HANDOFF.md" section in its report.
Fresh clone in the proof container: 735 passed, 3 skipped, no live path read or written.

## Left
Try the job command's flags with a real `claude -p` call; `D26-setup.md`; `D26-jobs.md`.
