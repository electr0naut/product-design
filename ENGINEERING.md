# Engineering Standards

## Purpose

This repository is a reusable product-design pipeline. It must remain small enough for personal use and rigorous enough to hand to a future team.

## Sources of truth

- Product intent lives in the phase documents.
- Behaviour-changing code needs a short spec in `docs/specs/` before implementation.
- Tests are the executable contract for parser, validator, path-handling and generation behaviour.
- Generated documents are drafts until a human explicitly reviews them.
- Markdown and model output are untrusted input, not program control.

## Change rules

- Every bug fix adds a regression test.
- Every change to a public CLI documents success/failure behaviour and exit status.
- Parsers, validators and file-writing paths fail closed: invalid input must not silently produce partial output or overwrite reviewed artefacts.
- Generated model output must be fully validated before it changes files.
- Preserve product traceability: stable BR/NFR, epic and story identifiers must not be silently rewritten.
- Keep changes focused. Do not mix generated project artefacts with unrelated tooling or source changes.

## Required checks

Run these before committing a Python or frontend change:

```bash
make check
```

The command runs Python linting, type checking and tests, followed by frontend linting and the production build.

## Testing policy

- Use test-first development for parsing, validation, filesystem safety and CLI behaviour.
- Use focused regression tests for bugs, then run the full suite.
- Add golden fixtures for realistic generated Markdown.
- Add property tests when a parser gains meaningful input surface area.
- Run mutation tests periodically on critical validation modules; mutation score is diagnostic, not a release target.

## Specification template

Create a concise spec for behaviour-changing work under `docs/specs/` using `docs/specs/TEMPLATE.md`. It must state the problem, non-goals, invariants, acceptance criteria and tests. Do not create specifications for copy-only or mechanical formatting changes.

## Review and automation

- CI must be green before merge.
- A change authored by an AI agent requires an independent review against its spec and command output proving verification.
- Never claim completion from agent prose alone.
