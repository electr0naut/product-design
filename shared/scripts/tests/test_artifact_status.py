"""Derived review status is a read-only projection of manifest decisions."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from gate_reviews import artifact_status  # noqa: E402
from test_gate_reviews import decide, manifest_fixture, write_manifest  # noqa: E402


def test_unenrolled_artifact_is_draft_without_mutating_manifest(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)
    before = manifest.read_bytes()
    untracked = tmp_path / "review" / "future.md"
    untracked.write_text("Unreviewed\n", encoding="utf-8")

    result = artifact_status(manifest, untracked, today=dt.date(2026, 11, 21))

    assert result["status"] == "draft"
    assert result["scopes"] == []
    assert manifest.read_bytes() == before


def test_reviewed_bytes_are_approved_then_require_reapproval_after_edit(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    write_manifest(manifest, doc)
    assert artifact_status(manifest, artifact)["status"] == "in_review"
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    approved = artifact_status(manifest, artifact)
    assert approved["status"] == "approved"
    assert approved["scopes"][0]["gate"] == "design-to-backlog"
    assert approved["scopes"][0]["lane"] == "E01"
    artifact.write_text("Accounts v2\n", encoding="utf-8")
    stale = artifact_status(manifest, artifact)
    assert stale["status"] == "needs_reapproval"
    assert "stale approval: product" in stale["scopes"][0]["reasons"]


def test_change_request_takes_precedence_over_stale_approval(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    artifact.write_text("Accounts v2\n", encoding="utf-8")
    decide(tmp_path, doc, "E01", "engineering", decision="request_changes")
    write_manifest(manifest, doc)

    result = artifact_status(manifest, artifact)

    assert result["status"] == "on_hold"
    assert "not approved: engineering" in result["scopes"][0]["reasons"]


def test_assumption_warning_is_visible_only_and_expiry_still_blocks(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    doc["assumptions"].append(
        {
            "id": "A-001",
            "statement": "Market remains open",
            "source": "ticket-001",
            "checked_at": "2026-11-01",
            "review_by": "2026-11-30",
        }
    )
    doc["gates"][0]["lanes"]["E01"]["assumptions"] = ["A-001"]
    write_manifest(manifest, doc)

    assert artifact_status(manifest, artifact, today=dt.date(2026, 11, 22))["warnings"] == []
    due = artifact_status(manifest, artifact, today=dt.date(2026, 11, 23))
    assert due["status"] == "approved"
    assert due["warnings"][0]["assumption"] == "A-001"
    assert (
        artifact_status(manifest, artifact, today=dt.date(2026, 11, 23), warning_days=6)["warnings"]
        == []
    )
    expired = artifact_status(manifest, artifact, today=dt.date(2026, 12, 1))
    assert expired["status"] == "on_hold"


def test_cli_projects_artifact_state_without_rewriting_manifest(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)
    before = manifest.read_bytes()
    command = [
        sys.executable,
        str(SCRIPTS / "check_gate.py"),
        "--manifest",
        str(manifest),
        "--artifact",
        str(tmp_path / "review" / "accounts.md"),
        "--today",
        "2026-11-21",
        "--json",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    assert result.returncode == 1, result.stderr
    report = json.loads(result.stdout)
    assert report["status"] == "in_review"
    assert report["artifact"] == "review/accounts.md"
    assert report["scopes"][0]["lane"] == "E01"
    assert manifest.read_bytes() == before


def test_cli_accepts_manifest_path_relative_to_current_directory(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check_gate.py"),
            "--manifest",
            "review/demo.json",
            "--artifact",
            str(tmp_path / "review" / "accounts.md"),
            "--json",
        ],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["status"] == "in_review"


def test_one_artifact_in_two_lanes_needs_both_scopes_ready(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    doc["gates"][0]["lanes"]["E02"]["artifacts"].append("review/accounts.md")
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)

    status = artifact_status(manifest, artifact)
    assert status["status"] == "in_review"
    assert [(scope["lane"], scope["status"]) for scope in status["scopes"]] == [
        ("E01", "approved"),
        ("E02", "in_review"),
    ]


def test_question_answer_removes_hold_but_requires_new_approval(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    doc.setdefault("questions", []).append(
        {
            "id": "Q-001",
            "gate": "design-to-backlog",
            "lane": "E01",
            "role": "product",
            "text": "Which market?",
            "source": {"artifact": "review/accounts.md", "heading": "Questions"},
            "raised_at": "2026-11-21T12:10:00Z",
        }
    )
    write_manifest(manifest, doc)
    assert artifact_status(manifest, artifact)["status"] == "on_hold"
    doc["question_answers"].append(
        {
            "id": "QA-001",
            "question_id": "Q-001",
            "text": "Market A",
            "answered_by": "product",
            "answered_at": "2026-11-21T12:20:00Z",
            "ai_assisted": False,
            "evidence": "ticket-003",
        }
    )
    write_manifest(manifest, doc)
    assert artifact_status(manifest, artifact)["status"] == "needs_reapproval"


def test_invalid_manifest_and_symlinked_artifact_fail_closed(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    write_manifest(manifest, doc)
    symlink = tmp_path / "review" / "alias.md"
    symlink.symlink_to(artifact)
    with pytest.raises(ValueError, match="unsafe artifact"):
        artifact_status(manifest, symlink)
    manifest.write_text('{"schema_version":2,"schema_version":1}', encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate JSON key"):
        artifact_status(manifest, artifact)


def test_status_uses_one_manifest_snapshot_for_all_scopes(tmp_path: Path, monkeypatch):
    import gate_reviews

    manifest, doc = manifest_fixture(tmp_path)
    doc["gates"][0]["lanes"]["E02"]["artifacts"].append("review/accounts.md")
    write_manifest(manifest, doc)
    loads = 0
    original = gate_reviews.load_manifest

    def counted(path):
        nonlocal loads
        loads += 1
        return original(path)

    monkeypatch.setattr(gate_reviews, "load_manifest", counted)
    artifact_status(manifest, tmp_path / "review" / "accounts.md")
    assert loads == 1


def test_artifact_changed_between_scope_checks_never_reports_approved(tmp_path: Path, monkeypatch):
    import gate_reviews

    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    e02 = doc["gates"][0]["lanes"]["E02"]
    e02["artifacts"].append("review/accounts.md")
    e02["depends_on"] = []
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    artifact.write_text("Accounts v2\n", encoding="utf-8")
    for role in ("product", "legal"):
        decision = decide(tmp_path, doc, "E02", role)
        decision["artifact_sha256"]["review/accounts.md"] = gate_reviews.artifact_hash(
            tmp_path, "review/accounts.md"
        )
    artifact.write_text("Accounts v1\n", encoding="utf-8")
    write_manifest(manifest, doc)
    original = gate_reviews._evaluate_gate_data
    calls = 0

    def mutating(*args, **kwargs):
        nonlocal calls
        result = original(*args, **kwargs)
        calls += 1
        if calls == 1:
            artifact.write_text("Accounts v2\n", encoding="utf-8")
        return result

    monkeypatch.setattr(gate_reviews, "_evaluate_gate_data", mutating)
    with pytest.raises(ValueError, match="changed during status evaluation"):
        artifact_status(manifest, artifact)


def test_nonoverlapping_historical_approvals_are_not_previous_full_approval(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    decide(tmp_path, doc, "E01", "product")["recorded_at"] = "2026-11-21T12:00:00Z"
    decide(tmp_path, doc, "E01", "product", decision="request_changes")["recorded_at"] = (
        "2026-11-21T12:01:00Z"
    )
    decide(tmp_path, doc, "E01", "engineering")["recorded_at"] = "2026-11-21T12:02:00Z"
    artifact.write_text("Accounts v2\n", encoding="utf-8")
    decide(tmp_path, doc, "E01", "product")["recorded_at"] = "2026-11-21T12:03:00Z"
    write_manifest(manifest, doc)
    assert artifact_status(manifest, artifact)["status"] == "in_review"


def test_cli_invalid_unhashable_role_returns_invalid_exit_not_traceback(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    doc["gates"][0]["lanes"]["E01"]["roles"] = [["product"]]
    write_manifest(manifest, doc)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "check_gate.py"),
            "--manifest",
            str(manifest),
            "--artifact",
            str(tmp_path / "review" / "accounts.md"),
            "--json",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
