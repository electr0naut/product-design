# Agent delivery harness: build spec

Audience: the Claude Code session that builds the harness inside a Docker Linux container, and the
engineer supervising it. The rationale for every decision is in `DESIGN.md`; this file says what to build,
in what order, and how to prove each step works.

Conventions:

- **Literal files.** A line `File: <path>` followed by a code block means: create that file with exactly
  that content. `tools/extract_literals.py` (section 0.2) writes all of them in one pass, so the builder
  does not spend tokens retyping them.
- **Contracts.** Everything else is a contract: implement it as described, in Python 3.12, standard
  library only (pytest and ruff for development).
- **Acceptance checks.** Every milestone ends with commands and expected results. A milestone is done only
  when they pass and the output has been shown.
- **"verify".** Wherever a step says "verify", run the check and record the result in `.harness/probe.json`
  instead of assuming it.

## 0. Getting started

### 0.1 Kickoff prompt (paste into Claude Code in the container)

```text
You are building the agent delivery harness specified in docs/BUILD_SPEC.md, with rationale in
docs/DESIGN.md. Work one milestone at a time, M0 through M6. For each milestone:
1. Read only that milestone's section and .harness-build/progress.md.
2. Create exactly the files it lists. Copy literal files with tools/extract_literals.py; do not retype them.
3. Run its acceptance checks and show the real output.
4. Update .harness-build/progress.md (at most 40 lines: done, decisions, next step) and stop for review.
Python 3.12 standard library only for the driver; pytest and ruff for development. Do not run live LLM
stages unless an acceptance check says so, and always with the budget cap it shows.
```

Builder settings:

- Run the builder as `claude --model sonnet`. Switch to Opus only for a design question you are stuck on.
- Use one session per milestone. `.harness-build/progress.md` carries state between sessions, which is the
  same progress-file pattern the harness itself uses.
- Once M1 exists, use the locator agent for lookups.

### 0.2 Bootstrap

1. Create a folder `agent-harness/` and a subfolder `docs/`. Save `DESIGN.md` and `BUILD_SPEC.md` in
   `docs/`.
2. Copy the extractor below to `tools/extract_literals.py` by hand. It is the only file you copy by hand.
3. Extract everything else:

```bash
docker run --rm -v "$PWD":/k -w /k python:3.12-slim python3 tools/extract_literals.py docs/BUILD_SPEC.md .
```

