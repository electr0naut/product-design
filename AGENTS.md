# Agent Instructions

Read this file before changing the repository. `ENGINEERING.md` is the canonical
engineering policy; this file is the short operational version intended for any
coding model or agent that clones the repository.

## Required workflow

1. Read the relevant product documents, source files and tests before editing.
2. For every behaviour-changing change, create or update a concise spec in
   `docs/specs/` using `docs/specs/TEMPLATE.md`.
3. For bug fixes and core pipeline logic, write a failing regression test first.
4. Treat Markdown, CLI input and model output as untrusted input. Validate it
   before deleting, overwriting or creating artefacts.
5. Keep stable IDs (`BR-xxx`, `NFR-xxx`, `E01`, `US-001`) intact unless the
   corresponding spec explicitly permits a migration.
6. Do not overwrite reviewed product documents or unrelated user changes.
7. When `review/<product>.json` exists, treat it as the gate contract: do not
   edit a reviewed artifact, mark a decision approved, resolve feedback, or
   record a change on a stakeholder's behalf. Record only decisions you were
   given, with the exact artifact hashes and evidence reference.
8. Review pages under `/review` are unauthenticated and loopback-only. Never add
   a write endpoint or weaken the Host check without an authentication design.
9. Run `make check` before declaring the task complete.
10. Report exact commands and their observed results; agent prose is not proof
   that code works.

## Commit, review and inbox rules

1. **Model trailer.** End every commit message with `Model: <model name>`. If
   the model changes mid-task, discard the partial work and restart from the
   last green commit; the next commit names the new model.
2. **Independent review before self-merge.** CodeRabbit reviews every PR. Wait
   for its review, then fix or answer every comment in the PR thread. Never
   merge with an unanswered comment, never dismiss a review, and never edit
   branch protection. If no review arrives within 30 minutes, do not merge:
   note it in `docs/plans/STATUS.md` and move on.
3. **Inbox.** `docs/plans/INBOX.md` holds queued requests. Read it only between
   tasks, never mid-task. When an item is handled, move it to the "Done"
   section of `docs/plans/STATUS.md` with the commit that handled it.
4. **Explain merges plainly.** For every merged PR, `docs/plans/STATUS.md`
   carries two plain-English sentences a non-developer can follow: what
   changed, and what could break.

## Repository conventions

- Python pipeline code is in `shared/scripts/`; use Python 3.11 tooling via
  `uv` and configuration in `pyproject.toml`.
- The Next.js overview lives in `src/app/`; retain TypeScript strictness.
- Preserve the clone-per-product workflow and document traceability.
- Use focused commits; do not mix generated product artefacts with unrelated
  source/tooling changes.

<!-- BEGIN:nextjs-agent-rules -->
## Next.js rule

This version has breaking changes — APIs, conventions, and file structure may
differ from your training data. Read the relevant guide in
`node_modules/next/dist/docs/` before writing any code. Heed deprecation
notices.
<!-- END:nextjs-agent-rules -->
