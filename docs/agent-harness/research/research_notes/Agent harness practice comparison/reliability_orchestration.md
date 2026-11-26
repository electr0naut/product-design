# Reliability and orchestration in agent harnesses: model failures, fallback, workflow state, stall alerting

Research date: 2026-11-26. Sources cover OpenHands (SDK and v0 controller), SWE-agent, GitHub Copilot coding agent, OpenAI Codex, Anthropic Claude Code (CLI, hooks, background sessions), two Anthropic engineering posts, LangGraph, and LiteLLM/OpenRouter. Access caveat: docs.litellm.ai, openrouter.ai, docs.github.com and docs.openhands.dev were blocked from this research session. For those, the notes rely on GitHub issues, search-engine excerpts of the official pages, or secondary write-ups, and each such case is flagged.

## Q1. How do systems detect an agent or model stuck in a loop or repeating output, and what happens next (abort, retry, switch model)?

### Takeaway
OpenHands is the only system surveyed that ships an explicit, rule-based loop detector. It compares recent events while ignoring IDs and timestamps, and its default action is to halt the run with a "stuck in loop" error. It does not retry or switch models. The other systems bound loops indirectly with step, turn, cost, or wall-clock limits. When a limit is hit, they either terminate the run or auto-submit partial work (SWE-agent).

