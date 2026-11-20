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
7. Run `make check` before declaring the task complete.
8. Report exact commands and their observed results; agent prose is not proof
   that code works.

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
