# Agent delivery harness: design

Status: proposal for local evaluation before team rollout. Researched 2026-11-18.
Companion file: `BUILD_SPEC.md` (what to build, in order, with acceptance checks).

## 1. Goal

Push Jira tickets through GitLab one at a time, in dependency order, so that each merge request is:

- reviewed enough to catch critical bugs,
- free of regressions,
- tested enough, without test bloat,
- cheap enough to run on every ticket.

The current flow: implementation, up to 3 cross-lab adversarial review rounds, a context-free review job in
CI, then human code review. Five problems:

1. Review spend grows with every round, and quality does not grow with it.
2. TDD produces many tests that do not pin any behaviour.
3. Mutation testing is too slow to run on every merge request.
4. Context rots across sessions, even with the per-task indexed wiki.
5. The orchestrator does not reliably hand grunt work to Haiku, whether the rule lives in memory, in
   context or in a hook.

## 2. Diagnosis

| Symptom | Cause | Evidence |
|---|---|---|
| More review rounds, little extra quality | Each round adds opinions, not evidence. Agreement between models is not proof. | Refute-or-Promote: a false positive was endorsed by 80+ agents and killed by one empirical test [R1]. Multi-agent systems use about 15x the tokens of a chat [A3]. |
| Noisy context-free CI review | Removing the codebase also removes what is needed to rule out false positives. What you want from that round is independence from the author, not ignorance of the code. | CodeRabbit field study: 10.3% of false positives came from missing cross-file context (vendor data, via Augment) [V1]. |
| Haiku routing ignored | Three mechanical causes, listed after this table. | Claude Code docs [C1]. |
| TDD runaway | "Write tests first" rewards test count. Nothing checks that a new test actually exercises the change. | SWE-bench defines a valid test as one that fails before the fix and passes after it (FAIL_TO_PASS) [R4]. |
| Mutation testing too slow | Mutating whole files or the whole repo. Most mutants are unproductive. | Google runs mutation testing only on changed lines during code review, with caps per line and per review. Unproductive mutants fell from 85% to 11% [R2]. |
| Context rot, forgotten rules | Long sessions, and memory used to enforce rules. | Anthropic's long-running harness uses fresh sessions, a progress file, a feature list and git [A1]. HumanLayer's research, plan, implement loop starts each phase in a fresh context [P1]. |

### Why the orchestrator does not use Haiku (current Claude Code behaviour)

- **The orchestrator's `model` parameter wins.** The per-call `model` that Claude passes to the Agent tool
  takes precedence over the subagent's frontmatter `model`. A subagent pinned to Haiku runs on Sonnet or
  Opus whenever the orchestrator asks for it [C1].
- **The built-in agents are not cheap.** Explore, Plan and general-purpose run on the parent's model. On a
  subscription or Console, Explore runs on whatever `opus` resolves to [C1].
- **The environment variable does not reach the built-ins.** `CLAUDE_CODE_SUBAGENT_MODEL` alone does not
  change Explore or Plan. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` forces one model on every subagent, which
  is too blunt [C1].
- **Hooks cannot make the model delegate.** A hook can deny a call or add context [C2]. A hook that tries
  to enforce "you should have delegated" keeps blocking, which matches the loop you hit.

## 3. Principles

1. **Mechanisms over instructions.** Anything that must always happen becomes a permission rule, a
   hook, a CI job or driver code. Memory and CLAUDE.md hold facts, not enforcement.
2. **Deterministic control flow, with the model only at the leaves.** A plain program sequences the
   stages and picks the model for each one. Models do judgment work inside a stage. This follows
   12-factor agents ("own your control flow") [P2] and Anthropic's advice to use workflows when the path
   is known [A4].
3. **Fresh context per stage, with files as the interface.** Each stage reads a small input bundle and
   writes an output file with a fixed schema [A1][A2][P1].
4. **Evidence over opinion.** A finding blocks a merge only when it is proven by a failing test or
   survives refutation by another lab. Giving Claude a way to verify its own work is the single biggest
   quality lever, per Boris Cherny [P3].
5. **Spend in proportion to risk.** The risk tier is computed from the diff, not judged by a model, and
   it decides how much review a merge request gets.
6. **Measure before you scale.** Every run writes a cost and outcome ledger. A fixed benchmark compares
   the new flow against today's.

## 4. Architecture

```text
Jira (or local tickets/)
  -> queue: dependency DAG ("blocks" links) + rank -> one ticket at a time
  -> readiness  [haiku]   vague ticket? bounce it with questions, spend nothing else
  -> plan       [sonnet; opus when risk = high]   AC -> named tests map, steps, files
  -> implement  [sonnet]  edits + AC tests; lookups through locator [haiku]
  -> gates      [no LLM]  lint/type, FAIL_TO_PASS, PASS_TO_PASS, test budget,
                          diff mutation (risk >= medium)
  -> review     [sonnet finder -> other-lab refuter -> sonnet prover -> harness runs the proof]
  -> fix loop   (max 2) -> escalate to a human with a summary
  -> handoff    [haiku scribe]  handoff.md + wiki update
  -> MR with an evidence table -> human review -> merge (merge train on Premium)