### Cited Findings
**OpenHands (software-agent-sdk `stuck_detector.py`)**
- Four hard-coded patterns, as of Oct 2025:
  1. 4 identical action-observation pairs.
  2. 3 identical actions that each produce an error.
  3. 3 consecutive agent messages with no tool use ("monologue").
  4. 6 events of alternating ping-pong between two actions/observations.
  — [GitHub issue #762, OpenHands/software-agent-sdk, opened 2025-10-16](https://github.com/OpenHands/software-agent-sdk/issues/762)
- On detection the agent is stopped with a "stuck in loop" error. Issue #762 reports false positives on legitimate polling, for example checking a training job every 5 minutes, and notes that before the fix "the only alternative is disabling detection entirely." — [issue #762](https://github.com/OpenHands/software-agent-sdk/issues/762)
- Resolution: PR #763 (closed as completed 2025-12-18) made the thresholds configurable. It added a `stuck_detection_thresholds` dict on `LocalConversation` with keys `action_observation`, `action_error`, `monologue`, and `alternating_pattern`. Defaults stay at 4/3/3/6 and detection stays on by default. — [issue #762](https://github.com/OpenHands/software-agent-sdk/issues/762)
- The official SDK guide (seen only as a search excerpt; the host was blocked) says the detector is on by default, monitors the conversation in real time, and halts execution on repeated patterns. Its example flags a run after 4 identical action-observation pairs. It ignores superficial differences such as timestamps and event IDs. Status is exposed as `conversation.stuck_detector.is_stuck()`. — [OpenHands SDK: Agent stuck detector](https://docs.openhands.dev/sdk/guides/agent-stuck-detector)
- The legacy v0 controller exposes `StuckDetector.is_stuck(headless_mode=True)`. In interactive (non-headless) mode, a new user message resets the history window used for the check. In headless mode the whole history counts. — [OpenHands v0 API docs](https://docs.all-hands.dev/modules/python/openhands/controller/stuck) (search excerpt); test behavior per [Qodo test index of OpenHands](https://tests.qodo.ai/repos/all-hands-ai/openhands/test/8631) (secondary)

**SWE-agent (Princeton/Stanford)**
- No semantic loop detector was found. Runaway behavior is bounded by `per_instance_cost_limit`, which defaults to 3.0 USD per task instance. — [SWE-agent docs: Model config](https://swe-agent.com/latest/reference/model_config/)
- When the budget runs out, the episode ends with `exit_cost` and "the episode's changes are automatically submitted" (autosubmit), rather than being discarded. — [SWE-agent paper, NeurIPS 2024](https://papers.nips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf)
- Budget-capped runs perform much worse. For GPT-4 Turbo on full SWE-bench, 14.3% of runs ending in a deliberate `submit` were resolved, against 3.1% of those ending in `exit_cost`. — [SWE-agent paper](https://papers.nips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf)
- In the retry loop in `agents.py`, a retry attempt's cost limit is lowered to the remaining overall budget, so retries cannot exceed the instance budget. — [SWE-agent `sweagent/agent/agents.py`](https://github.com/SWE-agent/SWE-agent/blob/main/sweagent/agent/agents.py) (seen as search excerpt only)

**Claude Code**
- `--max-turns` limits agentic turns in print (headless) mode. There is no limit by default. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- `--max-budget-usd` stops a headless run once estimated spend reaches the cap. Subagent spend counts toward it. At the cap, spawning another subagent fails with `Budget limit reached`, and running background subagents are stopped. Spend can overshoot the cap, so the docs advise leaving headroom. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- Caveat from the Agent SDK docs: "Hooks may not fire when the agent hits the max_turns limit because the session ends before hooks can execute." — [Claude Code Agent SDK: hooks](https://code.claude.com/docs/en/agent-sdk/hooks) (search excerpt)
- Stop/SubagentStop hooks can block a stop and feed a reason back as Claude's next instruction, unless the hook response sets `impossible: true`. This is a deterministic hook point for custom "are you actually done / are you looping" checks. — [Claude Code hooks reference](https://code.claude.com/docs/en/hooks) (search excerpt)

**Anthropic engineering guidance**
- "Agents are stateful and errors compound." The research system tells the agent when a tool is failing and lets it adapt ("works surprisingly well"). It pairs this with "deterministic safeguards like retry logic and regular checkpoints." — [Anthropic, "How we built our multi-agent research system", 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system)
- In long-running coding harnesses, the observed failure modes are behavioral rather than mechanical loops:
  - "one-shotting": attempting too much and running out of context mid-feature.
  - Premature "declares victory".
  - Marking features done without end-to-end tests.

  The post does not cover timeouts or hung sessions. — [Anthropic, "Effective harnesses for long-running agents", 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### Inferences
- OpenHands' issue #762 shows the core design tension: exact-repeat detection catches true loops but also fires on legitimate polling. Thresholds need to be per-stage configurable. A "Qwen loops on one file" detector should key on (action, target file, error) tuples rather than raw output.
- None of the surveyed agent frameworks responds to detected looping by switching models. Their responses are halt (OpenHands), or auto-submit plus stop (SWE-agent at budget). Model switching in these systems is triggered by provider errors (Q2), not by behavioral loops. If the harness wants "loop, then switch model," that is a custom policy layered on top. No surveyed primary source documents it.
- The SWE-agent data (3.1% vs 14.3%) suggests that partial work produced under a forced stop is low quality. A harness should mark such output as failed or needing review rather than passing it to the next gate.

### Gaps
- No official GitHub or OpenAI source was found describing loop or repetition detection in the Copilot coding agent or Codex cloud.
- OpenRouter's own "doom loop detection" page for its Agent SDK appeared in search results (https://openrouter.ai/docs/agent-sdk/call-model/doom-loop-detection.md), but the host was blocked, so its contents are unverified.
- The current exact code of OpenHands `stuck.py` (v0) could not be fetched. The raw GitHub paths returned 404, presumably after the repo restructure. Hugging Face mirrors exist but are unofficial and were not used.

## Q2. Do they retry on another model automatically? With what limits?

### Takeaway
Automatic model fallback lives in the client CLI or routing layer, not in the agent loop. It is triggered by provider-side failures (overload, unavailability, rate limit, context window, content policy). Claude Code takes an ordered `--fallback-model` chain for overload or unavailability. LiteLLM retries within a model group, then walks an ordered fallback list, and cools down failing deployments. OpenRouter accepts a `models` array and fails over across providers. Fallback on "the model is looping or slow" is not a documented trigger in any of them.

### Cited Findings
**Claude Code `--fallback-model`**
- The flag enables "automatic fallback to the specified model(s) when the primary model is overloaded or not available, for example a retired model." It "Accepts a comma-separated list tried in order", for example `claude --fallback-model sonnet,haiku`. The flag can be persisted via the `fallbackModel` setting, which the flag overrides. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- Claude Code Remote session metadata distinguishes a session's configured model from the model that actually served the latest turn. It emits `model_fallback` / `model_refusal_fallback` events naming the original and fallback models. — tool schema of the Claude Code Remote environment used for this research (observed 2026-11-26; not a public doc page)

**LiteLLM router/proxy** (official docs host blocked; claims from secondary guides and search excerpts of docs.litellm.ai)
- Order of operations: retries (`num_retries`) are exhausted within the same model group first, then the router moves to the next model in the `fallbacks` list, in order. — [LiteLLM Router docs](https://docs.litellm.ai/docs/routing) (search excerpt); [continuumcode.ai failover guide](https://continuumcode.ai/guides/llm-failover/) (secondary)
- Cooldown: a deployment is cooled down after more than `allowed_fails` failures in a window, for `cooldown_time` seconds. The config example uses `allowed_fails: 3` and `cooldown_time: 30`. — [LiteLLM Router docs](https://docs.litellm.ai/docs/routing) (search excerpt)
- Conflicting defaults: the docs excerpt lists a 5 s default cooldown, while one guide describes a "3 failures per minute" default. One commentator says the docs are unclear whether the failure window is 1 minute or 30 s. — [fast.io LiteLLM rate-limit guide](https://fast.io/resources/litellm-rate-limit/) (secondary); treat the specific defaults as unverified.
- From prior knowledge of the LiteLLM docs (not re-verified here because the host was blocked), separate lists exist for `context_window_fallbacks` and `content_policy_fallbacks`, alongside generic `fallbacks`.
- Example: free OpenRouter models are chained as mutual fallbacks, and LiteLLM "will route around the rate-limited model automatically." — [rtfm.co.ua LiteLLM + OpenRouter fallbacks](https://rtfm.co.ua/en/litellm-openrouter-integration-and-fallbacks-configuration/) (secondary)

**OpenRouter** (host blocked)
- Only secondary claims were found: provider failover is on by default, and a provider in outage is deprioritized for about 30 s. — [CODERCOPS routing overview](https://blog.codercops.com/blog/llm-routing-openrouter-litellm-2026) (low-quality secondary; verify against https://openrouter.ai/docs/features/model-routing)

**SWE-agent**
- Retries are bounded by the remaining instance cost budget: each retry's limit is reduced to whatever budget remains. — [SWE-agent `agents.py`](https://github.com/SWE-agent/SWE-agent/blob/main/sweagent/agent/agents.py) (search excerpt)

**Copilot coding agent**
- The documented recovery for a stuck session is manual: the session times out after an hour, and the user retries by unassigning and reassigning the issue to Copilot. No automatic model switch was found. — [GitHub Docs: Troubleshooting Copilot coding agent](https://docs.github.com/pt/enterprise-cloud@latest/copilot/how-tos/agents/copilot-coding-agent/troubleshooting-copilot-coding-agent) (search excerpt; host blocked)

### Inferences
- Across the field, the pattern is two layers:
  1. Transport-level failover (HTTP 429/5xx/overload/unavailable, context overflow) handled by a router with bounded retries, an ordered fallback list, and per-deployment cooldown.
  2. Behavioral failure (loops, timeouts on a specific task) handled by halting and escalating.
- The harness's "Qwen looped or timed out 3x, switched by hand" case sits in layer 2. No surveyed primary source automates it. A reasonable extension of the documented patterns is a per-card attempt counter: after N stuck or timeout outcomes on the same card, re-dispatch to the next profile in an ordered chain, with a cap and a human alert. This is an inference, not documented practice.
- Claude Code's separation of configured vs served model, and its fallback events, is a useful pattern. The board should record which model actually produced each stage output, for traceability.

### Gaps
- The LiteLLM official reliability page (`/docs/proxy/reliability`) and OpenRouter official docs could not be fetched. Exact defaults and the error classes that trigger fallback are unverified.
- No primary source on whether Codex cloud or the Copilot coding agent fall back across models automatically.
- Temporal's activity retry policies (maximum attempts, backoff, non-retryable errors) were not covered in this session's searches.

## Q3. What component owns workflow state, and how are human decisions or review results delivered back to it (events, webhooks, polling, interrupts)?

### Takeaway
Mature systems make one durable component the owner of state:
- An append-only event stream or conversation (OpenHands).
- A checkpointer keyed by thread (LangGraph).
- A CI job bound to the PR (Copilot).
- Files plus git in the repo (Anthropic's long-running harness).

Human input reaches that owner as an explicit resume event: LangGraph `Command(resume=...)`, `@copilot` PR comments that trigger a new run, or Claude Code hooks and stream-json input. None of them depend on a chat session independently noticing a file.

### Cited Findings
**LangGraph**
- A node calls `interrupt()` to pause, and a checkpointer is required to persist state across the pause. Without one, resuming raises a RuntimeError. — [LangChain docs: Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop) (search excerpt)
- Resume works by re-invoking the graph on the same `thread_id` with `Command(resume=value)`. The value becomes the return value of `interrupt()`. Code before the `interrupt()` in that node re-runs on resume, so side effects must be idempotent. — [LangChain docs: Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop) (search excerpt); idempotency caveat also in [secondary tutorial](https://www.jahanzaib.ai/blog/langgraph-human-in-the-loop)
- Production guidance is a persistent checkpointer (Postgres, SQLite, or Redis) rather than in-memory. — [secondary tutorial](https://docs.bswen.com/blog/2026-04-16-langgraph-human-in-the-loop/)

**GitHub Copilot coding agent**
- The agent's session runs inside a GitHub Actions job. Session length is governed by `timeout-minutes` in `.github/workflows/copilot-setup-steps.yml`, because setup steps and agent work run in one job. One project raised it from 30 to 59 minutes after seeing sessions die at 30. — [epam/ketcher PR #12866](https://github.com/epam/ketcher/pull/12866) (third-party repo; not a GitHub guarantee)
- The coding agent is triggered and re-triggered through GitHub objects: issue assignment, and retry by unassign/reassign. — [GitHub Docs troubleshooting](https://docs.github.com/pt/enterprise-cloud@latest/copilot/how-tos/agents/copilot-coding-agent/troubleshooting-copilot-coding-agent) (search excerpt)
- From prior knowledge of GitHub docs (not re-fetched; host blocked): progress is reported via a draft PR, commits, and session logs, and reviewer feedback is delivered via PR comments mentioning `@copilot`, which start a new agent run.

**Claude Code**
- Headless mode supports structured bidirectional I/O: `--input-format stream-json`, `--output-format stream-json`, `--replay-user-messages`. With `--max-turns`, "a message still queued when the limit ends a turn stays queued and starts a new turn." — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- Background sessions (`--bg`) run under a supervisor daemon and are managed with `claude attach`, `claude logs`, `claude respawn`, `claude stop`, and `claude daemon status`. `claude respawn` restarts a running or stopped session "with its conversation intact." `--bg` can't be combined with `-p`. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- Hooks give deterministic, harness-executed callbacks:
  - Stop/SubagentStop can block completion and inject the next instruction.
  - Notification fires on `permission_prompt` / `idle_prompt`.
  - A timed-out Stop hook callback is treated as "no decision" and the agent stops normally.

  — [Claude Code hooks reference](https://code.claude.com/docs/en/hooks); [Agent SDK hooks](https://code.claude.com/docs/en/agent-sdk/hooks) (search excerpts)

**OpenHands**
- The SDK's `Conversation` object owns state. Stuck detection runs over its event history, and the stuck status is queryable from it (`conversation.stuck_detector.is_stuck()`). Thresholds are passed when constructing `LocalConversation`, and `RemoteConversation` support was proposed. — [issue #762](https://github.com/OpenHands/software-agent-sdk/issues/762); [OpenHands SDK guide](https://docs.openhands.dev/sdk/guides/agent-stuck-detector) (search excerpt)

**Anthropic multi-agent research system**
- Orchestrator-worker design. The lead agent plans, spawns subagents, and saves its plan to memory so it survives context truncation. Subagents run synchronously, which "simplifies coordination" but means "the entire system can be blocked while waiting for a single subagent." Asynchrony adds "challenges in result coordination, state consistency, and error propagation." — [Anthropic, 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system)
- Because agents run for long periods, a restart can't just discard work. The team "built systems that can resume from where the agent was when the errors occurred," and uses rainbow deployments so code updates don't break in-flight agents. — [Anthropic, 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system)

**Anthropic long-running harness**
- State lives in the repo, not in the chat:
  - `claude-progress.txt`.
  - A JSON feature list whose only mutable field is `passes`. JSON was chosen because the model is less likely to inappropriately edit it than Markdown.
  - Descriptive git commits as checkpoints.
  - An `init.sh` script.

  Each new session re-orients by reading git log and the progress file, and runs an end-to-end smoke test before new work. — [Anthropic, "Effective harnesses for long-running agents", 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### Inferences
- The harness's failure, where reviewer decisions written as markdown on a PR were missed for hours by a chat session's background watcher, is the anti-pattern these systems avoid. Each surveyed system has a single state owner that consumes decisions as typed events: interrupt/resume, comment-triggered runs, or hook callbacks.
- The closest fit for the harness: let the deterministic runner (systemd timer) be the sole state owner. Have it poll or receive the PR review result (GitHub review state or labels rather than free-form markdown) and write the decision onto the card. Agent sessions then only consume cards. This mirrors LangGraph (checkpointer plus explicit resume) and Copilot (the PR event triggers the run).
- Anthropic's choice of JSON for status fields, because models edit it less inappropriately than Markdown, supports encoding reviewer decisions as structured fields rather than prose files.

### Gaps
- Temporal's documentation on signals, updates, and durable AI-agent workflows was not retrieved this session. Its human-in-the-loop mechanism (signals/updates delivered to a workflow) is known from general knowledge but is uncited here.
- Official GitHub docs on Copilot coding agent progress reporting and `@copilot` comment handling could not be fetched (docs.github.com blocked).
- OpenAI Codex cloud: official docs confirm separate approval policy and sandbox controls, with `on-request` asking before leaving the sandbox ([Codex sandboxing](https://developers.openai.com/codex/concepts/sandboxing), search excerpt). No primary source was found on how cloud task state or review results are fed back, or on cloud task time limits. The only documented timeout found was a 60 s default per-tool timeout for MCP servers ([Codex config reference](https://developers.openai.com/codex/config-reference), search excerpt).

## Q4. How are stalls surfaced to humans (alerts, timeouts, dashboards)?

### Takeaway
Most products surface stalls passively, through hard wall-clock timeouts that turn a hang into a visible failure, plus session logs or status views. Active alerting is mostly left to the integrator through hooks (Claude Code Notification/Stop) or tracing. No surveyed system documents a "no progress for N minutes" alert of the kind the harness now has.

### Cited Findings
- **Copilot coding agent.**
  - Per the official troubleshooting page, a session that "remains stuck… will time out after an hour." — [GitHub Docs troubleshooting](https://docs.github.com/pt/enterprise-cloud@latest/copilot/how-tos/agents/copilot-coding-agent/troubleshooting-copilot-coding-agent) (search excerpt)
  - The effective limit is the Actions job `timeout-minutes` in `copilot-setup-steps.yml`. — [epam/ketcher PR #12866](https://github.com/epam/ketcher/pull/12866)
  - Community reports show sessions that run indefinitely and cannot be stopped or replied to. — [github/copilot-cli issue #2364](https://github.com/github/copilot-cli/issues/2364)
  - GitHub's own agentic workflows fail on hard job caps ("exceeded the maximum allowed execution time (10 minutes)") and auto-file issues titled "[aw] … Agent timed out". — [github/copilot-sdk issue #2620](https://github.com/github/copilot-sdk/issues/2620); [#2729](https://github.com/github/copilot-sdk/issues/2729)
- **Claude Code.**
  - The Notification hook fires on `idle_prompt` and `permission_prompt`, the "waiting on you" signal. Stop is the "work finished" signal. — [Claude Code hooks reference](https://code.claude.com/docs/en/hooks) (search excerpt)
  - Background sessions are inspectable via `claude logs <id>` and `claude daemon status`. The latter "Exits 1 if the supervisor isn't running", so it can serve as a scriptable health check. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
  - `claude respawn --all` restarts every running session. — [Claude Code CLI reference](https://code.claude.com/docs/en/cli-reference)
- **OpenHands.** A stuck conversation is halted and reported as an error state ("stuck in loop") rather than left hanging. — [issue #762](https://github.com/OpenHands/software-agent-sdk/issues/762)
- **Anthropic research system.**
  - "Adding full production tracing let us diagnose why agents failed and fix issues systematically."
  - The team monitors "agent decision patterns and interaction structures" without reading conversation contents.

  — [Anthropic, 2025-06-13](https://www.anthropic.com/engineering/multi-agent-research-system)
- **Anthropic long-running harness.** No timeout or stall handling is discussed. Recovery mechanisms target broken state between sessions, not a hung session. — [Anthropic, 2025-11-26](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)

### Inferences
- The industry baseline is "every unit of work has a hard wall-clock cap, and expiry becomes a visible failure on the work item": an Actions job timeout, an issue auto-filed on timeout. The harness's 45-minute stall alert and runner-failure alerts match or exceed what is documented by these vendors.
- GitHub auto-files an issue per timed-out agentic workflow run. For a card-based board, the analogous move is to make the failure land on the card itself (a blocked state with a reason), plus a push alert, so it can't be missed in a log.
- The Claude Code caveat that hooks may not fire when `max_turns` ends a session means stall alerting should not depend on the agent's own hooks. An external watchdog that checks progress timestamps, like the harness's systemd runner, is more robust.

### Gaps
- No primary source documents a configurable "no-progress" (heartbeat) alert in OpenHands, SWE-agent, Codex, or Copilot. All rely on timeouts, budgets, or halting on loops.
- Codex cloud task timeouts and stall notifications: no official figure was found.
- Temporal (heartbeat timeouts on activities, a direct analogue of stall detection) was not covered in this session's sources.
