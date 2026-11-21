"""Behavior tests for recording, migrating and projecting review decisions."""

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


def write(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")


def fixture(root: Path) -> tuple[Path, dict]:
    (root / "review").mkdir()
    (root / "artifacts").mkdir()
    artifact = root / "artifacts" / "scope.md"
    artifact.write_text("Scope v1\n", encoding="utf-8")
    doc = {
        "schema_version": 2,
        "product": "demo",
        "gates": [
            {
                "id": "design-to-backlog",
                "lanes": {
                    "E01": {
                        "roles": ["product", "engineering"],
                        "artifacts": ["artifacts/scope.md"],
                        "depends_on": [],
                        "assumptions": [],
                        "epic": True,
                    },
                    "E02": {
                        "roles": ["product", "legal"],
                        "artifacts": ["artifacts/scope.md"],
                        "depends_on": [],
                        "assumptions": [],
                        "epic": True,
                    },
                },
            }
        ],
        "decisions": [],
        "feedback_events": [],
        "changes": [],
        "change_events": [],
        "assumptions": [],
        "questions": [],
        "question_answers": [],
    }
    return root / "review" / "demo.json", doc


def packet(
    root: Path, *, decision: str = "approve", role: str = "product", lane: str = "E01"
) -> dict:
    digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
    return {
        "schema_version": 1,
        "product": "demo",
        "gate": "design-to-backlog",
        "lane": lane,
        "role": role,
        "decision": decision,
        "reviewer": "Named Reviewer",
        "artifact_sha256": {"artifacts/scope.md": digest},
        "feedback": [{"text": "Tighten the retention wording."}],
        "created_at": "2026-11-21T12:00:00Z",
        "source_commit": "a" * 40,
    }


def run(
    root: Path, manifest: Path, packet_data: dict | None = None, *extra: str
) -> subprocess.CompletedProcess:
    path = root / "packet.json"
    write(path, packet_data or packet(root))
    command = [
        sys.executable,
        str(SCRIPTS / "record_decision.py"),
        "--manifest",
        str(manifest),
        "--packet",
        str(path),
        "--evidence",
        "slack:C123/456",
        *extra,
    ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def test_approve_packet_is_recorded_with_assigned_ids_and_attestation():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        result = run(root, manifest)
        assert result.returncode == 0, result.stderr
        data = json.loads(manifest.read_text())
        decision = data["decisions"][0]
        assert decision["id"] == "D-001"
        assert decision["attestation"] == "typed-name, unverified"
        assert decision["source_commit"] == "a" * 40
        assert decision["feedback"][0]["id"] == "F-001"
        assert "F-001" in result.stdout


def test_stale_approval_is_refused_without_touching_the_manifest():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        before = manifest.read_bytes()
        stale_packet = packet(root)
        (root / "artifacts" / "scope.md").write_text("Scope v2\n", encoding="utf-8")
        result = run(root, manifest, stale_packet)
        assert result.returncode == 1
        assert "stale approval" in result.stderr
        assert manifest.read_bytes() == before


def test_stale_non_approval_needs_explicit_acceptance():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        stale_packet = packet(root, decision="request_changes")
        (root / "artifacts" / "scope.md").write_text("Scope v2\n", encoding="utf-8")
        refused = run(root, manifest, stale_packet)
        assert refused.returncode == 1
        assert "--accept-stale" in refused.stderr
        accepted = run(root, manifest, stale_packet, "--accept-stale")
        assert accepted.returncode == 0, accepted.stderr
        assert json.loads(manifest.read_text())["decisions"][0]["decision"] == "request_changes"


def test_packet_older_than_the_latest_decision_is_refused():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        doc["decisions"].append(
            {
                "id": "D-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "product",
                "reviewer": "Earlier",
                "decision": "request_changes",
                "recorded_at": "2026-11-21T13:00:00Z",
                "artifact_sha256": {"artifacts/scope.md": digest},
                "evidence": "slack:C1/1",
                "feedback": [],
            }
        )
        write(manifest, doc)
        result = run(root, manifest)
        assert result.returncode == 1
        assert "predates" in result.stderr


def test_unknown_role_packet_is_refused():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        result = run(root, manifest, packet(root, role="stranger"))
        assert result.returncode == 2
        assert "not required" in result.stderr


def test_questions_block_until_answered_and_reapproved():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        for role in ("product", "engineering"):
            doc["decisions"].append(
                {
                    "id": f"D-{role}",
                    "gate": "design-to-backlog",
                    "lane": "E01",
                    "role": role,
                    "reviewer": "R",
                    "decision": "approve",
                    "recorded_at": "2026-11-21T12:00:00Z",
                    "artifact_sha256": {"artifacts/scope.md": digest},
                    "evidence": "slack:C1/1",
                    "feedback": [],
                }
            )
        doc["questions"].append(
            {
                "id": "Q-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "engineering",
                "text": "Is 30-day retention correct?",
                "source": {"artifact": "artifacts/scope.md", "heading": "Data retention"},
                "raised_at": "2026-11-21T12:05:00Z",
            }
        )
        write(manifest, doc)
        assert evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["ready"] is False
        doc["question_answers"].append(
            {
                "id": "QA-001",
                "question_id": "Q-001",
                "text": "Confirmed 30 days with legal.",
                "answered_by": "engineering",
                "answered_at": "2026-11-21T12:30:00Z",
                "ai_assisted": False,
                "evidence": "slack:C1/2",
            }
        )
        write(manifest, doc)
        reasons = evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["reasons"]
        assert "question needs reapproval: Q-001" in reasons
        doc["decisions"].append(
            {
                "id": "D-003",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "engineering",
                "reviewer": "R",
                "decision": "approve",
                "recorded_at": "2026-11-21T13:00:00Z",
                "artifact_sha256": {"artifacts/scope.md": digest},
                "evidence": "slack:C1/3",
                "feedback": [],
            }
        )
        write(manifest, doc)
        assert evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["ready"] is True


def test_portal_view_splits_pending_ready_and_context_for_a_role():
    from gate_reviews import portal_view

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        doc["decisions"].append(
            {
                "id": "D-001",
                "gate": "design-to-backlog",
                "lane": "E02",
                "role": "product",
                "reviewer": "P",
                "decision": "request_changes",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {"artifacts/scope.md": digest},
                "evidence": "slack:C1/1",
                "feedback": [],
            }
        )
        doc["questions"].append(
            {
                "id": "Q-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "product",
                "text": "Which launch market?",
                "source": {"artifact": "artifacts/scope.md", "heading": "Release"},
                "raised_at": "2026-11-21T12:05:00Z",
            }
        )
        write(manifest, doc)
        view = portal_view(manifest, "product")
        assert [item["lane"] for item in view["pending_for_role"]] == ["E01", "E02"]
        assert [item["lane"] for item in view["context"]] == []
        assert view["questions_for_role"][0]["id"] == "Q-001"
        engineer = portal_view(manifest, "engineering")
        assert engineer["pending_for_role"][0]["lane"] == "E01"
        assert {item["lane"] for item in engineer["context"]} == {"E02"}


def test_cli_emits_the_portal_view_for_a_role():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "check_gate.py"),
                "--manifest",
                str(manifest),
                "--role",
                "product",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        view = json.loads(result.stdout)
        assert view["role"] == "product"
        assert [item["lane"] for item in view["pending_for_role"]] == ["E01", "E02"]


def test_out_of_order_decisions_are_rejected():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        base = {
            "gate": "design-to-backlog",
            "lane": "E01",
            "role": "product",
            "reviewer": "R",
            "decision": "approve",
            "artifact_sha256": {"artifacts/scope.md": digest},
            "evidence": "slack:C1/1",
            "feedback": [],
        }
        doc["decisions"] = [
            {**base, "id": "D-001", "recorded_at": "2026-11-21T13:00:00Z"},
            {**base, "id": "D-002", "recorded_at": "2026-11-21T12:00:00Z"},
        ]
        write(manifest, doc)
        try:
            evaluate_gate(manifest, "design-to-backlog", "E01")
        except ValueError as exc:
            assert "out of time order" in str(exc)
        else:
            raise AssertionError("out-of-order decisions were accepted")


def test_migration_is_idempotent_and_preserves_outcomes():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        doc["schema_version"] = 1
        for key in ("feedback_events", "change_events", "questions", "question_answers"):
            doc.pop(key)
        doc["decisions"].append(
            {
                "id": "D-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "product",
                "reviewer": "P",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {"artifacts/scope.md": digest},
                "evidence": "slack:C1/1",
                "feedback": [
                    {
                        "id": "F-001",
                        "text": "Clarify retention.",
                        "status": "resolved",
                        "resolution": "Clarified in the source",
                    }
                ],
            }
        )
        doc["changes"].append(
            {
                "id": "CHG-001",
                "source": "regulator-notice-001",
                "raised_at": "2026-11-21T12:10:00Z",
                "effective_at": "2026-12-01",
                "status": "resolved",
                "resolved_at": "2026-11-21T12:20:00Z",
                "affected": [{"gate": "design-to-backlog", "lane": "E01"}],
            }
        )
        write(manifest, doc)
        first = subprocess.run(
            [sys.executable, str(SCRIPTS / "migrate_manifest.py"), "--manifest", str(manifest)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert first.returncode == 0, first.stderr
        migrated = manifest.read_bytes()
        data = json.loads(migrated)
        assert data["schema_version"] == 2
        assert data["feedback_events"][0]["action"] == "resolve"
        assert data["change_events"][0]["action"] == "resolve"
        second = subprocess.run(
            [sys.executable, str(SCRIPTS / "migrate_manifest.py"), "--manifest", str(manifest)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert second.returncode == 0, second.stderr
        assert manifest.read_bytes() == migrated
        reasons = evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["reasons"]
        assert "reapproval required after change: CHG-001 (product)" in reasons


def test_migration_accepts_open_feedback_and_keeps_it_blocking():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        digest = hashlib.sha256((root / "artifacts" / "scope.md").read_bytes()).hexdigest()
        doc["schema_version"] = 1
        for key in ("feedback_events", "change_events", "questions", "question_answers"):
            doc.pop(key)
        doc["decisions"].append(
            {
                "id": "D-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "product",
                "reviewer": "P",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {"artifacts/scope.md": digest},
                "evidence": "slack:C1/1",
                "feedback": [{"id": "F-001", "text": "Still open.", "status": "open"}],
            }
        )
        write(manifest, doc)
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "migrate_manifest.py"), "--manifest", str(manifest)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        reasons = evaluate_gate(manifest, "design-to-backlog", "E01")["lanes"]["E01"]["reasons"]
        assert "unresolved feedback: product" in reasons


def test_change_event_before_the_change_is_rejected():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        doc["changes"].append(
            {
                "id": "CHG-001",
                "source": "notice",
                "raised_at": "2026-11-21T12:30:00Z",
                "effective_at": "2026-12-01",
                "affected": [{"gate": "design-to-backlog", "lane": "E01"}],
            }
        )
        doc["change_events"].append(
            {
                "id": "CE-001",
                "change_id": "CHG-001",
                "action": "resolve",
                "text": "Too early",
                "at": "2026-11-21T11:00:00Z",
                "by": "legal",
                "evidence": "memo-1",
            }
        )
        write(manifest, doc)
        try:
            evaluate_gate(manifest, "design-to-backlog", "E01")
        except ValueError as exc:
            assert "predates its change" in str(exc)
        else:
            raise AssertionError("a change event before the change was accepted")


def test_answer_before_question_is_rejected():
    from gate_reviews import evaluate_gate

    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        doc["questions"].append(
            {
                "id": "Q-001",
                "gate": "design-to-backlog",
                "lane": "E01",
                "role": "product",
                "text": "Which market?",
                "source": {"artifact": "artifacts/scope.md", "heading": "Release"},
                "raised_at": "2026-11-21T12:30:00Z",
            }
        )
        doc["question_answers"].append(
            {
                "id": "QA-001",
                "question_id": "Q-001",
                "text": "EU",
                "answered_by": "product",
                "answered_at": "2026-11-21T11:00:00Z",
                "ai_assisted": False,
                "evidence": "memo-1",
            }
        )
        write(manifest, doc)
        try:
            evaluate_gate(manifest, "design-to-backlog", "E01")
        except ValueError as exc:
            assert "predates its question" in str(exc)
        else:
            raise AssertionError("an answer before its question was accepted")


def test_packet_with_non_string_source_commit_is_refused():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = fixture(root)
        write(manifest, doc)
        bad = packet(root)
        bad["source_commit"] = 123
        result = run(root, manifest, bad)
        assert result.returncode == 2
        assert "source_commit" in result.stderr
        assert json.loads(manifest.read_text())["decisions"] == []
