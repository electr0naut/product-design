"""Split PRDs: epic-scoped generation and real per-epic invalidation."""

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

PRD = """# Demo PRD

## Overview
Shared context that every epic reads.

### E01: Accounts
| ID | Story | Persona | Traces to | Priority |
|----|-------|---------|-----------|----------|
| US-001 | Create account | User | BR-001 | Must |

### E02: Billing
| ID | Story | Persona | Traces to | Priority |
|----|-------|---------|-----------|----------|
| US-002 | Pay bill | User | BR-002 | Must |

## Release Plan
| Phase | Date |
|-------|------|
| MVP   |      |

## Open Questions
- Which market?
"""


def split(root: Path) -> Path:
    source = root / "04-prd" / "demo-prd.md"
    source.parent.mkdir(parents=True)
    source.write_text(PRD, encoding="utf-8")
    out = root / "04-prd" / "demo"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "split_prd.py"), "--prd", str(source), "--out", str(out)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return out


def write_manifest(root: Path, prd: Path, design: Path, *, approve_e01: bool) -> Path:
    lanes = {}
    for eid in ("E01", "E02"):
        lanes[eid] = {
            "roles": ["product", "engineering"],
            "artifacts": [
                (prd / "core.md").relative_to(root).as_posix(),
                (prd / "epics" / f"{eid}.md").relative_to(root).as_posix(),
                design.relative_to(root).as_posix(),
            ],
            "depends_on": [],
            "assumptions": [],
            "epic": True,
        }
    doc = {
        "schema_version": 2,
        "product": "demo",
        "gates": [{"id": "design-to-backlog", "lanes": lanes}],
        "decisions": [],
        "feedback_events": [],
        "changes": [],
        "change_events": [],
        "assumptions": [],
        "questions": [],
        "question_answers": [],
    }
    if approve_e01:
        hashes = {
            path: hashlib.sha256((root / path).read_bytes()).hexdigest()
            for path in lanes["E01"]["artifacts"]
        }
        for role in ("product", "engineering"):
            doc["decisions"].append(
                {
                    "id": f"D-{len(doc['decisions']) + 1:03d}",
                    "gate": "design-to-backlog",
                    "lane": "E01",
                    "role": role,
                    "reviewer": role,
                    "decision": "approve",
                    "recorded_at": "2026-11-21T12:00:00Z",
                    "artifact_sha256": hashes,
                    "evidence": "ticket-1",
                    "feedback": [],
                }
            )
    (root / "review").mkdir(exist_ok=True)
    path = root / "review" / "demo.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path


def test_splitter_preserves_epic_blocks_and_refuses_re_split():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        prd = split(root)
        core = (prd / "core.md").read_text()
        assert core.startswith("# Demo PRD")
        assert "| MVP   |" in core
        assert "## Open Questions" in core
        assert "Which market?" in core
        assert "E02: Billing" not in core
        epic = (prd / "epics" / "E01.md").read_text()
        assert "### E01: Accounts" in epic and "US-001" in epic
        again = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "split_prd.py"),
                "--prd",
                str(root / "04-prd" / "demo-prd.md"),
                "--out",
                str(prd),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert again.returncode != 0
        assert "already looks split" in again.stderr


def test_epic_generation_uses_only_its_own_file():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        prd = split(root)
        design = root / "05-technical-design" / "demo-technical-design.md"
        design.parent.mkdir()
        design.write_text("# Design\n", encoding="utf-8")
        manifest = write_manifest(root, prd, design, approve_e01=True)
        out = root / "06-backlog" / "demo"
        command = [
            sys.executable,
            str(SCRIPTS / "generate_stories.py"),
            "--prd",
            str(prd),
            "--technical-design",
            str(design),
            "--out-dir",
            str(out),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        allowed = subprocess.run(
            [*command, "--epic", "E01"], text=True, capture_output=True, check=False
        )
        assert allowed.returncode == 0, allowed.stderr
        prompt = (out / "prompts" / "E01-accounts.prompt.md").read_text()
        assert "Create account" in prompt
        assert "Pay bill" not in prompt
        blocked = subprocess.run(
            [*command, "--epic", "E02"], text=True, capture_output=True, check=False
        )
        assert blocked.returncode != 0
        assert "missing approval" in blocked.stderr


def test_editing_only_e02_keeps_e01_ready():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        prd = split(root)
        design = root / "05-technical-design" / "demo-technical-design.md"
        design.parent.mkdir()
        design.write_text("# Design\n", encoding="utf-8")
        manifest = write_manifest(root, prd, design, approve_e01=True)
        assert evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["ready"] is True
        (prd / "epics" / "E02.md").write_text(
            (prd / "epics" / "E02.md").read_text() + "\nNew E02 detail.\n", encoding="utf-8"
        )
        assert evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["ready"] is True
        assert evaluate_gate(manifest, "design-to-backlog", "E02")["lanes"]["E02"]["ready"] is False
