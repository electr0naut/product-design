"""The implementation phase must consume exactly the validated backlog."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

STORY = """---
id: {sid}
title: {title}
epic: {epic}
traces_to: [{requirement}]
depends_on: []
components: []
priority: Must
estimate: M
status: Draft
---

# {sid}: {title}

**As a** user, **I want** {title}, **so that** the product works.

## Acceptance Criteria
- [ ] Given a user, when they act, then it works

## Tasks
- [ ] Implement {sid}
"""


def fixture(root: Path) -> tuple[Path, Path, Path]:
    (root / "review").mkdir()
    (root / "03-brd").mkdir()
    (root / "04-prd").mkdir()
    (root / "05-technical-design").mkdir()
    backlog = root / "06-backlog" / "demo"
    (backlog / "E01-accounts").mkdir(parents=True)
    (backlog / "E02-billing").mkdir()
    brd = root / "03-brd" / "demo-brd.md"
    brd.write_text(
        "| ID | Requirement |\n|----|-------------|\n| BR-001 | Accounts |\n| BR-002 | Billing |\n",
        encoding="utf-8",
    )
    prd = root / "04-prd" / "demo-prd.md"
    prd.write_text(
        "### E01: Accounts\n| ID | Story | Persona | Traces to | Priority |\n"
        "|----|-------|---------|-----------|----------|\n"
        "| US-001 | Create account | User | BR-001 | Must |\n\n"
        "### E02: Billing\n| ID | Story | Persona | Traces to | Priority |\n"
        "|----|-------|---------|-----------|----------|\n"
        "| US-002 | Pay bill | User | BR-002 | Must |\n",
        encoding="utf-8",
    )
    design = root / "05-technical-design" / "demo-technical-design.md"
    design.write_text("# Design\n\nShared architecture.\n", encoding="utf-8")
    (backlog / "E01-accounts" / "US-001-account.md").write_text(
        STORY.format(sid="US-001", title="Create account", epic="E01", requirement="BR-001"),
        encoding="utf-8",
    )
    (backlog / "E02-billing" / "US-002-bill.md").write_text(
        STORY.format(sid="US-002", title="Pay bill", epic="E02", requirement="BR-002"),
        encoding="utf-8",
    )
    return brd, prd, design


def validate(root: Path, brd: Path, prd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "validate_backlog.py"),
            "--brd",
            str(brd),
            "--prd",
            str(prd),
            "--backlog",
            str(root / "06-backlog" / "demo"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def manifest(root: Path, design: Path, *, approved: bool) -> Path:
    backlog = root / "06-backlog" / "demo"
    lock = backlog / "backlog.lock.json"
    stories = {
        "E01": backlog / "E01-accounts" / "US-001-account.md",
        "E02": backlog / "E02-billing" / "US-002-bill.md",
    }
    lanes = {
        "E01": {
            "roles": ["product", "engineering"],
            "artifacts": [stories["E01"].relative_to(root).as_posix()],
            "depends_on": [],
            "assumptions": [],
            "epic": True,
        },
        "E02": {
            "roles": ["product", "engineering"],
            "artifacts": [stories["E02"].relative_to(root).as_posix()],
            "depends_on": [],
            "assumptions": [],
            "epic": True,
        },
        "baseline": {
            "roles": ["engineering"],
            "artifacts": [
                design.relative_to(root).as_posix(),
                lock.relative_to(root).as_posix(),
            ],
            "depends_on": [],
            "assumptions": [],
        },
    }
    doc = {
        "schema_version": 2,
        "product": "demo",
        "gates": [{"id": "backlog-to-implementation", "lanes": lanes}],
        "decisions": [],
        "feedback_events": [],
        "changes": [],
        "change_events": [],
        "assumptions": [],
        "questions": [],
        "question_answers": [],
    }
    if approved:
        for lane, roles in (
            ("E01", ("product", "engineering")),
            ("E02", ("product", "engineering")),
            ("baseline", ("engineering",)),
        ):
            hashes = {
                path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                for path in lanes[lane]["artifacts"]
            }
            for role in roles:
                doc["decisions"].append(
                    {
                        "id": f"D-{len(doc['decisions']) + 1:03d}",
                        "gate": "backlog-to-implementation",
                        "lane": lane,
                        "role": role,
                        "reviewer": role,
                        "decision": "approve",
                        "recorded_at": "2026-11-21T12:00:00Z",
                        "artifact_sha256": hashes,
                        "evidence": "review-ticket-1",
                        "feedback": [],
                    }
                )
    path = root / "review" / "demo.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path


def scaffold(
    root: Path, design: Path, manifest_path: Path, *extra: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "scaffold_code.py"),
            "--technical-design",
            str(design),
            "--backlog",
            str(root / "06-backlog" / "demo"),
            "--out",
            str(root / "07-implementation" / "plan.md"),
            "--prompt-only",
            "--review-manifest",
            str(manifest_path),
            *extra,
        ],
        text=True,
        capture_output=True,
        check=False,
    )


def test_validation_writes_a_lock_and_the_gate_allows_the_plan():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        validated = validate(root, brd, prd)
        assert validated.returncode == 0, validated.stderr
        lock = json.loads((root / "06-backlog" / "demo" / "backlog.lock.json").read_text())
        assert lock["product"] == "demo"
        assert len(lock["stories"]) == 2
        result = scaffold(root, design, manifest(root, design, approved=True))
        assert result.returncode == 0, result.stderr
        prompt = root / "07-implementation" / "plan.prompt.md"
        assert prompt.exists()
        text = prompt.read_text()
        assert "Shared architecture." in text
        assert "US-001" in text and "US-002" in text


def test_editing_a_story_after_validation_blocks_the_plan():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        assert validate(root, brd, prd).returncode == 0
        story = root / "06-backlog" / "demo" / "E01-accounts" / "US-001-account.md"
        story.write_text(story.read_text() + "\nEdited after validation.\n", encoding="utf-8")
        result = scaffold(root, design, manifest(root, design, approved=True))
        assert result.returncode != 0
        assert "changed since validation" in result.stderr
        assert not (root / "07-implementation" / "plan.prompt.md").exists()


def test_unapproved_backlog_blocks_but_draft_is_explicit():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        assert validate(root, brd, prd).returncode == 0
        path = manifest(root, design, approved=False)
        blocked = scaffold(root, design, path)
        assert blocked.returncode != 0
        assert not (root / "07-implementation" / "plan.prompt.md").exists()
        draft = scaffold(root, design, path, "--draft")
        assert draft.returncode == 0, draft.stderr
        assert "DRAFT ONLY" in draft.stderr
        assert (root / "07-implementation" / "plan.prompt.md").exists()


def test_failed_validation_removes_the_previous_lock_and_scaffold_refuses():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        assert validate(root, brd, prd).returncode == 0
        lock = root / "06-backlog" / "demo" / "backlog.lock.json"
        assert lock.exists()
        (root / "06-backlog" / "demo" / "US-003-orphan.md").write_text(
            STORY.format(sid="US-003", title="Orphan", epic="E01", requirement="BR-999"),
            encoding="utf-8",
        )
        failed = validate(root, brd, prd)
        assert failed.returncode != 0
        assert not lock.exists()
        result = scaffold(root, design, manifest(root, design, approved=False))
        assert result.returncode != 0
        assert "validate_backlog" in result.stderr


def test_revalidation_without_changes_keeps_the_lock_bytes_and_approval():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        assert validate(root, brd, prd).returncode == 0
        lock = root / "06-backlog" / "demo" / "backlog.lock.json"
        before = lock.read_bytes()
        assert validate(root, brd, prd).returncode == 0
        assert lock.read_bytes() == before
        result = scaffold(root, design, manifest(root, design, approved=True))
        assert result.returncode == 0, result.stderr


def test_story_added_after_the_lock_is_refused():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        brd, prd, design = fixture(root)
        assert validate(root, brd, prd).returncode == 0
        (root / "06-backlog" / "demo" / "US-003-extra.md").write_text(
            STORY.format(sid="US-003", title="Extra", epic="E01", requirement="BR-001"),
            encoding="utf-8",
        )
        result = scaffold(root, design, manifest(root, design, approved=False))
        assert result.returncode != 0
        assert "does not cover the current story files" in result.stderr