File: `tools/extract_literals.py`
```python
"""Extract every `File: <path>` literal block from a Markdown spec into a target directory."""

import re
import sys
from pathlib import Path

FILE_LINE = re.compile(r"^File: `?([^`\s]+)`?\s*$")
FENCE = re.compile(r"^(`{3,})[\w.+-]*\s*$")


def extract(spec: Path, root: Path) -> list[Path]:
    """Write each literal block of spec below root and return the written paths."""
    lines = spec.read_text(encoding="utf-8").splitlines()
    written: list[Path] = []
    i = 0
    while i < len(lines):
        match = FILE_LINE.match(lines[i])
        i += 1
        if match is None:
            continue
        while i < len(lines) and not lines[i].strip():
            i += 1
        fence = FENCE.match(lines[i]) if i < len(lines) else None
        if fence is None:
            raise SystemExit(f"No code fence after 'File: {match.group(1)}' (line {i + 1})")
        closing = fence.group(1)
        i += 1
        start = i
        while i < len(lines) and lines[i] != closing:
            i += 1
        if i == len(lines):
            raise SystemExit(f"Unclosed code fence for {match.group(1)}")
        target = root / match.group(1)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("\n".join(lines[start:i]) + "\n", encoding="utf-8")
        written.append(target)
        i += 1
    return written


def main() -> None:
    """Run as: extract_literals.py SPEC.md TARGET_DIR."""
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_literals.py SPEC.md TARGET_DIR")
    for path in extract(Path(sys.argv[1]), Path(sys.argv[2])):
        print(path)


if __name__ == "__main__":
    main()
```

### 0.3 Kit layout after all milestones

```text
agent-harness/
  Dockerfile                 container (section 1)
  pyproject.toml             ruff + pytest config
  harness.toml               config pointing at the eval fixture
  docs/                      DESIGN.md, BUILD_SPEC.md
  tools/extract_literals.py
  src/harness/               driver package (M2 to M6)
  schemas/                   JSON Schemas for stage outputs (M2)
  template/                  copied into a target repo by `harness install` (M1)
    AGENTS.md  CLAUDE.md  ci/gitlab-ci.yml
    .claude/settings.json  .claude/agents/*.md  .claude/hooks/*.py  .claude/skills/*/SKILL.md
  eval/fixture/              benchmark (M5): repo/, tickets/, hidden/, reference/, variants.toml
  tests/                     pytest suite, including the stub CLIs
```

## 1. Container

File: `Dockerfile`
```dockerfile
FROM node:22-bookworm-slim AS node

FROM python:3.12-slim-bookworm

ARG CLAUDE_CODE_VERSION=latest
ARG INSTALL_CODEX=false
ARG INSTALL_GEMINI=false

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ripgrep curl ca-certificates jq \
    && rm -rf /var/lib/apt/lists/*

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN if [ "$INSTALL_CODEX" = "true" ]; then npm install -g @openai/codex; fi \
    && if [ "$INSTALL_GEMINI" = "true" ]; then npm install -g @google/gemini-cli; fi

RUN pip install --no-cache-dir "pytest>=8" "ruff>=0.6"

RUN useradd --create-home --uid 1000 harness \
    && mkdir -p /work /ledger /harness \
    && chown harness:harness /work /ledger /harness
USER harness
RUN curl -fsSL https://claude.ai/install.sh | bash -s "$CLAUDE_CODE_VERSION" \
    && git config --global --add safe.directory '*' \
    && git config --global user.name "agent-harness" \
    && git config --global user.email "agent-harness@localhost"
ENV PATH="/home/harness/.local/bin:${PATH}" \
    PYTHONPATH="/harness/src"

WORKDIR /harness
CMD ["bash"]
```

Build the image (pin `CLAUDE_CODE_VERSION` to the version M0 records, once you have it):

```bash
docker build -t agent-harness:dev --build-arg INSTALL_CODEX=true .
```

Run it with the kit mounted. The named volumes keep the ledger and a `claude /login` session between
runs:

```bash
docker run --rm -it -e ANTHROPIC_API_KEY -v "$PWD":/harness -v harness-ledger:/ledger -v harness-claude:/home/harness/.claude agent-harness:dev
```

Credentials and options:

- **Bedrock.** Pass `-e CLAUDE_CODE_USE_BEDROCK=1` and your AWS variables instead of the API key.
- **Vertex.** Pass `-e CLAUDE_CODE_USE_VERTEX=1`, `-e CLOUD_ML_REGION` and the Google credentials.
- **Other lab.** The refuter's credentials go in via `-e OPENAI_API_KEY` or `-e GEMINI_API_KEY`.
- **Replay mode** (M5) needs a real repository: add `-v /path/to/repo:/work`.
- **Corporate proxy.** Pass `--build-arg HTTPS_PROXY=...` and add your CA certificate to the image. Most
  corporate networks need this.

File: `pyproject.toml`
```toml
[project]
name = "agent-harness"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]

[tool.ruff]
target-version = "py312"
line-length = 100
extend-exclude = ["eval/fixture"]

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP"]
```

## 2. M0: probe and baseline

Goal: learn what your CLI version actually does before building on it, and capture today's numbers.

Steps:

1. Check the CLI version:

```bash
claude --version
```

2. Run a schema probe:

```bash
mkdir -p .harness && echo 'Return ok=true.' | claude -p --model haiku --max-turns 2 --max-budget-usd 0.05 --output-format json --json-schema '{"type":"object","properties":{"ok":{"type":"boolean"}},"required":["ok"]}' > .harness/probe-schema.json
```

```bash
python3 -c "import json; d = json.load(open('.harness/probe-schema.json')); print(sorted(d)); print(d.get('structured_output'), d.get('total_cost_usd'))"
```

3. Run a budget probe, to learn what a run that hits the budget reports:

```bash
echo 'Count from 1 to 400, one number per line.' | claude -p --model haiku --max-budget-usd 0.0001 --output-format json > .harness/probe-budget.json; python3 -c "import json; d = json.load(open('.harness/probe-budget.json')); print(d.get('subtype'), d.get('is_error'))"
```

4. Record the results in `.harness/probe.json`:
   - `cli_version`
   - `result_keys`
   - `structured_output_key` (the key that holds schema output)
   - `budget_subtype`
   - `max_turns_subtype`: get it the same way, with `--max-turns 1` on a task that needs tools.
   - `json_schema_arg`: `"inline"` or `"path"`, whichever form worked.
5. Baseline from today's flow, if you have the data: for 5 recent tickets, record cost, wall time, review
   rounds, human review comments and post-merge defects in `.harness/baseline.json`. If you have no data,
   the `baseline` profile in M5 stands in for it.

Acceptance:

- The `claude --version` output is 2.1.186 or newer. That version is needed for `Agent(type)` deny rules.
  If yours is older, note it; the guard hook still covers the gap.
- The schema probe prints `structured_output` with `{"ok": true}`, and `total_cost_usd` is a number.
- `.harness/probe.json` exists with all six fields.

## 3. M1: the Claude Code layer (literal files)

These files go into every target repository through `python -m harness install <repo>` (M2). They are
written for `template/` and work on their own in interactive Claude Code sessions.

File: `template/.claude/settings.json`
```json
{
  "env": {
    "CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS": "1"
  },
  "permissions": {
    "deny": [
      "Agent(general-purpose)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Agent|Task",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/guard_agent.py\""
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup|resume|compact",
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/session_context.py\""
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 \"$CLAUDE_PROJECT_DIR/.claude/hooks/stop_gate.py\""
          }
        ]
      }
    ]
  }
}
```

### 3.1 Hooks

File: `template/.claude/hooks/guard_agent.py`
```python
"""PreToolUse hook for the Agent tool: allow pinned subagents only, reject model overrides."""

import json
import re
import sys
from pathlib import Path

AGENTS_DIR = Path(__file__).resolve().parent.parent / "agents"
MAIN_THREAD_ONLY = frozenset({"orchestrator"})
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def pinned_models(agents_dir: Path) -> dict[str, str]:
    """Return the pinned model of every spawnable agent, keyed by agent name."""
    pins: dict[str, str] = {}
    for path in sorted(agents_dir.glob("*.md")):
        match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
        if match is None:
            continue
        top_level = (
            line.partition(":")
            for line in match.group(1).splitlines()
            if not line.startswith((" ", "\t"))
        )
        fields = {key.strip(): value.strip() for key, _, value in top_level}
        name, model = fields.get("name", ""), fields.get("model", "")
        if name and model and name not in MAIN_THREAD_ONLY:
            pins[name] = model
    return pins


def denial_reason(tool_input: dict[str, object], pins: dict[str, str]) -> str | None:
    """Return why this Agent call must be denied, or None to allow it."""
    agent = str(tool_input.get("subagent_type") or "general-purpose")
    requested = tool_input.get("model")
    if agent not in pins:
        return (
            f"Subagent '{agent}' is not allowed. Use one of: {', '.join(sorted(pins))}. "
            "Lookups go to locator, test runs to test-runner, handoff notes to scribe."
        )
    if requested and requested != pins[agent]:
        return (
            f"Do not pass model='{requested}' to '{agent}'; it is pinned to '{pins[agent]}'. "
            "Repeat the same Agent call without the model argument."
        )
    return None


def main() -> None:
    """Read the PreToolUse payload from stdin and print a deny decision when needed."""
    payload = json.load(sys.stdin)
    reason = denial_reason(payload.get("tool_input", {}), pinned_models(AGENTS_DIR))
    if reason is not None:
        decision = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        json.dump({"hookSpecificOutput": decision}, sys.stdout)


if __name__ == "__main__":
    main()
```

File: `template/.claude/hooks/session_context.py`
```python
"""SessionStart hook: re-inject the routing rules and the active ticket's handoff."""

import json
import os
import sys
from pathlib import Path

ROUTING = (
    "Routing is enforced by hooks: lookups go to locator, test runs to test-runner, "
    "handoff notes to scribe, code changes to implementer, reviews to reviewer. "
    "Never pass a model argument to the Agent tool."
)
MAX_HANDOFF_LINES = 60


def build_context(project_dir: Path) -> str:
    """Return the routing rules followed by the head of the active ticket's handoff."""
    current = project_dir / ".harness" / "current_ticket"
    if not current.is_file():
        return ROUTING
    key = current.read_text(encoding="utf-8").strip()
    handoff = Path(".harness") / "tickets" / key / "handoff.md"
    parts = [ROUTING]
    if (project_dir / handoff).is_file():
        lines = (project_dir / handoff).read_text(encoding="utf-8").splitlines()
        parts.append(f"Active ticket {key}; handoff from {handoff}:")
        parts.extend(lines[:MAX_HANDOFF_LINES])
    else:
        parts.append(f"Active ticket {key}; no handoff yet. Ask scribe to create {handoff}.")
    return "\n".join(parts)


def main() -> None:
    """Read the SessionStart payload from stdin and print additional context."""
    payload = json.load(sys.stdin)
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    output = {"hookEventName": "SessionStart", "additionalContext": build_context(project_dir)}
    json.dump({"hookSpecificOutput": output}, sys.stdout)


if __name__ == "__main__":
    main()
```

File: `template/.claude/hooks/stop_gate.py`
```python
"""Stop hook: block once when code changed after the active ticket's handoff was written."""

import json
import os
import subprocess
import sys
from pathlib import Path


def changed_paths(project_dir: Path) -> list[Path]:
    """Return files with uncommitted changes, excluding harness state."""
    status = subprocess.run(
        ["git", "status", "--porcelain", "-z", "--untracked-files=all"],
        cwd=project_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    paths: list[Path] = []
    entries = iter(status.split("\0"))
    for entry in entries:
        if len(entry) < 4:
            continue
        code, rel = entry[:2], entry[3:]
        if code[0] in "RC":
            next(entries, None)
        path = project_dir / rel
        if not rel.startswith(".harness/") and path.is_file():
            paths.append(path)
    return paths


def block_reason(project_dir: Path) -> str | None:
    """Return why stopping should be blocked, or None to allow it."""
    current = project_dir / ".harness" / "current_ticket"
    if not current.is_file():
        return None
    key = current.read_text(encoding="utf-8").strip()
    handoff = project_dir / ".harness" / "tickets" / key / "handoff.md"
    changed = changed_paths(project_dir)
    if not changed:
        return None
    newest = max(path.stat().st_mtime for path in changed)
    if handoff.is_file() and handoff.stat().st_mtime >= newest:
        return None
    return (
        f"Files changed after the {key} handoff was last written. Ask scribe to update "
        f"{handoff.relative_to(project_dir)} (status, decisions, next step), then stop."
    )


def main() -> None:
    """Read the Stop payload from stdin and print a block decision when needed."""
    payload = json.load(sys.stdin)
    if payload.get("stop_hook_active") or os.environ.get("HARNESS_PIPELINE") == "1":
        return
    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or payload.get("cwd") or ".")
    reason = block_reason(project_dir)
    if reason is not None:
        json.dump({"decision": "block", "reason": reason}, sys.stdout)


if __name__ == "__main__":
    main()
```

### 3.2 Agents

Every worker agent pins its model in frontmatter. The guard hook reads these pins, so a model change is
made in one place. In pipeline mode the driver runs each stage agent as the main thread
(`claude -p --agent <name>`), which is where `Agent(x, y)` allowlists in `tools` take effect.

File: `template/.claude/agents/orchestrator.md`
````markdown
---
name: orchestrator
description: Main-thread coordinator for interactive ticket work. Start it with `claude --agent orchestrator`. Not for use as a subagent.
model: sonnet
tools: Agent(locator, test-runner, scribe, implementer, reviewer), Read
---
You coordinate one ticket at a time. You have no search, shell or edit tools; delegate instead.

- Find anything (files, symbols, call sites, config keys, tests, wiki pages): locator.
- Run tests, linters or type checks: test-runner.
- Change code or tests: implementer, with the plan step and the exact files.
- Review the current diff: reviewer.
- Record status, decisions and the next step: scribe.

Read only the files and line ranges that locator returns.
Never pass a `model` argument to the Agent tool. Every agent has a fixed model.
````

File: `template/.claude/agents/locator.md`
````markdown
---
name: locator
description: Finds files, symbols, call sites, config keys, tests and wiki pages. Use it for every lookup before reading code. Read-only. Returns locations, not opinions.
model: haiku
maxTurns: 12
omitClaudeMd: true
tools: Read, Grep, Glob, Bash
disallowedTools: Edit, Write
---
Answer lookups with locations.

Prefer exact tools: Grep for text and symbols, Glob for paths, `git log -S '<text>' --oneline` for history.
If `.harness/wiki_search` exists, also run `.harness/wiki_search "<query>"`.
Use Bash only for read-only commands.

Output one result per line:
path:line  why it matches

If you find nothing, output `NOT FOUND`, then every query you ran, one per line.
Never guess a location.
````

File: `template/.claude/agents/test-runner.md`
````markdown
---
name: test-runner
description: Runs tests, linters and type checks and summarises failures. Use it instead of running test commands yourself.
model: haiku
maxTurns: 8
tools: Read, Bash
disallowedTools: Edit, Write
---
Run the command you are given. If none is given, use the test command in AGENTS.md.

Report:
- first line: `PASS <n>` or `FAIL <n failed> / <n total>`
- for each failure: test id, file:line, and at most 5 lines of assertion output

Never paste full logs. Never edit files. Never retry a failing command more than once.
````

File: `template/.claude/agents/scribe.md`
````markdown
---
name: scribe
description: Writes and updates the ticket handoff file from structured input. Use after each stage and before stopping.
model: haiku
maxTurns: 6
omitClaudeMd: true
tools: Read, Write, Edit
skills: handoff
---
Follow the handoff skill exactly. Write only facts present in your input. Never invent status or decisions.
````

File: `template/.claude/agents/readiness.md`
````markdown
---
name: readiness
description: Decides whether a ticket is ready to implement. Pipeline stage; returns JSON.
model: haiku
maxTurns: 4
tools: Read, Agent(locator)
skills: ticket-readiness
---
Follow the ticket-readiness skill. Return only the JSON object the schema asks for.
````

File: `template/.claude/agents/planner.md`
````markdown
---
name: planner
description: Turns a ready ticket into a step plan with an acceptance-criterion-to-test map. Pipeline stage; returns JSON.
model: sonnet
maxTurns: 30
tools: Agent(locator), Read, Grep, Glob
skills: plan-ticket
---
Follow the plan-ticket skill. Use locator for every lookup. Return only the JSON object the schema asks for.
````

File: `template/.claude/agents/implementer.md`
````markdown
---
name: implementer
description: Implements one planned ticket or one fix list, with the tests named in the plan. Use for every code change.
model: sonnet
maxTurns: 80
tools: Agent(locator, test-runner), Read, Edit, Write, Bash, Grep, Glob
skills: implement-ticket
---
Follow the implement-ticket skill. Use locator for lookups and test-runner for test runs, so their output stays out of your context.
````

File: `template/.claude/agents/test-critic.md`
````markdown
---
name: test-critic
description: Prunes new tests that the gates flagged as useless or over budget. Pipeline stage; returns JSON.
model: haiku
maxTurns: 15
tools: Read, Edit, Bash
---
You receive gate results: new tests flagged `passes_on_base`, the acceptance-criterion-to-test map, and the per-criterion budget.

1. Delete every test flagged `passes_on_base`, unless it is the only test mapped to a criterion. Report that case instead of deleting.
2. If a criterion still has more tests than the budget, keep the ones that check observable behaviour through the public interface. Delete those that check internals, mocks or duplicates. Kent Beck's Test Desiderata is the yardstick: behavioural, structure-insensitive, specific, deterministic.
3. Never delete the last test for a criterion. Never edit production code.

Return only the JSON object the schema asks for.
````

File: `template/.claude/agents/reviewer.md`
````markdown
---
name: reviewer
description: Finds defects in a diff against the ticket's acceptance criteria. Author-blind; returns JSON findings.
model: sonnet
maxTurns: 25
tools: Agent(locator), Read, Grep, Glob, Bash
disallowedTools: Edit, Write
skills: review-evidence
---
Follow the review-evidence skill. You see the ticket and the diff only, and that is intentional. Do not ask for the author's plan.
````

File: `template/.claude/agents/prover.md`
````markdown
---
name: prover
description: Writes the smallest failing test that demonstrates one review finding. Pipeline stage; returns JSON.
model: sonnet
maxTurns: 20
tools: Read, Write, Edit, Bash, Grep, Glob
---
You get one finding: file, line, claim, failure and test idea.

1. Write one test, in the project's test style, that fails on the current code if the finding is true.
2. Run only that test.
3. If it passes, the finding is probably false. Say so, and do not weaken the test until it fails.

Return only the JSON object the schema asks for. The harness reruns your test itself; your report of the result is not trusted.
````

### 3.3 Skills

File: `template/.claude/skills/ticket-readiness/SKILL.md`
````markdown
---
name: ticket-readiness
description: Decide whether a ticket is ready for implementation and normalise its acceptance criteria. Use before planning any ticket.
---
A ticket is ready only if all of these hold:

1. Every acceptance criterion is observable: an input or action, and an expected result a test can check.
2. The scope is bounded. You can name the module or area it touches; ask locator if you need to. It does not say "and other improvements" or similar.
3. Every ticket listed as blocking it is done. The input states blocker status.

Output fields:
- `acceptance_criteria`: the criteria rewritten as AC1..ACn, keeping the author's values exactly. Do not invent criteria. If one is implied but not written, put it in `questions_for_author`.
- `missing`: which of rules 1 to 3 fail, quoting the ticket text that fails.
- `questions_for_author`: questions that, once answered, would make the ticket ready.
- `ready`: true only when `missing` is empty.
````

File: `template/.claude/skills/plan-ticket/SKILL.md`
````markdown
---
name: plan-ticket
description: Plan a ready ticket as small steps with an acceptance-criterion-to-test map. Use after readiness and before any code change.
---
Inputs: the ticket, its normalised acceptance criteria, and the handoff file if one exists.

1. Research with locator. Record the files and symbols you will touch, and the existing tests near them.
2. Steps: each step names its files and the change. Keep to what the criteria need. Anything else goes in `out_of_scope`.
3. `ac_tests`: for each criterion, 1 to 3 tests. Each test checks one behaviour through the public interface and is named `test_<unit>_<condition>_<expected>`. Give the full runnable test id and what it asserts.
   - Plan no tests for unchanged behaviour.
   - Plan no tests of private helpers or of mocks of code we own.
4. `risk_notes`: anything that touches auth, money, data migration, concurrency or public APIs, and any existing test you expect to change, with the reason.
5. Keep the plan under 80 lines when rendered as Markdown.
````

File: `template/.claude/skills/implement-ticket/SKILL.md`
````markdown
---
name: implement-ticket
description: Implement a planned ticket or a fix list, with exactly the planned tests. Use for every code change in the pipeline.
---
1. For each criterion, write the planned tests, then the code that makes them pass. The harness runs every new test against the base commit, so a test that already passes there will be flagged.
2. Change only the files in the plan. If another file must change, add it to `notes` with the reason.
3. Do not modify existing tests unless a criterion requires it. List every modified existing test, with the reason, in `modified_existing_tests`.
4. Extra tests beyond the plan are allowed only for a bug you found while implementing. List each one in `extra_tests` with the reason.
5. Before finishing, ask test-runner to run the lint command and the tests for the files you changed. Fix failures.
6. Fix lists (review findings or mutation survivors): each item names a failing test or a surviving mutant. Make that test pass, or kill that mutant with one targeted test, and change nothing else.

Return only the JSON object the schema asks for.
````

File: `template/.claude/skills/review-evidence/SKILL.md`
````markdown
---
name: review-evidence
description: Report only evidence-backed defects in a diff, scored for confidence. Use for every code review.
---
Report a finding only if all of these hold:

- It points to a changed line in the diff, as file and line.
- It states a concrete failure: this input or state produces this wrong output, crash, data loss or security exposure.
- It is in scope for the ticket's acceptance criteria, or it breaks existing behaviour.

Severity:
- critical: data loss, security exposure, or a crash on the main path.
- high: a wrong result for a valid input within the criteria.
- medium: a wrong result off the main path, or a resource leak.

Do not report style, naming, missing comments, hypothetical future needs or "consider" suggestions.

Confidence, from 0 to 100: how sure you are that the failure happens as stated.
- 90 and above: you traced the exact path.
- Below 50: do not report it.

`test_idea` is the smallest test that would fail if the finding is true.

An empty findings list is a valid and common answer.
````

File: `template/.claude/skills/handoff/SKILL.md`
````markdown
---
name: handoff
description: Write the ticket handoff file with fixed headers, at most 60 lines. Use after each stage and before ending a session.
---
Write `.harness/tickets/<KEY>/handoff.md`, overwriting it, with exactly these headers:

# <KEY> handoff
## Status
One line: stage reached, and done, blocked or escalated.
## Done
Bullets. Each has what changed and where (file or test id).
## Decisions
Bullets. Each has the decision and why.
## Open questions
Bullets, or "none".
## Next step
One concrete action.
## Gotchas
Bullets, or "none". Only things a fresh session would otherwise get wrong.

Rules: at most 60 lines, facts only from your input, no transcript excerpts.
````

### 3.4 Repository instructions

`harness install` replaces `@@LINT@@`, `@@TEST_FULL@@` and `@@TEST_ONE@@` with the commands from
`harness.toml`.

File: `template/AGENTS.md`
````markdown
# Agent rules for this repository

These rules apply to every coding agent (Claude Code, Codex, Gemini) working in this repository.

## Commands
- Lint: `@@LINT@@`
- All tests: `@@TEST_FULL@@`
- One test: `@@TEST_ONE@@` (replace `{id}` with the test id)

## Scope
- Work only on the ticket named in `.harness/current_ticket`. Its folder is `.harness/tickets/<KEY>/`.
- Change only what the acceptance criteria need. Note anything else in the handoff; do not fix it.

## Tests
- Every acceptance criterion gets 1 to 3 tests that check behaviour through the public interface.
- The harness rejects new tests that already pass on the base commit, and flags edits to existing tests.

## Review findings
- A finding needs a changed line, a concrete failure and a confidence score. Style is not a finding.

## Handoff
- `.harness/tickets/<KEY>/handoff.md` is the source of truth for status in a fresh session. Read it first.
````

File: `template/CLAUDE.md`
````markdown
@AGENTS.md

## Claude Code specifics
- For interactive ticket work, start with `claude --agent orchestrator`.
- Lookups go to locator, test runs to test-runner, handoff notes to scribe. A PreToolUse hook enforces the allowed agents and their fixed models.
- Never pass `model` to the Agent tool.
````

### M1 acceptance

1. Extract and parse:

```bash
python3 tools/extract_literals.py docs/BUILD_SPEC.md . && python3 -m json.tool template/.claude/settings.json > /dev/null && echo settings-ok
```

2. Write `tests/test_hooks.py`. Feed JSON payloads through `subprocess.run([sys.executable, hook], input=...)`
   and assert the output. Cover these cases:
   - **guard, allowed type.** `{"tool_input": {"subagent_type": "locator"}}` prints nothing.
   - **guard, unknown type.** `general-purpose` or a missing type is denied. The reason names `locator`.
   - **guard, model override.** `{"subagent_type": "locator", "model": "opus"}` is denied. The reason
     contains `pinned to 'haiku'`.
   - **guard, matching model.** `{"subagent_type": "locator", "model": "haiku"}` prints nothing.
   - **session_context, no ticket.** No `.harness/current_ticket`: `additionalContext` equals the routing
     text.
   - **session_context, with handoff.** A ticket and a 70-line handoff: the context includes the first 60
     handoff lines only.
   - **stop_gate, loop guard.** `stop_hook_active: true` prints nothing.
   - **stop_gate, pipeline mode.** `HARNESS_PIPELINE=1` prints nothing.
   - **stop_gate, clean tree.** Nothing changed: prints nothing.
   - **stop_gate, stale handoff.** A file changed after the handoff was written: prints
     `{"decision": "block", ...}`.

3. Run the tests and the linters:

```bash
python -m pytest tests/test_hooks.py -q && ruff check template tools && ruff format --check template tools
```

4. **Live, cost-capped.** Install the template into a scratch copy of the fixture (M2's
   `harness install`), then run:

```bash
claude -p --agent orchestrator --max-budget-usd 0.50 --output-format json "Where is the Product class defined? Answer with path:line." > /tmp/orch.json; python3 -c "import json; d = json.load(open('/tmp/orch.json')); print(d['result']); print(list(d.get('modelUsage', {})))"
```

   Expected: the answer is `pricing/catalog.py:<line>`, and `modelUsage` lists a Haiku model (from the
   locator) and no Opus model.

5. **Interactive check, in the same copy.** Run `claude --agent orchestrator`:
   - `/agents` does not list Explore or Plan.
   - `/hooks` lists the three hooks.
   - Asking "use general-purpose with model opus to find X" ends with a denial and a locator call.

## 4. M2: the driver core

Package: `src/harness/`, run as `python -m harness`. Use `tomllib`, `json`, `subprocess`, `pathlib`,
`dataclasses` and `argparse`. No third-party runtime dependencies.

### 4.1 Commands

```text
python -m harness --version
python -m harness install <repo> [--config harness.toml]
python -m harness queue [--tickets local|jira]
python -m harness run <KEY>|--all [--profile tiered|baseline] [--stub] [--from <stage>] [--forge local|gitlab] [--tickets local|jira]
python -m harness gates --base <sha> [--head <sha>] [--ticket <KEY>] [--report <path>]
python -m harness review --base <sha> [--head <sha>] [--ticket <KEY>] [--mr <iid>] [--post-notes]
python -m harness eval --profile tiered|baseline [--stub] [--tickets K1,K2] [--max-usd X]
python -m harness eval-review --profile tiered|baseline [--stub] [--max-usd X]
python -m harness report <report.json> [<other report.json>]
```

`install` copies `template/` into the repository and fills the `@@...@@` command tokens. It also:

- writes `.harness/wiki_search`, an executable wrapper around `wiki.search_cmd`, only when that is set;
- adds `.harness/` and `.claude/settings.local.json` to `.gitignore`;
- **never overwrites** an existing `CLAUDE.md`, `AGENTS.md` or `.claude/settings.json`. It writes
  `*.harness.*` siblings instead, prints which files need a manual merge, and exits with code 3.

### 4.2 Configuration

File: `harness.toml`
```toml
# Points at the eval fixture. Copy and adapt per target repository.
# Budget values are starting points; calibrate them from M0 and the first eval run.

[project]
key_prefix = "PRC"
base_branch = "main"
repo = "/ledger/fixture-repo"
tickets_dir = "eval/fixture/tickets"
work_dir = "/ledger/work"
ledger = "/ledger/ledger.jsonl"

[claude]
bin = "claude"
permission_mode = "acceptEdits"
stage_timeout_s = 1800
allowed_tools = [
  "Bash(python -m pytest *)",
  "Bash(ruff *)",
  "Bash(git diff *)",
  "Bash(git status *)",
  "Bash(git log *)",
  "Bash(rg *)",
]

[commands]
lint = "ruff check ."
typecheck = ""
test_full = "python -m pytest -q"
test_affected = ""
test_one = "python -m pytest -q {id}"
collect = "python -m pytest --collect-only -q"
collect_regex = '^\S+::\S+'
test_globs = ["tests/*"]

[tests]
max_per_ac = 3

[mutation]
tool = "builtin-python"
max_mutants = 20
max_per_line = 1
timeout_s = 300
min_risk = "medium"

[risk]
high_paths = ["*/auth/*", "*/payments/*", "*/migrations/*", "infra/*"]
medium_paths = ["pricing/*"]
medium_diff_lines = 150
high_diff_lines = 500
high_labels = ["risk:high"]

[review]
confidence_block = 80
min_confidence = 50
max_fix_loops = 2
line_tolerance = 3
other_lab_cmd = ""

[budget]
ticket_max_usd = 8.0
eval_max_usd = 40.0

[wiki]
search_cmd = ""
update_cmd = ""

[stages.readiness]
agent = "readiness"
model = "haiku"
max_turns = 4
max_usd = 0.10
schema = "schemas/readiness.json"

[stages.plan]
agent = "planner"
model = "sonnet"
model_high_risk = "opus"
max_turns = 30
max_usd = 1.00
schema = "schemas/plan.json"

[stages.implement]
agent = "implementer"
model = "sonnet"
max_turns = 80
max_usd = 3.00
schema = "schemas/implement.json"

[stages.critic]
agent = "test-critic"
model = "haiku"
max_turns = 15
max_usd = 0.20
schema = "schemas/critic.json"

[stages.find]
agent = "reviewer"
model = "sonnet"
max_turns = 25
max_usd = 1.00
schema = "schemas/findings.json"

[stages.prove]
agent = "prover"
model = "sonnet"
max_turns = 20
max_usd = 0.60
schema = "schemas/proof.json"

[stages.handoff]
agent = "scribe"
model = "haiku"
max_turns = 6
max_usd = 0.10

[profiles.tiered]
review_mode = "tiered"
implement_addendum = ""
gates_before_review = true
mutation = true
test_budget = true

[profiles.baseline]
review_mode = "rounds"
review_rounds = ["claude", "other_lab", "claude", "context_free"]
implement_addendum = "Use strict TDD: write a failing test before every behaviour you add."
gates_before_review = false
mutation = false
test_budget = false
max_fix_loops = 3
```

Config rules:

- **Validation.** `config.py` loads this file into dataclasses. Each missing or wrongly typed key raises
  an error naming the key and the file.
- **Path patterns.** All path patterns use `fnmatch` on POSIX paths relative to the repository root, so
  `*` crosses directory separators. Python 3.12's `PurePath.match` does not support `**`.
- **Other lab command.** `other_lab_cmd` is a command template with `{schema}` and `{out}` placeholders.
  The prompt goes on stdin; the JSON result is read from `{out}`. Examples:
  - `codex exec --sandbox read-only --output-schema {schema} -o {out} -`
  - `sh -c 'gemini -p "$(cat)" --output-format json > {out}'`. Gemini does not enforce the schema, so
    validate its output yourself.

  When `other_lab_cmd` is empty, the refuter step is skipped and the ledger records it as `skipped`.

### 4.3 Stage output schemas

These schemas are passed to `--json-schema` and to the other lab's `--output-schema`. They are written to
satisfy OpenAI's strict mode as well: every property is required, and `additionalProperties` is false.

File: `schemas/readiness.json`
```json
{
  "type": "object",
  "properties": {
    "ready": {"type": "boolean"},
    "acceptance_criteria": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "text": {"type": "string"}},
        "required": ["id", "text"],
        "additionalProperties": false
      }
    },
    "missing": {"type": "array", "items": {"type": "string"}},
    "questions_for_author": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["ready", "acceptance_criteria", "missing", "questions_for_author"],
  "additionalProperties": false
}
```

File: `schemas/plan.json`
```json
{
  "type": "object",
  "properties": {
    "summary": {"type": "string"},
    "steps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "files": {"type": "array", "items": {"type": "string"}},
          "change": {"type": "string"}
        },
        "required": ["id", "files", "change"],
        "additionalProperties": false
      }
    },
    "ac_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ac": {"type": "string"},
          "tests": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {"id": {"type": "string"}, "asserts": {"type": "string"}},
              "required": ["id", "asserts"],
              "additionalProperties": false
            }
          }
        },
        "required": ["ac", "tests"],
        "additionalProperties": false
      }
    },
    "out_of_scope": {"type": "array", "items": {"type": "string"}},
    "risk_notes": {"type": "array", "items": {"type": "string"}}
  },
  "required": ["summary", "steps", "ac_tests", "out_of_scope", "risk_notes"],
  "additionalProperties": false
}
```

File: `schemas/implement.json`
```json
{
  "type": "object",
  "properties": {
    "changed_files": {"type": "array", "items": {"type": "string"}},
    "ac_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ac": {"type": "string"},
          "test_ids": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["ac", "test_ids"],
        "additionalProperties": false
      }
    },
    "extra_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["id", "reason"],
        "additionalProperties": false
      }
    },
    "modified_existing_tests": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["id", "reason"],
        "additionalProperties": false
      }
    },
    "notes": {"type": "string"}
  },
  "required": ["changed_files", "ac_tests", "extra_tests", "modified_existing_tests", "notes"],
  "additionalProperties": false
}
```

File: `schemas/critic.json`
```json
{
  "type": "object",
  "properties": {
    "deleted": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["id", "reason"],
        "additionalProperties": false
      }
    },
    "kept_over_budget": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {"id": {"type": "string"}, "reason": {"type": "string"}},
        "required": ["id", "reason"],
        "additionalProperties": false
      }
    }
  },
  "required": ["deleted", "kept_over_budget"],
  "additionalProperties": false
}
```

File: `schemas/findings.json`
```json
{
  "type": "object",
  "properties": {
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "severity": {"type": "string", "enum": ["critical", "high", "medium"]},
          "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
          "file": {"type": "string"},
          "line": {"type": "integer"},
          "claim": {"type": "string"},
          "failure": {"type": "string"},
          "test_idea": {"type": "string"}
        },
        "required": ["id", "severity", "confidence", "file", "line", "claim", "failure", "test_idea"],
        "additionalProperties": false
      }
    }
  },
  "required": ["findings"],
  "additionalProperties": false
}
```

File: `schemas/refutations.json`
```json
{
  "type": "object",
  "properties": {
    "refutations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "finding_id": {"type": "string"},
          "verdict": {"type": "string", "enum": ["refuted", "stands", "unsure"]},
          "reason": {"type": "string"},
          "counter_evidence": {"type": "string"}
        },
        "required": ["finding_id", "verdict", "reason", "counter_evidence"],
        "additionalProperties": false
      }
    }
  },
  "required": ["refutations"],
  "additionalProperties": false
}
```

File: `schemas/proof.json`
```json
{
  "type": "object",
  "properties": {
    "finding_id": {"type": "string"},
    "test_id": {"type": "string"},
    "test_file": {"type": "string"},
    "could_not_prove_because": {"type": "string"}
  },
  "required": ["finding_id", "test_id", "test_file", "could_not_prove_because"],
  "additionalProperties": false
}
```

### 4.4 Module contracts

| Module | Responsibility | Key functions |
|---|---|---|
| `config.py` | Load and validate `harness.toml` into frozen dataclasses; apply the selected profile | `load(path, profile) -> Config` |
| `claude.py` | Run one stage agent headless and return a structured result | `run_agent(stage, prompt, cwd, model=None) -> AgentResult` |
| `tickets.py` | Ticket model, local adapter, dependency ordering | `load_local(dir) -> list[Ticket]`, `order(tickets) -> list[Ticket]` |
| `forge.py` | Branches, commits, MR text, merge (local forge here; GitLab in M6) | `start(ticket)`, `open_mr(ticket, body)`, `merge(ticket)` |
| `pipeline.py` | Per-ticket state machine with resume | `run_ticket(cfg, ticket, profile) -> TicketState` |
| `stages.py` | Prompt assembly and output handling per stage | one function per stage |
| `gates.py` | Deterministic gates (M3) | `run_gates(cfg, base, head, implement) -> GateReport` |
| `mutate.py` | Changed-line mutation (M3) | `changed_lines(...)`, `run_mutation(...)` |
| `risk.py` | Risk tier from the diff (M4) | `tier(cfg, base, head, ticket) -> Risk` |
| `review.py` | Find, refute, prove, decide (M4) | `run_review(cfg, ticket, base, head, tier) -> ReviewReport` |
| `ledger.py` | Append-only JSONL ledger | `record(entry)`, `load(path)` |
| `wiki.py` | Optional wiki commands | `search(query)`, `update(ticket, handoff)` |
| `eval.py` | Benchmark runs and reports (M5) | `run_eval(...)`, `run_eval_review(...)`, `compare(...)` |
| `jira.py`, `gitlab.py` | Adapters (M6) | see M6 |

Error rule (all modules): an error message states what failed and the value that caused it. Raise
`HarnessError(message)`, which the CLI prints before exiting with code 2. Never swallow an exception
without a real recovery.

#### claude.py

- **Command line:** `[bin, "-p", "--agent", agent, "--model", model, "--max-turns", N, "--max-budget-usd",
  B, "--output-format", "json", "--permission-mode", mode]`. Add `["--json-schema", <schema>]` when the
  stage has a schema; use the inline or path form that M0 recorded.
- **Prompt:** goes on stdin, as in the existing `shared/scripts/workflow_common.py` pattern.
- **Process environment:** the caller's environment plus `HARNESS_PIPELINE=1`. The working directory is
  the ticket worktree.
- **Allowed tools** are not passed on the command line. Before each run, `claude.py` writes
  `.claude/settings.local.json` in the worktree with `{"permissions": {"allow": cfg.claude.allowed_tools}}`.
  This avoids quoting problems with patterns that contain spaces.
- **Result parsing:** read stdout as JSON. Required keys are those recorded in M0. A missing key raises an
  error naming the key and the stage. Map `subtype` to the outcome values `ok`, `max_turns`,
  `budget_exceeded` and `error`, using the values M0 recorded. A timeout (`stage_timeout_s`) kills the
  process and records `timeout`.
- **`AgentResult`** is a dataclass with these fields: `outcome`, `text`, `structured` (a dict or None),
  `cost_usd`, `duration_ms`, `num_turns` and `model_usage`.
- **Ledger:** every call appends one ledger entry (section 4.6).

#### tickets.py

- **Local ticket file:** `tickets/<KEY>.md`. The front matter is TOML between `+++` lines and holds `key`,
  `title`, `rank`, `blocked_by` (a list of keys) and `labels`. The body is the description.
- **`order()`:** Kahn's algorithm; among ready tickets, the lowest `(rank, key)` goes first.
  - A cycle raises `HarnessError` naming the keys in the cycle.
  - An unknown blocker key raises an error naming both keys.
- **Done:** a ticket is done when its `state.json` status is `done` (local forge), or its Jira status
  category is `done` (M6).

#### pipeline.py

- **Stage order:** `readiness, plan, implement, gates, critic, review, fix, handoff, mr, merge`. The
  `critic` and `fix` stages are conditional. `fix` loops back through `gates` and `review` at most
  `max_fix_loops` times.
- **Ticket folder:** `work_dir/<KEY>/` holds the worktree on branch `harness/<KEY>`. The worktree's
  `.harness/tickets/<KEY>/` holds the stage files: `readiness.json`, `plan.json`, `plan.md`,
  `implement.json`, `gates.json`, `findings.json`, `review.json`, `handoff.md`, `mr.md` and `state.json`.
- **`state.json`:**
  ```text
  {key, base_sha, branch, risk: {tier, reasons}, completed: [stage...],
   fix_loops, cost_usd, status: running|done|bounced|escalated|failed, last_error}
  ```
- **Resume:** `run <KEY>` skips the stages listed in `completed`. `--from <stage>` clears that stage and
  everything after it.
- **Start of a ticket:**
  1. Create the worktree from `base_branch`.
  2. Record `base_sha` and write `.harness/current_ticket`.
  3. Run `test_full` on the base. If the base suite is red, escalate with `base branch red`; do not
     implement on a red base.
- **Readiness bounce:** write `readiness.json` and set status `bounced`. Locally, also write
  `tickets/<KEY>.questions.md`; in M6, post a Jira comment.
- **Ticket budget:** once the summed `cost_usd` passes `budget.ticket_max_usd`, the ticket stops with
  status `escalated` and reason `budget`.
- **Model choice:** the plan stage uses `model_high_risk` when the risk tier is `high`. Risk is computed
  from the ticket's labels before planning, and recomputed from the diff after implementation.
- **Prompts:** `stages.py` puts stable instructions first and variable content last, so prompt caching
  can apply. The reviewer's prompt contains only the ticket title, the acceptance criteria and the diff:
  never the plan, the handoff or `implement.json`.

#### Stub CLIs for tests

`tests/stub_claude.py` is an executable that behaves like `claude -p` for the agents above:

- It reads `--agent` and the stdin prompt.
- It prints JSON with every result key M0 recorded, `total_cost_usd: 0` and the structured output for
  that agent.
- Readiness: `ready: true` when the prompt contains `Acceptance criteria`, otherwise `ready: false` with a
  question.
- Implementer: copies `eval/fixture/reference/pricing/<module>.py` for the ticket, plus the matching hidden
  test file renamed to `tests/test_<module>.py`, into the worktree.
- Reviewer: returns no findings.

`tests/stub_other_lab.py` writes `{"refutations": []}` to `{out}`. Stub mode checks control flow and metric
plumbing only; its quality numbers mean nothing.

### 4.5 MR description template

File: `template/mr_description.md`
```markdown
## {key}: {title}

Risk tier: **{risk_tier}** ({risk_reasons})

### Acceptance criteria and tests
| AC | Test | Fails on base | Passes on head |
|---|---|---|---|
{ac_rows}

### Gates
{gate_rows}

### Review
- Proven (blocking): {proven_count}
- Unproven, refuter agrees (blocking, needs human attention): {unproven_blocking_count}
- Refuted or notes (non-blocking): {note_count}

{findings_list}

### Mutation testing on changed lines
{mutation_summary}

### Cost
{cost_rows}

Handoff: `.harness/tickets/{key}/handoff.md`
```

### 4.6 Ledger entry

One JSON object per line:

```text
{ts, run_id, profile, ticket, stage, agent, model, outcome, cost_usd, duration_ms, num_turns,
 model_usage, details}
```

Deterministic stages record `model: null` and `cost_usd: 0`. `details` holds stage-specific data such as
gate results, finding counts or the bounce reason.

### M2 acceptance

```bash
python -m pytest tests -q -k "not live" && ruff check src tests && ruff format --check src tests
```

The suite (all against the stubs) covers:

- **Order.** `order()` on the fixture tickets returns `PRC-1, PRC-2, PRC-3, PRC-4, PRC-5, PRC-6`.
- **Cycle.** A cycle raises an error naming every key in it.
- **Resume.** A stage that fails, then succeeds on a rerun, leaves the earlier stages untouched.
- **Ticket budget.** Passing the budget gives status `escalated`.
- **Ledger.** Every entry has all the fields in 4.6.
- **Bounce.** `run PRC-6 --stub` ends with status `bounced` and writes `tickets/PRC-6.questions.md`.

Then run these two commands:

```bash
python -m harness queue
```

```bash
python -m harness run PRC-1 --stub
```

Expected: `queue` prints the order above, and `run` ends with status `done`, the merge recorded and a
ledger cost of 0.

## 5. M3: deterministic gates

`gates.py`, given `base` and `head` commits in the target repository:

1. **Changed files.** Run `git diff --name-status base head`. Test files are those matching
   `commands.test_globs`. A modified or deleted existing test file sets `existing_tests_touched`, which
   `risk.py` reads.
2. **Collect test ids** with `commands.collect`, keeping lines that match `collect_regex`:
   - on a clean worktree of `base`, giving `base_ids`;
   - on `head`, giving `head_ids`.

   `new_ids` is `head_ids - base_ids`; `removed_ids` is `base_ids - head_ids`.
3. **FAIL_TO_PASS.** Make a worktree of `base` and copy in the test files that changed in `head` (test
   files only). Run every new id there with `test_one`; exit code 0 means `base_pass`. Run every new id on
   `head`, giving `head_pass`. A test is valid when `not base_pass and head_pass`.
   - Flags: `passes_on_base`, `fails_on_head`.
   - A new test that fails on base because of an import error still counts as failing on base, as in
     SWE-bench.
4. **AC coverage.** `implement.json.ac_tests` intersected with the valid tests. Any criterion without a
   valid test goes into `missing_acs`.
5. **Budget.** Count the valid tests per criterion. More than `tests.max_per_ac` goes into `over_budget`.
   Tests in no criterion and not in `extra_tests` go into `unmapped`.
6. **Lint and typecheck:** pass or fail by exit code. An empty command is skipped.
7. **PASS_TO_PASS.** Run `test_affected` on `head`, or `test_full` when it is empty; exit code 0 means
   pass. Run `test_full` before merge either way.
8. **Mutation** (section 5.1): only when the profile enables it and the risk tier is at least
   `mutation.min_risk`.

**Pass rule:** `gates.json` passes when lint and typecheck pass, no test fails on head, `missing_acs` is
empty and PASS_TO_PASS passes.

**Critic rule:** `passes_on_base`, `over_budget` or `unmapped` sends the ticket to the `critic` stage,
which is not a failure. Gates run once more after the critic.

### 5.1 Changed-line mutation (`mutate.py`)

- **Changed lines.** Parse `git diff -U0 base head -- <file>` hunk headers `@@ -a,b +c,d @@` into
  `{file: set(lines)}`. Use only non-test files.
- **The `builtin-python` tool:**
  - **Operator order.** For each changed `.py` file, parse with `ast` and visit nodes whose `lineno` is a
    changed line. At most one mutant per line (`max_per_line`): use the first operator in this order that
    applies.
    1. `Compare`: `<` and `<=`, `>` and `>=`, `==` and `!=`.
    2. `BoolOp`: `and` and `or`. `UnaryOp Not`: replace with its operand.
    3. A call to `max` or `min`: swap the name.
    4. `BinOp`: `+` and `-`, `*` and `/`.
    5. An int `Constant` (not bool): c becomes c + 1.
    6. A `Return` with a non-None value: return `None`.
  - **Cap and order.** At most `max_mutants`, ordered by (file, line).
  - **Running a mutant.** Write `ast.unparse(mutated_tree)` over the file in a dedicated mutation worktree
    of `head`. Run the ticket's valid new tests plus `test_affected` (or `test_full`). A non-zero exit
    means the mutant was killed. Restore the file before the next mutant.
  - **Time box.** Stop at `mutation.timeout_s` and record `timed_out` and the untested count.
- **The `stryker` tool:** build `--mutate path:start-end` arguments from the changed line ranges. Run
  `npx stryker run --incremental --mutate ...`, then read `reports/mutation/mutation.json` and take mutants
  with status `Survived`.
- **The `cargo-mutants` tool:** `cargo mutants --in-diff <diff file>`, then read `mutants.out/outcomes.json`.
  Verify the flag on your version.
- **Survivor record:** `{file, line, operator, original, mutated}`. Survivors go into `gates.json`,
  feed the reviewer as evidence, and turn into "kill this survivor" items in a fix list.

### M3 acceptance

Write `tests/test_gates.py` and `tests/test_mutate.py` against throwaway git repositories made in
`tmp_path`. Cover:

- a new test that passes on base is flagged `passes_on_base`;
- a new test that fails on head is flagged `fails_on_head`, and the gate fails;
- a criterion without a valid test appears in `missing_acs`;
- breaking an existing test fails PASS_TO_PASS;
- 4 valid tests for one criterion with `max_per_ac = 3` gives `over_budget`;
- mutation:
  - a weak test (asserts only that the result is not None) leaves a `Compare` mutant surviving;
  - a strong test kills it;
  - `max_mutants` and `timeout_s` are respected;
- `changed_lines` parses `@@ -10,0 +11,3 @@` as lines 11, 12 and 13.

```bash
python -m pytest tests/test_gates.py tests/test_mutate.py -q
```

## 6. M4: risk and review

### 6.1 Risk (`risk.py`)

| Tier | Any of |
|---|---|
| high | a changed path matches `high_paths`; existing tests modified or removed; changed non-test lines > `high_diff_lines`; a label in `high_labels` |
| medium | a changed path matches `medium_paths`; changed non-test lines > `medium_diff_lines` |
| low | otherwise |

Changed lines come from `git diff --numstat` (added plus deleted, non-test files). Return
`Risk(tier, reasons: list[str])`, with one reason per rule that matched.

### 6.2 Review (`review.py`), profile `tiered`

1. **Find.** Run the reviewer agent. The prompt holds the ticket title, the acceptance criteria and
   `git diff -U5 base head`. For `high` risk, also run `other_lab_cmd` with the same prompt and
   `schemas/findings.json`, and merge the two lists, keeping a `source` tag on each finding.
2. **Filter.** Drop findings with confidence below `review.min_confidence`, and findings whose file is not
   in the diff or whose line is not within `line_tolerance` of a changed line. Record the drops in the
   ledger `details`.
3. **Refute** (medium and high). Send the surviving findings, each with ±20 lines of `head` code around its
   line and the criteria, to `other_lab_cmd` with `schemas/refutations.json`. For high risk, findings that
   came from the other lab are refuted by the Claude reviewer agent instead, using the same schema.
4. **Prove** each finding with severity critical or high and a verdict of `stands` or `unsure`. On low risk,
   prove only critical findings with confidence of at least `confidence_block`.
   1. Make a scratch worktree of `head` and run the prover agent there with that one finding.
   2. Copy the reported `test_file` into a second clean worktree of `head` and run `test_one` on `test_id`.
   3. **Proven** if it fails. **Disproved** if it passes.
5. **Decide:**

   | Condition | Result |
   |---|---|
   | proven | blocking; the proving test is committed to the branch as a regression test |
   | prover wrote no test, refuter says `stands`, confidence >= `confidence_block` | blocking-unproven (shown separately to the human) |
   | refuted, or disproved by test | note |
   | medium severity | note |

6. **Fix loop.** If anything blocks:
   1. Build a fix list: proven findings with their failing tests, blocking-unproven findings, and mutation
      survivors on lines covered by a criterion.
   2. Run `implement` in fix mode.
   3. Run `gates`, then `review` again.
   4. After `max_fix_loops`, set the ticket to `escalated`, render the MR as a draft, and put the reason in
      the handoff.
7. **MR description.** `forge.open_mr` renders `template/mr_description.md` from `gates.json`,
   `review.json`, `state.json` and the ledger.

### 6.3 Review, profile `baseline` (approximates today's flow)

- Run `review_rounds` in order: Claude reviewer, other lab, Claude reviewer, then a `context_free` round
  (the reviewer gets the diff only, with no criteria).
- Every finding with medium severity or above, from any round, blocks.
- No refuter, no prover, no mutation, no test budget. Fix loops up to `max_fix_loops = 3`.

### M4 acceptance

`tests/test_risk.py` and `tests/test_review.py` use stubbed agent outputs to cover each row of both tables
above. They also check that the MR description renders with no unreplaced `{...}` fields.

```bash
python -m pytest tests/test_risk.py tests/test_review.py -q
```

## 7. M5: evaluation

### 7.1 Fixture

The fixture is a small pricing library:

- 6 tickets. PRC-1 blocks PRC-2, PRC-3 and PRC-5; PRC-4 needs PRC-2 and PRC-3. PRC-6 is deliberately vague.
- 22 hidden acceptance tests, which agents never see.
- A reference solution.
- 6 seeded-bug variants and 4 clean variants of that solution.

`eval` copies `eval/fixture/repo` to `project.repo`, runs `git init`, and commits it on `main`. Hidden tests
and reference files stay in the kit, outside every agent's working directory.

File: `eval/fixture/repo/pyproject.toml`
```toml
[project]
name = "pricing"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B"]
```

File: `eval/fixture/repo/pricing/__init__.py`
```python
"""Pricing library used as the harness benchmark fixture."""
```

File: `eval/fixture/repo/pricing/catalog.py`
```python
"""Product catalogue records."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Product:
    """A sellable product identified by its SKU."""

    sku: str
    name: str

    def __post_init__(self) -> None:
        if not self.sku.strip():
            raise ValueError(f"Product SKU must not be blank, got {self.sku!r}")
```

File: `eval/fixture/repo/tests/test_catalog.py`
```python
import pytest

from pricing.catalog import Product


def test_product_valid_sku_keeps_fields() -> None:
    product = Product(sku="SKU-1", name="Pen")
    assert (product.sku, product.name) == ("SKU-1", "Pen")


def test_product_blank_sku_raises_value_error() -> None:
    with pytest.raises(ValueError, match="blank"):
        Product(sku="  ", name="Pen")
```

#### Tickets

File: `eval/fixture/tickets/PRC-1.md`
````markdown
+++
key = "PRC-1"
title = "Money value type"
rank = 1
blocked_by = []
labels = []
+++
Add `pricing/money.py` with an immutable `Money(amount, currency)` value type and a `CurrencyMismatch` exception.

Acceptance criteria
- AC1: `Money(Decimal("1.10"), "USD") + Money(Decimal("2.20"), "USD") == Money(Decimal("3.30"), "USD")`.
- AC2: Adding Money values in different currencies raises `CurrencyMismatch`; the message names both currencies.
- AC3: A float amount raises `TypeError`; `Decimal` and `int` amounts are accepted (`Money(3, "USD").amount == Decimal("3.00")`).
- AC4: Amounts are rounded to 2 decimal places with ROUND_HALF_EVEN on construction: `Money(Decimal("2.665"), "USD").amount == Decimal("2.66")`.
- AC5: `Money(Decimal("1.25"), "USD") * 3 == Money(Decimal("3.75"), "USD")`.
````

File: `eval/fixture/tickets/PRC-2.md`
````markdown
+++
key = "PRC-2"
title = "Price list lookup"
rank = 2
blocked_by = ["PRC-1"]
labels = []
+++
Add `pricing/pricelist.py` with `PriceList(items)`, built from `(sku, Money)` pairs, and an `UnknownSku` exception (a `KeyError`).

Acceptance criteria
- AC1: `PriceList([("SKU-1", Money(Decimal("9.99"), "USD"))]).price_for("SKU-1")` returns that Money.
- AC2: `price_for` with an unknown SKU raises `UnknownSku`; the message contains the SKU.
- AC3: Building a PriceList with the same SKU twice raises `ValueError`; the message contains the SKU.
- AC4: PriceList instances do not share prices: after building `PriceList([("SKU-A", p)])`, `PriceList([("SKU-B", p)]).price_for("SKU-A")` raises `UnknownSku`.
````

File: `eval/fixture/tickets/PRC-3.md`
````markdown
+++
key = "PRC-3"
title = "Percentage discounts"
rank = 3
blocked_by = ["PRC-1"]
labels = []
+++
Add `pricing/discount.py` with `apply_discount(price: Money, percent: Decimal) -> Money`.

Acceptance criteria
- AC1: 15% off USD 100.00 is USD 85.00.
- AC2: The result never goes below zero: 150% off USD 10.00 is USD 0.00.
- AC3: The discounted amount is rounded to cents with ROUND_HALF_EVEN: 50% off USD 10.05 is USD 5.02.
- AC4: A negative percent raises `ValueError`; the message contains the percent.
````

File: `eval/fixture/tickets/PRC-4.md`
````markdown
+++
key = "PRC-4"
title = "Quantity tier pricing"
rank = 4
blocked_by = ["PRC-2", "PRC-3"]
labels = []
+++
Add `pricing/tiers.py` with `TierTable(sku_tiers)` and `line_total(table, sku, qty, percent=Decimal(0))`. `sku_tiers` maps a SKU to a list of `(min_qty, Money)` breaks.

Acceptance criteria
- AC1: With breaks `[(1, USD 10.00), (10, USD 9.00), (50, USD 8.00)]`, `unit_price("SKU-1", 10)` is USD 9.00 (a break applies from its min_qty, inclusive).
- AC2: With the same breaks, `unit_price("SKU-1", 9)` is USD 10.00.
- AC3: `line_total(table, "SKU-1", 12, percent=Decimal("10"))` is USD 97.20 (12 x 9.00 = 108.00, then 10% off via `apply_discount`).
- AC4: A quantity below 1 raises `ValueError`; the message contains the quantity.
- AC5: A SKU without tiers raises `UnknownSku` from `pricing.pricelist`.
````

File: `eval/fixture/tickets/PRC-5.md`
````markdown
+++
key = "PRC-5"
title = "Money formatting"
rank = 5
blocked_by = ["PRC-1"]
labels = []
+++
Add `pricing/formatting.py` with `format_money(money: Money) -> str`.

Acceptance criteria
- AC1: `format_money(Money(Decimal("1234.5"), "USD")) == "USD 1,234.50"`.
- AC2: `format_money(Money(Decimal("-1234.5"), "USD")) == "USD -1,234.50"`.
- AC3: `format_money(Money(Decimal("0"), "EUR")) == "EUR 0.00"`.
````

File: `eval/fixture/tickets/PRC-6.md`
````markdown
+++
key = "PRC-6"
title = "Make pricing faster and other improvements"
rank = 6
blocked_by = []
labels = []
+++
Pricing feels slow sometimes. Make it faster and clean up anything else that looks off.
````

#### Hidden acceptance tests (scoring only)

File: `eval/fixture/hidden/test_prc_1.py`
```python
from decimal import Decimal

import pytest

from pricing.money import CurrencyMismatch, Money


def test_money_same_currency_add_returns_sum() -> None:
    total = Money(Decimal("1.10"), "USD") + Money(Decimal("2.20"), "USD")
    assert total == Money(Decimal("3.30"), "USD")


def test_money_mixed_currency_add_raises_naming_both() -> None:
    with pytest.raises(CurrencyMismatch) as excinfo:
        Money(Decimal("1"), "USD") + Money(Decimal("1"), "EUR")
    assert "USD" in str(excinfo.value)
    assert "EUR" in str(excinfo.value)


def test_money_float_amount_raises_type_error() -> None:
    with pytest.raises(TypeError):
        Money(1.5, "USD")


def test_money_int_amount_is_accepted() -> None:
    assert Money(3, "USD").amount == Decimal("3.00")


def test_money_construction_rounds_half_even() -> None:
    assert Money(Decimal("2.665"), "USD").amount == Decimal("2.66")


def test_money_times_int_multiplies_amount() -> None:
    assert Money(Decimal("1.25"), "USD") * 3 == Money(Decimal("3.75"), "USD")
```

File: `eval/fixture/hidden/test_prc_2.py`
```python
from decimal import Decimal

import pytest

from pricing.money import Money
from pricing.pricelist import PriceList, UnknownSku

PEN = Money(Decimal("9.99"), "USD")


def test_pricelist_known_sku_returns_price() -> None:
    assert PriceList([("SKU-1", PEN)]).price_for("SKU-1") == PEN


def test_pricelist_unknown_sku_raises_naming_sku() -> None:
    with pytest.raises(UnknownSku, match="SKU-404"):
        PriceList([("SKU-1", PEN)]).price_for("SKU-404")


def test_pricelist_duplicate_sku_raises_naming_sku() -> None:
    with pytest.raises(ValueError, match="SKU-9"):
        PriceList([("SKU-9", PEN), ("SKU-9", PEN)])


def test_pricelist_instances_do_not_share_prices() -> None:
    PriceList([("SKU-A", PEN)])
    with pytest.raises(UnknownSku):
        PriceList([("SKU-B", PEN)]).price_for("SKU-A")
```

File: `eval/fixture/hidden/test_prc_3.py`
```python
from decimal import Decimal

import pytest

from pricing.discount import apply_discount
from pricing.money import Money


def usd(amount: str) -> Money:
    return Money(Decimal(amount), "USD")


def test_apply_discount_fifteen_percent_reduces_price() -> None:
    assert apply_discount(usd("100.00"), Decimal("15")) == usd("85.00")


def test_apply_discount_over_hundred_percent_floors_at_zero() -> None:
    assert apply_discount(usd("10.00"), Decimal("150")) == usd("0.00")


def test_apply_discount_half_cent_rounds_half_even() -> None:
    assert apply_discount(usd("10.05"), Decimal("50")) == usd("5.02")


def test_apply_discount_negative_percent_raises_naming_percent() -> None:
    with pytest.raises(ValueError, match="-5"):
        apply_discount(usd("10.00"), Decimal("-5"))
```

File: `eval/fixture/hidden/test_prc_4.py`
```python
from decimal import Decimal

import pytest

from pricing.money import Money
from pricing.pricelist import UnknownSku
from pricing.tiers import TierTable, line_total


def usd(amount: str) -> Money:
    return Money(Decimal(amount), "USD")


TABLE = TierTable({"SKU-1": [(1, usd("10.00")), (10, usd("9.00")), (50, usd("8.00"))]})


def test_unit_price_at_break_uses_that_break() -> None:
    assert TABLE.unit_price("SKU-1", 10) == usd("9.00")


def test_unit_price_below_break_uses_previous_break() -> None:
    assert TABLE.unit_price("SKU-1", 9) == usd("10.00")


def test_line_total_applies_discount_to_total() -> None:
    assert line_total(TABLE, "SKU-1", 12, percent=Decimal("10")) == usd("97.20")


def test_unit_price_quantity_below_one_raises_naming_quantity() -> None:
    with pytest.raises(ValueError, match="0"):
        TABLE.unit_price("SKU-1", 0)


def test_unit_price_sku_without_tiers_raises_unknown_sku() -> None:
    with pytest.raises(UnknownSku):
        TABLE.unit_price("SKU-404", 1)
```

File: `eval/fixture/hidden/test_prc_5.py`
```python
from decimal import Decimal

from pricing.formatting import format_money
from pricing.money import Money


def test_format_money_positive_groups_thousands() -> None:
    assert format_money(Money(Decimal("1234.5"), "USD")) == "USD 1,234.50"


def test_format_money_negative_keeps_sign() -> None:
    assert format_money(Money(Decimal("-1234.5"), "USD")) == "USD -1,234.50"


def test_format_money_zero_shows_two_decimals() -> None:
    assert format_money(Money(Decimal("0"), "EUR")) == "EUR 0.00"
```

#### Reference solution (stub implementer and review variants)

File: `eval/fixture/reference/pricing/money.py`
```python
"""Immutable money values with currency checks."""

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal

CENT = Decimal("0.01")


class CurrencyMismatch(ValueError):
    """Raised when combining Money values in different currencies."""


@dataclass(frozen=True)
class Money:
    """An amount rounded to cents in a single currency."""

    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, (Decimal, int)):
            raise TypeError(
                f"Money amount must be Decimal or int, got {type(self.amount).__name__}"
            )
        rounded = Decimal(self.amount).quantize(CENT, rounding=ROUND_HALF_EVEN)
        object.__setattr__(self, "amount", rounded)

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise CurrencyMismatch(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, factor: int | Decimal) -> "Money":
        return Money(self.amount * factor, self.currency)
```

File: `eval/fixture/reference/pricing/pricelist.py`
```python
"""Look up prices by SKU."""

from collections.abc import Iterable

from pricing.money import Money


class UnknownSku(KeyError):
    """Raised when a SKU has no price."""


class PriceList:
    """Prices keyed by SKU, built once from (sku, price) pairs."""

    def __init__(self, items: Iterable[tuple[str, Money]]) -> None:
        self._prices: dict[str, Money] = {}
        for sku, price in items:
            if sku in self._prices:
                raise ValueError(f"Duplicate SKU in price list: {sku}")
            self._prices[sku] = price

    def price_for(self, sku: str) -> Money:
        """Return the price for sku."""
        try:
            return self._prices[sku]
        except KeyError:
            raise UnknownSku(f"No price for SKU {sku}") from None
```

File: `eval/fixture/reference/pricing/discount.py`
```python
"""Percentage discounts on money values."""

from decimal import ROUND_HALF_EVEN, Decimal

from pricing.money import CENT, Money

HUNDRED = Decimal(100)


def apply_discount(price: Money, percent: Decimal) -> Money:
    """Return price reduced by percent, never below zero, rounded half-even to cents."""
    if percent < 0:
        raise ValueError(f"Discount percent must not be negative, got {percent}")
    discounted = price.amount * (HUNDRED - percent) / HUNDRED
    discounted = max(discounted, Decimal(0))
    return Money(discounted.quantize(CENT, rounding=ROUND_HALF_EVEN), price.currency)
```

File: `eval/fixture/reference/pricing/tiers.py`
```python
"""Quantity break pricing per SKU."""

from collections.abc import Mapping, Sequence
from decimal import Decimal

from pricing.discount import apply_discount
from pricing.money import Money
from pricing.pricelist import UnknownSku


class TierTable:
    """Unit prices per SKU that drop at quantity breaks."""

    def __init__(self, sku_tiers: Mapping[str, Sequence[tuple[int, Money]]]) -> None:
        self._tiers = {sku: sorted(breaks, key=lambda b: b[0]) for sku, breaks in sku_tiers.items()}

    def unit_price(self, sku: str, qty: int) -> Money:
        """Return the unit price for qty of sku from the highest break that applies."""
        if qty < 1:
            raise ValueError(f"Quantity must be at least 1, got {qty}")
        breaks = self._tiers.get(sku)
        if not breaks:
            raise UnknownSku(f"No tiers for SKU {sku}")
        price = breaks[0][1]
        for min_qty, tier_price in breaks:
            if qty >= min_qty:
                price = tier_price
        return price


def line_total(table: TierTable, sku: str, qty: int, percent: Decimal = Decimal(0)) -> Money:
    """Return unit price times qty for sku, with the percent discount applied to the total."""
    return apply_discount(table.unit_price(sku, qty) * qty, percent)
```

File: `eval/fixture/reference/pricing/formatting.py`
```python
"""Human-readable money strings."""

from pricing.money import Money


def format_money(money: Money) -> str:
    """Return text such as 'USD -1,234.50': currency, sign, grouped digits, two decimals."""
    sign = "-" if money.amount < 0 else ""
    return f"{money.currency} {sign}{abs(money.amount):,.2f}"
```

#### Review variants

Each variant is applied to the reference file with exact find-and-replace edits. Every `find` must occur
exactly once; otherwise raise an error naming the variant and the edit index. The bug lines, used to score
recall, are every line of the edited file that differs from the reference. B2, for example, changes both
the import and the rounding call.

File: `eval/fixture/variants.toml`
```toml
[[variant]]
id = "B1"
kind = "bug"
ticket = "PRC-4"
file = "pricing/tiers.py"
why = "Tier break no longer inclusive: quantity 10 gets the quantity-1 price."

[[variant.edit]]
find = "            if qty >= min_qty:"
replace = "            if qty > min_qty:"

[[variant]]
id = "B2"
kind = "bug"
ticket = "PRC-3"
file = "pricing/discount.py"
why = "Rounds half-up instead of half-even."

[[variant.edit]]
find = "from decimal import ROUND_HALF_EVEN, Decimal"
replace = "from decimal import ROUND_HALF_UP, Decimal"

[[variant.edit]]
find = "rounding=ROUND_HALF_EVEN"
replace = "rounding=ROUND_HALF_UP"

[[variant]]
id = "B3"
kind = "bug"
ticket = "PRC-1"
file = "pricing/money.py"
why = "Adds amounts across currencies without checking."

[[variant.edit]]
find = '''
        if other.currency != self.currency:
            raise CurrencyMismatch(f"Cannot add {self.currency} and {other.currency}")
'''
replace = ""

[[variant]]
id = "B4"
kind = "bug"
ticket = "PRC-3"
file = "pricing/discount.py"
why = "No floor at zero: discounts above 100% produce negative prices."

[[variant.edit]]
find = "    discounted = max(discounted, Decimal(0))\n"
replace = ""

[[variant]]
id = "B5"
kind = "bug"
ticket = "PRC-2"
file = "pricing/pricelist.py"
why = "Class-level dict shares prices between PriceList instances."

[[variant.edit]]
find = '''
    def __init__(self, items: Iterable[tuple[str, Money]]) -> None:
        self._prices: dict[str, Money] = {}
'''
replace = '''
    _prices: dict[str, Money] = {}

    def __init__(self, items: Iterable[tuple[str, Money]]) -> None:
'''

[[variant]]
id = "B6"
kind = "bug"
ticket = "PRC-5"
file = "pricing/formatting.py"
why = "Negative amounts print a double minus sign."

[[variant.edit]]
find = "{sign}{abs(money.amount):,.2f}"
replace = "{sign}{money.amount:,.2f}"

[[variant]]
id = "C1"
kind = "clean"
ticket = "PRC-4"
file = "pricing/tiers.py"
why = "Rename a local variable."

[[variant.edit]]
find = '''
        price = breaks[0][1]
        for min_qty, tier_price in breaks:
            if qty >= min_qty:
                price = tier_price
        return price
'''
replace = '''
        best = breaks[0][1]
        for min_qty, tier_price in breaks:
            if qty >= min_qty:
                best = tier_price
        return best
'''

[[variant]]
id = "C2"
kind = "clean"
ticket = "PRC-3"
file = "pricing/discount.py"
why = "Extract the zero floor into a helper."

[[variant.edit]]
find = "    discounted = max(discounted, Decimal(0))\n"
replace = "    discounted = _floor_at_zero(discounted)\n"

[[variant.edit]]
find = "HUNDRED = Decimal(100)\n"
replace = '''
HUNDRED = Decimal(100)


def _floor_at_zero(amount: Decimal) -> Decimal:
    return max(amount, Decimal(0))
'''

[[variant]]
id = "C3"
kind = "clean"
ticket = "PRC-2"
file = "pricing/pricelist.py"
why = "Reword an error message; it still contains the SKU."

[[variant.edit]]
find = 'raise UnknownSku(f"No price for SKU {sku}") from None'
replace = 'raise UnknownSku(f"SKU {sku} has no price") from None'

[[variant]]
id = "C4"
kind = "clean"
ticket = "PRC-1"
file = "pricing/money.py"
why = "Add docstrings."

[[variant.edit]]
find = "    def __add__(self, other: \"Money\") -> \"Money\":\n"
replace = "    def __add__(self, other: \"Money\") -> \"Money\":\n        \"\"\"Return the sum of two amounts in the same currency.\"\"\"\n"

[[variant.edit]]
find = "    def __mul__(self, factor: int | Decimal) -> \"Money\":\n"
replace = "    def __mul__(self, factor: int | Decimal) -> \"Money\":\n        \"\"\"Return the amount multiplied by factor.\"\"\"\n"
```

### 7.2 Runs

**`eval --profile P [--stub] [--tickets ...] [--max-usd X]`:**

1. Set up the fixture repository fresh.
2. Run the queue in order through `pipeline.run_ticket`.
3. After each ticket merges, copy `hidden/test_prc_<n>.py` into a scoring worktree of `main`, run it, and
   record pass or fail per hidden test.
4. Run `test_full` on `main` to check for regressions.
5. Stop the run once the run's ledger cost passes `--max-usd` (default `budget.eval_max_usd`).
6. Write `<work_dir>/eval-<profile>-<ts>/report.json` and `report.md`.

**`eval-review --profile P [--stub] [--max-usd X]`** measures review on its own. For each variant:

1. **Base:** the fixture repository plus the reference modules of every ticket ordered before the variant's
   ticket.
2. **Head:** base plus the variant ticket's reference module, with the variant's edits applied. No tests go
   in the diff, so review quality is measured without help from the tests.
3. **Run:** `review.run_review` only, at that profile's settings, with the risk tier forced to `medium`
   for `tiered`.
4. **Score:**
   - A bug counts as **caught** if a blocking finding has the same file and a line within
     `line_tolerance` of any bug line.
   - A **false block** is any blocking finding on a clean variant.

**`report a.json b.json`** prints a side-by-side table with deltas.

#### Report metrics

| Metric | Definition |
|---|---|
| Correctness | tickets whose hidden tests all pass |
| Regressions | tickets after which `test_full` fails on `main` |
| Cost | USD per merged ticket, by stage and by model |
| Haiku share | Haiku tokens over all tokens in readiness, critic and handoff, plus locator calls |
| Review recall | bugs caught / 6 |
| False blocks | clean variants with a blocking finding / 4 |
| Test economy | median valid new tests per criterion; valid / all new tests |
| Mutation | survivors after the fix loop on criterion-covered lines |
| Wall time | per ticket, per stage |
| Escalations | count and reasons |

Proposed targets are in `DESIGN.md` section 12. Agree them with the team before the real runs.

### M5 acceptance

1. Stub run, at no cost:

```bash
python -m harness eval --profile tiered --stub
```

Expected:

- PRC-1 to PRC-5 merged in order, and PRC-6 bounced.
- 22 of 22 hidden tests passing.
- Zero regressions and zero cost.
- `report.md` written.

2. Real runs, in this order. Stop and inspect the ledger after each one.

```bash
python -m harness eval --profile tiered --tickets PRC-1 --max-usd 3
```

```bash
python -m harness eval --profile tiered --max-usd 25
```

```bash
python -m harness eval --profile baseline --max-usd 25
```

```bash
python -m harness eval-review --profile tiered --max-usd 10
```

```bash
python -m harness eval-review --profile baseline --max-usd 10
```

3. Compare the two profiles. Report paths are printed by each run.

```bash
python -m harness report <baseline report.json> <tiered report.json>
```

### 7.3 Replay mode (at work, after the fixture)

`eval --replay <file>`, where the file lists merged MR merge commits, or MR iids once M6 exists. For each
entry:

1. **Base:** the first parent of the merge.
2. **Hidden tests:** the test files changed by the MR.
3. **Ticket:** the Jira description, using the key from the MR title or branch. Fall back to the MR
   description.
4. **Interface hints:** the names of public functions and classes the MR added (from `def` and `class`
   lines in the diff), so that hidden tests can import what the agent builds.
5. **Score:** run the pipeline from the base, then score the result with the hidden tests.

Expect some false failures where hidden tests depend on internal names the agent chose differently.
Report them separately; do not tune the harness to them.

## 8. M6: Jira, GitLab and CI

Build this only after M5 shows the targets are met.

### 8.1 `jira.py`

- **Authentication** (Jira Cloud): basic auth with `JIRA_EMAIL` and `JIRA_API_TOKEN` against
  `JIRA_BASE_URL`.
- **Search:** `POST /rest/api/3/search/jql` with this body:

  ```json
  {
    "jql": "<cfg>",
    "fields": ["summary", "description", "issuelinks", "labels", "status"],
    "maxResults": 50,
    "nextPageToken": "..."
  }
  ```

  - Keep paging while `nextPageToken` is present.
  - A repeated token is a known issue: raise an error naming the token instead of looping.
  - The legacy `/rest/api/3/search` has been removed.
- **Rank** is the position in the results of `ORDER BY Rank ASC`.
- **Blockers.** In issue A's `issuelinks`, an entry with `type.name == <cfg link type, default "Blocks">`
  and an `inwardIssue` means A is blocked by that issue. Verify the direction by recording one real
  issue's JSON as a test fixture.
- **Done:** `fields.status.statusCategory.key == "done"`.
- **Description:** convert the Atlassian Document Format to text by walking the nodes:
  - `text`: its text;
  - `paragraph` and `heading`: a newline;
  - `bulletList` and `orderedList` items: `- `;
  - `hardBreak`: a newline;
  - `codeBlock`: fenced.
- **Bounce comment:** `POST /rest/api/3/issue/{key}/comment` with an ADF body.
- **Data Center:** `/rest/api/2/search` with `startAt` paging; descriptions are wiki markup. Implement this
  only if you need it.

### 8.2 `gitlab.py`

- **Authentication:** `GITLAB_URL`, `GITLAB_TOKEN` (a project access token with `api` scope) and
  `GITLAB_PROJECT_ID`.
- **Create MR:** `POST /api/v4/projects/:id/merge_requests` with `source_branch`, `target_branch`, `title`,
  `description` and `remove_source_branch: true`.
- **Notes:** `POST /api/v4/projects/:id/merge_requests/:iid/notes` with `body`.
- **State:** `GET /api/v4/projects/:id/merge_requests/:iid`, where `state == "merged"` means done.
- **Premium:** add to a merge train with `POST /api/v4/projects/:id/merge_trains/merge_requests/:iid`.
  Set MR dependencies in the UI or through the API. Verify both on your instance before relying on them.
- **Push:** `git push` to a remote URL that carries the token. CI job tokens usually cannot push.

File: `template/ci/gitlab-ci.yml`
```yaml
# Include from the project's .gitlab-ci.yml. Needs CI/CD variables: HARNESS_IMAGE, ANTHROPIC_API_KEY
# (masked) or the Bedrock/Vertex variables, GITLAB_TOKEN, and JIRA_* when tickets come from Jira.
stages:
  - harness-gates
  - harness-review
  - harness-ticket

variables:
  GIT_DEPTH: "0"

.harness:
  image: $HARNESS_IMAGE
  before_script:
    - python -m harness --version

harness-gates:
  extends: .harness
  stage: harness-gates
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - python -m harness gates --base "$CI_MERGE_REQUEST_DIFF_BASE_SHA" --head "$CI_COMMIT_SHA" --report gates.json
  artifacts:
    when: always
    paths:
      - gates.json

harness-review:
  extends: .harness
  stage: harness-review
  needs: [harness-gates]
  # Shadow mode: findings are posted as notes and never fail the pipeline. Remove to start gating.
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - python -m harness review --base "$CI_MERGE_REQUEST_DIFF_BASE_SHA" --head "$CI_COMMIT_SHA" --mr "$CI_MERGE_REQUEST_IID" --post-notes

harness-ticket:
  extends: .harness
  stage: harness-ticket
  rules:
    - if: $HARNESS_TICKET
  script:
    - python -m harness run "$HARNESS_TICKET" --forge gitlab --tickets jira
```

In merge request pipelines, `review` takes the Jira key from the MR title or source branch
(`<key_prefix>-<n>`) and loads the criteria from Jira. Without a key, it uses the MR description as the
ticket text.

### M6 acceptance

1. **Contract tests.** Run against recorded JSON served by `http.server` in a test thread:
   - pagination, including the repeated-token error;
   - ADF to text;
   - blocker direction;
   - the MR create and note request bodies.

```bash
python -m pytest tests/test_jira.py tests/test_gitlab.py -q
```

2. **Read-only dry run against real Jira.** Prints the order and the readiness verdicts; nothing is
   written.

```bash
python -m harness queue --tickets jira
```

3. **Sandbox GitLab project.** Run one fixture ticket end to end with `--forge gitlab`, and check the MR
   description and the notes.

## 9. Rollout

1. **Shadow.** Two weeks or 30 merge requests, whichever comes first. The review job posts non-blocking
   notes on human-written merge requests. Engineers mark each note useful or not, which gives you
   real-code precision.
2. **Assist.** The harness implements low-risk tickets. Humans review as they do today.
3. **Gate.** Proven findings and failing gates block the merge. Human review concentrates on plan approval
   for high-risk tickets.

Move to the next stage only when the targets in `DESIGN.md` section 12 hold on real merge requests.