```

| Stage | Runs as | Model | Input | Output | Stops when |
|---|---|---|---|---|---|
| readiness | `claude -p --agent readiness` | haiku | ticket text, blocker status | `readiness.json` | schema output, or 3 turns |
| plan | `claude -p --agent planner` | sonnet (opus if high risk) | ticket, readiness, locator results | `plan.json`, `plan.md` | budget or turn cap |
| implement | `claude -p --agent implementer` | sonnet | plan, handoff | code, `implement.json` | budget or turn cap |
| gates | driver | none | diff, test commands | `gates.json` | deterministic |
| test critic | `claude -p --agent test-critic` | haiku | gate flags, AC map | edited tests | only when over budget or useless tests are flagged |
| find | `claude -p --agent reviewer` | sonnet | AC + diff only (author-blind) | `findings.json` | schema output |
| refute | `$REFUTER_CMD` (Codex or Gemini) | other lab | finding + code excerpts | `refutations.json` | schema output |
| prove | `claude -p --agent prover` | sonnet | one surviving finding | failing test id | the harness runs it |
| handoff | `claude -p --agent scribe` | haiku | stage JSON outputs | `handoff.md` | 60 lines or fewer |

Every `claude -p` call carries `--model`, `--max-turns`, `--max-budget-usd` and
`--output-format json`, plus `--json-schema` where the stage has an output schema [C3]. The driver reads
`total_cost_usd` and `modelUsage` from the result and appends them to the ledger. M0 of the build spec
confirms these result keys on your CLI version.

## 5. Model routing

| Agent | Model | Tools | Why |
|---|---|---|---|
| orchestrator (interactive only) | sonnet | `Agent(locator, test-runner, scribe, implementer, reviewer)`, `Read` | It cannot search or run commands itself, so it has to delegate |
| locator | haiku | Read, Grep, Glob, Bash (read-only use) | Lookups with checkable output. `NOT FOUND` must list the queries it ran |
| test-runner | haiku | Read, Bash | Runs commands and summarises failures |
| scribe | haiku | Read, Write, Edit | Writes the handoff from structured input |
| readiness | haiku | Read, Agent(locator) | Classification with a schema |
| test-critic | haiku | Read, Edit, Bash | Removes flagged tests. Gates re-check the result |
| planner | sonnet, opus when risk = high | Agent(locator), Read, Grep, Glob | The only stage where more reasoning pays off upstream |
| implementer | sonnet | Agent(locator, test-runner), Read, Edit, Write, Bash, Grep, Glob | Bulk work |
| reviewer (finder) | sonnet | Agent(locator), Read, Grep, Glob | Author-blind |
| prover | sonnet | Read, Write, Edit, Bash | Writes one failing test per finding |

How routing is enforced:

- **Pipeline mode (the default).** The driver passes `--agent` and `--model` on every call. No model ever
  chooses a model.
- **Interactive mode** (`claude --agent orchestrator`) uses four mechanisms:
  1. **Capability.** The orchestrator's `tools` allowlist names only worker agents and Read. A `tools`
     allowlist with `Agent(x, y)` applies to the main thread started with `--agent` [C1].
  2. **Pinning.** Each worker's frontmatter `model` is fixed.
  3. **Guard hook.** A PreToolUse hook on the Agent tool denies two objective cases, an unknown subagent
     type and a `model` argument that differs from the agent's pin. The deny message states the exact
     call to retry. Pins are read from `.claude/agents/*.md`, so they live in one place.
  4. **Removing the expensive defaults.** Set `permissions.deny: ["Agent(general-purpose)"]` and
     `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1` [C1]. According to the issue tracker, `Agent(type)` deny
     rules need Claude Code 2.1.186 or later. M0 verifies this.
- **Lookups that a tool can answer do not go to a model.** ripgrep, `git log -S`, ast-grep and your wiki
  index cost no tokens and have no silent false negatives. Haiku retrieval can miss things silently [V2].
  The locator therefore has to show its queries when it finds nothing.

## 6. Context and memory

- **One ticket, one folder:** `.harness/tickets/<KEY>/` holds `readiness.json`, `plan.json`/`plan.md`,
  `implement.json`, `gates.json`, `findings.json`, `handoff.md` and `state.json`. Any stage can resume from
  these files in a fresh session.
- **The handoff file is the progress file** [A1]. It has fixed headers (Status, Done, Decisions with the
  reason, Open questions, Next step, Gotchas) and at most 60 lines. The Haiku scribe overwrites it from
  stage JSON, never from a transcript.
- **SessionStart hook** with matcher `startup|resume|compact`. It re-injects the active ticket's handoff and
  a three-line routing reminder at session start and after every compaction [C2]. This is the mechanical
  fix for rules that fade as the context fills up.
- **Your indexed wiki stays.** It plugs in through two commands in `harness.toml`: `wiki.search_cmd`, which
  the locator calls through `.harness/wiki_search`, and `wiki.update_cmd`, which the driver calls after the
  handoff stage. Retrieval is just-in-time, not preloaded [A2].
- **Stop hook.** In interactive mode it blocks a stop once if source files changed after the handoff was
  last written. It uses `stop_hook_active` so it cannot loop, and it is skipped in pipeline mode.

## 7. Testing policy (replaces "TDD everywhere")

1. **The plan maps each acceptance criterion to named tests:** at least one per criterion, at most `k`
   (default 3). Tests outside the map need a stated reason in `implement.json`.
2. **FAIL_TO_PASS gate.** Every new test must fail on the base commit and pass on head. The test files are
   copied onto a `git worktree` of the base, the same method SWE-bench uses [R4]. A new test that already
   passes on base does not test the change, so it is flagged for deletion.
3. **AC coverage gate.** Every criterion has at least one valid FAIL_TO_PASS test.
4. **PASS_TO_PASS gate.** The affected existing tests must still pass. The full suite runs before merge
   (or in the merge train).
5. **Test budget.** When the count goes over `k` per criterion, or tests are flagged, the Haiku test critic
   prunes against Kent Beck's Test Desiderata (behavioural, structure-insensitive, specific,
   deterministic) [P4]. The gates then run again.
6. **Edits to existing tests raise the risk tier.** Each one is listed with its reason in the MR.

## 8. Mutation testing, the Google way

- Mutate only the changed lines (from `git diff -U0`), at most 1 mutant per line and N per merge request,
  within a time box, and only when risk is medium or higher [R2].
- Operators are tried in a fixed order of usefulness: comparison boundary, boolean negation, arithmetic
  swap, constant change, return value.
- A surviving mutant is evidence, not a failure. It goes to the reviewer and becomes a targeted
  "kill this survivor" task for the implementer. Meta's ACH works the same way, generating tests aimed at
  specific mutants instead of chasing coverage: 73% of its tests were accepted, and 277 of 571 would have
  been discarded under a coverage criterion [R3].
- Adapters:
  - a stdlib `ast` mini-mutator for Python, used by the benchmark fixture;
  - StrykerJS with `--mutate file:5-7 --incremental` [T1];
  - cargo-mutants with `--in-diff` (not verified this session);
  - PIT for the JVM (adapter left to M3 if you need it).

## 9. Review protocol

**Risk tier**, computed by the driver:

- high: path globs (auth, payments, migrations, infra), edits to existing tests, a large diff, or the
  `risk:high` label;
- medium: API path globs or a medium-sized diff;
- low: anything else.

| Tier | Deterministic gates | Finder | Refuter (other lab) | Prover | Mutation | Human |
|---|---|---|---|---|---|---|
| low | all | 1 Sonnet pass | no | critical findings only | no | normal review |
| medium | all | 1 Sonnet pass | yes | for high and critical findings | yes | normal review |
| high | all | Sonnet + other-lab finder | each lab refutes the other | for high and critical findings | yes | plan approval before implement, plus review |

Rules:

- **Gates run first.** No LLM spends tokens on what lint, types or tests already catch.
- **Finder.** Every finding must point to a line in the diff and state a concrete failure (input or state
  leading to a wrong output or crash), with a confidence from 0 to 100. Style comments are not findings.
  Anthropic's code-review plugin filters findings below a confidence of 80 [A5].
- **Refuter.** It tries to disprove each finding. It sees the finding and the relevant code, but not the
  finder's reasoning chain [R1].
- **Prover.** For each surviving high or critical finding, it writes the smallest failing test it can, in a
  scratch worktree. The harness runs that test. If it fails on head, the finding is proven, it blocks the
  merge, and the test is kept.
- **Unproven findings.** Survivors that cannot be tested (configuration, security posture) block only when
  confidence is at least 80 and the refuter agrees. They are labelled "unproven" for the human reviewer.
  Everything else becomes a non-blocking MR note.
- **Fix loop.** At most 2 iterations. After that the merge request becomes a draft, with an escalation
  summary.
- **The context-free CI review becomes author-blind.** It gets the ticket's criteria, the diff and nearby
  code through the locator. It never gets the plan, the transcript or the implementer's notes. That keeps
  the independence you wanted without the false positives that come from missing code.
- **The MR description is generated:**
  - a criterion-to-test table, with each test's FAIL_TO_PASS status;
  - gate results;
  - risk tier and the reasons for it;
  - findings, split into proven, refuted and notes;
  - mutation survivors;
  - cost and time.

  The human reviewer reads evidence, not a wall of comments.

## 10. Ticket order and GitLab

- **Order.**
  - The queue is a topological sort over Jira "Blocks" links, with rank breaking ties. A cycle is an error
    that names the cycle.
  - Blocked tickets wait until their blockers are Done.
  - Ticket text comes from the Jira Cloud endpoint `POST /rest/api/3/search/jql`, paged with
    `nextPageToken` [T2].
- **Readiness gate.** Every acceptance criterion has to be observable (an input and a checkable result),
  the scope has to be bounded, and the blockers have to be done. If not, the ticket gets a Jira comment with
  questions, and no implementation tokens are spent. Atlassian's guidance on writing tickets for agents
  supports this [V3]. Keep tickets small: spec-driven tools turn large specs into review burden [P5].
- **GitLab Premium or Ultimate.** MR dependencies block a dependent merge request until its dependencies
  merge. Merge trains test each merge request against the ones ahead of it [T3].
- **GitLab Free.** The driver serialises the work: one open MR at a time, and the full suite on the
  rebased branch before merge.
- **CI.** Claude Code's GitLab CI/CD integration is in beta and maintained by GitLab. It supports an API
  key, Bedrock through OIDC, and Vertex through workload identity [C4]. The harness only needs `claude -p`
  inside your image.

## 11. Budget controls

- A per-stage `--max-turns` and `--max-budget-usd` (subagent spend counts toward it [C3]).
- A per-ticket ceiling (`budget.ticket_max_usd`). Going over it escalates instead of retrying.
- A ledger (JSONL) with cost, time, turns and per-model usage for each stage. This is the data you show the
  team.
- Stable system prompts (agent files) come first and variable content last, so prompt caching applies
  across tickets.
- Opus is used only to plan high-risk tickets. Another lab is used only to refute or find, at medium risk
  and above.

## 12. Measuring success (before the team sees it)

**Benchmark (ships in the kit):** a small pricing library fixture.

- 6 tickets. PRC-1 blocks PRC-2, PRC-3 and PRC-5. PRC-4 needs PRC-2 and PRC-3. PRC-6 is deliberately
  vague, to exercise the readiness gate.
- Hidden acceptance tests that agents never see.
- 6 seeded-bug variants and 4 clean refactor variants of the reference solution, to measure review recall
  and false blocks.

**Replay mode (at work):** take N merged merge requests that changed tests. Start from the parent commit,
use the Jira description as the ticket, hide the merge request's own test changes, run the pipeline, then
score with the hidden tests.

**Profiles:**

- `baseline`: your current flow, approximated as an implementer told to do TDD, 3 alternating-lab
  adversarial rounds plus 1 context-free round, with every finding blocking.
- `tiered`: this design.

| Metric | Definition | Proposed target (agree with the team first) |
|---|---|---|
| Correctness | tickets whose hidden tests all pass / tickets | tiered >= baseline; 5/5 on the fixture |
| Regressions | tickets that broke the existing suite after merge | 0 |
| Cost per merged ticket | sum of `total_cost_usd` over stages | tiered at least 30% below baseline |
| Haiku share | Haiku tokens / all tokens in readiness, locate, scribe and critic | 100% in pipeline mode; at least 90% of lookup subagent tokens in interactive mode |
| Review recall | seeded bugs caught by a blocking finding within 3 lines | at least 5/6 |
| False blocks | blocking findings on clean variants | 0/4 on the fixture; at most 1 per 10 merge requests in replay |
| Test economy | median new tests per criterion; FAIL_TO_PASS ratio of new tests | at most 2; at least 0.8 |
| Mutation survivors | survivors on changed lines after the fix loop (medium risk and up) | reported; 0 on lines covered by a criterion |
| Wall time | per ticket, per stage | tiered <= baseline |
| Escalations | tickets handed to a human | reported, with the reason |

**Rollout after the local results:**

1. **Shadow.** The review job posts non-blocking notes on human-written merge requests. Measure precision
   on real code.
2. **Assist.** The harness implements low-risk tickets.
3. **Gate.** Proven findings and gates block merges.

Move to the next stage only when the targets hold.

## 13. Audit your current harness first

These failure modes make rules "get ignored". This repository has the first two, which suggests your work
setup may have them as well:

- [ ] **Skills in the wrong place.** Skills must live at `.claude/skills/<name>/SKILL.md`. Flat files such
  as `.claude/review` are never loaded.
- [ ] **Hook matchers that never match.** Matchers match tool names (`Write|Edit`), not `Write(*.ts)`. Hook
  input arrives as JSON on stdin; there is no `$file` variable [C2].
- [ ] **Hooks that loop.** Exit code 2 blocks and feeds stderr to the model. A Stop hook without a
  `stop_hook_active` check can loop.
- [ ] **Missing loads.** Run `/agents`, `/hooks`, `/context` and `/memory` in a session to see what actually
  loaded and what fills the context.
- [ ] **Old CLI version.** `claude --version` must be at least 2.1.186 for `Agent(type)` deny rules.
- [ ] **Expensive built-ins.** Check whether Explore and general-purpose are running on Opus. They inherit
  the parent's model [C1].

## 14. What not to do

- Do not add review rounds. Add evidence (a failing test, a refutation) to fewer rounds.
- Do not treat agreement between models or labs as proof.
- Do not run mutation testing on unchanged code or on the whole repository.
- Do not use memory or CLAUDE.md text for rules that must hold. Use permissions, hooks or driver code.
- Do not write hooks that try to force delegation. Constrain capabilities instead.
- Do not send lookups to an LLM when ripgrep, git or the wiki index can answer them.
- Do not run whole tickets inside one long session. Use one fresh session per stage, with files between
  stages.

## 15. Not verified (to check in M0 and M6)

- **Live behaviour.** The `claude -p` result keys (`total_cost_usd`, `modelUsage`, `structured_output`)
  and the `--json-schema` argument form, on your CLI version.
- **Version-dependent rules.** `Agent(general-purpose)` deny and `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS`
  on your CLI version.
- **Other tools:**
  - cargo-mutants `--in-diff`;
  - whether Gemini CLI reads `AGENTS.md`;
  - the GitLab merge-train and MR-dependency API calls;
  - Jira "Blocks" link direction on your instance (record one issue's JSON as a test fixture);
  - Jira Data Center differences: it uses `/rest/api/2/search` and wiki-markup descriptions.

## 16. People and projects worth following

- **Boris Cherny** (@bcherny), creator of Claude Code: verification loops, Stop hooks for deterministic
  checks [P3].
- **Dex Horthy** (@dexhorthy), HumanLayer: context engineering; the research, plan, implement loop;
  12-factor agents [P1][P2].
- **Simon Willison** (@simonw): practical, evidence-based notes on agentic coding.
- **Geoffrey Huntley** (@GeoffreyHuntley): the "Ralph" loop, i.e. small repeated fresh-context iterations.
- **Kent Beck** (@KentBeck): Test Desiderata; augmented coding, and how agents game tests.
- **Birgitta Böckeler**, Thoughtworks / martinfowler.com: a sceptical comparison of spec-driven
  development tools [P5].
- **Repositories:**
  - `humanlayer/12-factor-agents`;
  - `obra/superpowers` (its plan and subagent-per-task skills are useful; replace its strict TDD skill
    with sections 7 and 8 here);
  - `github/spec-kit`;
  - `anthropics/claude-code` (`plugins/code-review`);
  - `SWE-bench/SWE-bench`;
  - `stryker-mutator/stryker-js`.

## 17. Sources

Retrieved during this research unless marked "(not re-fetched)".

- [C1] Claude Code, Subagents: https://code.claude.com/docs/en/sub-agents
- [C2] Claude Code, Hooks: https://code.claude.com/docs/en/hooks
- [C3] Claude Code, CLI reference: https://code.claude.com/docs/en/cli-reference (also model configuration: https://code.claude.com/docs/en/model-config)
- [C4] Claude Code, GitLab CI/CD: https://code.claude.com/docs/en/gitlab-ci-cd
- [A1] Anthropic, Effective harnesses for long-running agents: https://anthropic.com/engineering/effective-harnesses-for-long-running-agents
- [A2] Anthropic, Effective context engineering for AI agents: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents (not re-fetched)
- [A3] Anthropic, How we built our multi-agent research system: https://www.anthropic.com/engineering/multi-agent-research-system (not re-fetched)
- [A4] Anthropic, Building effective agents: https://www.anthropic.com/engineering/building-effective-agents (not re-fetched)
- [A5] Anthropic code-review plugin: https://claude.com/plugins/code-review
- [P1] HumanLayer, Advanced Context Engineering for Coding Agents: https://humanlayer.dev/blog/advanced-context-engineering
- [P2] HumanLayer, 12-factor agents: https://github.com/humanlayer/12-factor-agents (not re-fetched)
- [P3] InfoQ, How the creator of Claude Code uses it (Jan 2026): https://www.infoq.com/news/2026/01/claude-code-creator-workflow
- [P4] Kent Beck, Test Desiderata: https://testdesiderata.com (not re-fetched)
- [P5] Birgitta Böckeler, Understanding spec-driven development: Kiro, spec-kit and Tessl (martinfowler.com, 2025) (not re-fetched)
- [R1] Refute-or-Promote: adversarial stage-gated multi-agent review (arXiv 2604.19049): https://arxiv.org/abs/2604.19049
- [R2] Petrović, Ivanković, Fraser, Just, Practical Mutation Testing at Scale: A view from Google (TSE 2021): https://arxiv.org/abs/2102.11378
- [R3] Harman et al., Mutation-Guided LLM-based Test Generation at Meta (FSE 2025): https://arxiv.org/abs/2501.12862
- [R4] Jimenez et al., SWE-bench (ICLR 2024): https://www.swebench.com (not re-fetched)
- [T1] StrykerJS incremental mode: https://stryker-mutator.io/docs/stryker-js/incremental/
- [T2] Atlassian, Run JQL search query using Jira Cloud REST API: https://confluence.atlassian.com/jirakb/run-jql-search-query-using-jira-cloud-rest-api-1289424308.html
- [T3] GitLab merge trains: https://docs.gitlab.com/ci/pipelines/merge_trains/ and MR dependencies: https://docs.gitlab.com/user/project/merge_requests/dependencies
- [V1] Augment Code, AI code review accuracy (cites the CodeRabbit study; vendor source): https://www.augmentcode.com/guides/ai-code-review-accuracy
- [V2] Community gist on Haiku retrieval false negatives (anecdotal): https://gist.github.com/christophermark/da8972564a630ae4583c5d54c481fe3c
- [V3] Atlassian, Writing tickets for AI agents: https://www.atlassian.com/blog/jira/writing-tickets-for-ai-agents
