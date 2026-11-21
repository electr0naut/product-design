# Pipeline Integrity Hardening Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make the document pipeline fail closed on malformed story output, prevent accidental cross-product context and prompt overwrites, harden repository-path handling, and align the public contract with actual implementation-plan output.

**Architecture:** Keep the standard-library Python CLI architecture. Add narrow reusable helpers in `workflow_common.py` for safe repository-relative path resolution and protected writes; use exact phase-02 artifact names rather than generic product-prefix matching. Validate a complete story response before any deletion or write. Retain exploratory draft workflows, but document phase gates as human review rather than machine-enforced approval.

**Tech Stack:** Python standard library, `unittest`, Markdown templates/prompts, Next.js/TypeScript static overview.

---

### Task 1: Add failing safety and overwrite tests

**Objective:** Specify expected non-destructive behaviour before implementation.

**Files:**
- Modify: `shared/scripts/tests/test_backlog.py`

**Steps:**
1. Add tests proving prompt-only generation preserves an existing prompt absent `--force`.
2. Add tests proving BRD source discovery only includes exact role artifacts for the selected slug and excludes a prefix-neighbour product.
3. Add tests proving symlinked discovered inputs and symlinked output targets are rejected.
4. Run `python -m unittest discover shared/scripts/tests` and confirm failures.

### Task 2: Harden common file and analysis helpers

**Objective:** Eliminate accidental overwrite and unsafe symlink/path traversal for repository-managed artefacts.

**Files:**
- Modify: `shared/scripts/workflow_common.py`
- Modify: `shared/scripts/generate_brd.py`
- Modify: `shared/scripts/tests/test_backlog.py`

**Steps:**
1. Add safe read/write checks rejecting symlinked discovered inputs and symlinked managed outputs.
2. Move `generate()` existence protection ahead of prompt-only writes.
3. Replace generic product-prefix selection with exact expected analysis role filenames.
4. Update BRD generation to use exact role analysis selection.
5. Run the focused tests, then the full suite.

### Task 3: Make story import transactional and fail closed

**Objective:** Prevent incomplete or contradictory Claude output from creating a superficially successful but invalid backlog.

**Files:**
- Modify: `shared/scripts/generate_stories.py`
- Modify: `shared/scripts/tests/test_backlog.py`

**Steps:**
1. Add failing tests for unknown story IDs, duplicate markers, missing expected IDs, mismatched frontmatter IDs, and mismatched epics.
2. Parse and validate all response chunks before deleting or writing a file.
3. Reject any invalid response with nonzero exit and retain pre-existing story files.
4. Write only after validation passes; preserve `--force` semantics for valid complete output.
5. Run focused tests and the full suite.

### Task 4: Align product documentation, prompt, and overview UI

**Objective:** Remove claims the code does not meet and make draft-mode workflow behaviour explicit.

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `shared/prompts/07-scaffold-code.md`
- Modify: `shared/scripts/scaffold_code.py`
- Modify: `src/app/page.tsx`

**Steps:**
1. Recast phase 07 as implementation-plan generation rather than a runnable code scaffold.
2. State that phase gates are human review checklists; scripts support iterative draft workflows and do not cryptographically enforce approval.
3. Label the Next.js page as a static workflow overview, not a workflow browser.
4. Run `npm run lint`, `npm run build`, and Python tests.

### Task 5: Review and commit

**Objective:** Verify the implementation matches this plan without including the user’s pre-existing `.gitignore` change.

**Files:**
- Review all changed files.

**Steps:**
1. Inspect `git diff --check` and staged file list.
2. Run `python -m unittest discover shared/scripts/tests`, `npm run lint`, and `npm run build`.
3. Perform an independent spec/quality review.
4. Commit only intended files with a conventional commit; leave `.gitignore` unstaged.
