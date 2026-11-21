"""Review packs and the all-products stale report."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def build(root: Path) -> tuple[Path, dict]:
    (root / "review").mkdir()
    (root / "artifacts").mkdir()
    (root / "artifacts" / "a.md").write_text("A v1\n", encoding="utf-8")
    (root / "artifacts" / "b.md").write_text("B v1\n", encoding="utf-8")
    doc = {
        "schema_version": 2,
        "product": "demo",
        "gates": [
            {
                "id": "gate-a",
                "lanes": {
                    "E01": {
                        "roles": ["product"],
                        "artifacts": ["artifacts/a.md"],
                        "depends_on": [],
                        "assumptions": [],
                        "epic": True,
                    }
                },
            },
            {
                "id": "gate-b",
                "lanes": {
                    "E02": {
                        "roles": ["product"],
                        "artifacts": ["artifacts/b.md"],
                        "depends_on": [],
                        "assumptions": ["A-001"],
                        "epic": True,
                    }
                },
            },
        ],
        "decisions": [],
        "feedback_events": [],
        "changes": [],
        "change_events": [],
        "assumptions": [
            {
                "id": "A-001",
                "statement": "Regulator guidance is current",
                "source": "regulator-2026",
                "checked_at": "2026-01-01",
                "review_by": "2026-06-01",
            }
        ],
        "questions": [
            {
                "id": "Q-001",
                "gate": "gate-b",
                "lane": "E02",
                "role": "product",
                "text": "Which market?",
                "source": {"artifact": "artifacts/b.md", "heading": "Release"},
                "raised_at": "2026-11-21T12:00:00Z",
            }
        ],
        "question_answers": [],
    }
    for gate, lane, artifact in (("gate-a", "E01", "a.md"), ("gate-b", "E02", "b.md")):
        digest = hashlib.sha256((root / "artifacts" / artifact).read_bytes()).hexdigest()
        doc["decisions"].append(
            {
                "id": f"D-{len(doc['decisions']) + 1:03d}",
                "gate": gate,
                "lane": lane,
                "role": "product",
                "reviewer": "P",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {f"artifacts/{artifact}": digest},
                "evidence": "ticket-1",
                "feedback": [],
            }
        )
    path = root / "review" / "demo.json"
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return path, doc


def test_pack_names_missing_approval_and_open_question():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = build(root)
        doc["decisions"] = [d for d in doc["decisions"] if d["lane"] == "E01"]
        manifest.write_text(json.dumps(doc), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "review_pack.py"),
                "--manifest",
                str(manifest),
                "--role",
                "product",
                "--out",
                str(root / "pack.md"),
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        text = (root / "pack.md").read_text()
        assert "gate-b / E02 — BLOCKED" in text
        assert "missing approval: product" in text
        assert "Q-001" in text
        assert "unanswered" in text
        assert "A-001" in text


def test_all_report_exposes_a_stale_lane_and_a_fixed_date():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = build(root)
        (root / "artifacts" / "b.md").write_text("B v2\n", encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_gate.py"),
                "--manifest",
                str(manifest),
                "--all",
                "--json",
                "--today",
                "2026-05-01",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        report = json.loads(result.stdout)
        assert report["today"] == "2026-05-01"
        lanes = report["products"][0]["gates"]
        assert lanes["gate-a"]["lanes"]["E01"]["ready"] is True
        assert lanes["gate-b"]["lanes"]["E02"]["ready"] is False
        assert lanes["gate-b"]["lanes"]["E02"]["stale_roles"] == ["product"]
        expired = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_gate.py"),
                "--manifest",
                str(manifest),
                "--all",
                "--json",
                "--today",
                "2026-07-01",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        reasons = json.loads(expired.stdout)["products"][0]["gates"]["gate-b"]["lanes"]["E02"][
            "reasons"
        ]
        assert "expired assumption: A-001" in reasons
