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
    original = gate_reviews.load_manifest_snapshot

    def counted(path):
        nonlocal loads
        loads += 1
        return original(path)

    monkeypatch.setattr(gate_reviews, "load_manifest_snapshot", counted)
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


def test_warning_window_includes_the_review_by_day_and_allows_zero_days(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    artifact = tmp_path / "review" / "accounts.md"
    for role in ("product", "engineering"):
        decide(tmp_path, doc, "E01", role)
    doc["assumptions"] = [
        {
            "id": "A-001",
            "statement": "Market stays open",
            "source": "ticket-001",
            "checked_at": "2026-11-01",
            "review_by": "2026-11-30",
        }
    ]
    doc["gates"][0]["lanes"]["E01"]["assumptions"] = ["A-001"]
    write_manifest(manifest, doc)

    due_today = artifact_status(manifest, artifact, today=dt.date(2026, 11, 30), warning_days=0)
    assert due_today["status"] == "approved"
    assert [warning["assumption"] for warning in due_today["warnings"]] == ["A-001"]
    assert set(due_today) == {"artifact", "status", "scopes", "warnings"}
    assert set(due_today["scopes"][0]) == {"gate", "lane", "status", "reasons"}


def test_portal_view_reports_every_pending_lane_for_the_role(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    decision = decide(tmp_path, doc, "E01", "engineering")
    decision["feedback"].append({"id": "F-01", "text": "Clarify scope"})
    write_manifest(manifest, doc)

    view = portal_view(manifest, "product")

    assert view["schema_version"] == 1
    assert set(view) == {
        "schema_version",
        "product",
        "role",
        "generated_at",
        "pending_for_role",
        "blocked_on_others",
        "context",
        "questions_for_role",
    }
    assert [entry["lane"] for entry in view["pending_for_role"]] == ["E01", "E02"]
    entry = next(item for item in view["pending_for_role"] if item["lane"] == "E01")
    assert entry["other_roles"]["engineering"]["id"] == "D-001"
    assert entry["decision"] is None


def test_portal_view_handles_a_role_that_only_one_lane_needs(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)

    view = portal_view(manifest, "legal")

    assert [entry["lane"] for entry in view["pending_for_role"]] == ["E02"]
    assert [entry["lane"] for entry in view["context"]] == ["E01"]


def test_portal_view_reports_the_roles_own_approval_without_counting_it_ready(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    write_manifest(manifest, doc)

    view = portal_view(manifest, "product")

    blocked = next(entry for entry in view["blocked_on_others"] if entry["lane"] == "E01")
    assert blocked["decision"]["id"] == "D-001"
    assert [entry["lane"] for entry in view["pending_for_role"]] == ["E02"]


def test_portal_view_returns_stale_approval_to_own_role(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    write_manifest(manifest, doc)
    (tmp_path / "review" / "accounts.md").write_text("Accounts v2\n", encoding="utf-8")
    before = manifest.read_bytes()

    view = portal_view(manifest, "product")

    pending = next(entry for entry in view["pending_for_role"] if entry["lane"] == "E01")
    assert pending["decision"]["decision"] == "approve"
    assert pending["actions"] == ["review_again"]
    assert "stale approval: product" in pending["reasons"]
    assert not any(entry["lane"] == "E01" for entry in view["blocked_on_others"])
    assert manifest.read_bytes() == before


def test_portal_view_requires_roles_own_reapproval_after_question_answer(tmp_path: Path):
    from gate_reviews import portal_view
    from test_gate_reviews import answer, question

    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    question(doc, "E01", "product")
    answer(doc, "Q-001", "2026-11-21T13:00:00Z")
    write_manifest(manifest, doc)

    view = portal_view(manifest, "product")

    entry = next(item for item in view["pending_for_role"] if item["lane"] == "E01")
    assert entry["actions"] == ["review_again"]
    assert "question needs reapproval: Q-001" in entry["reasons"]
    assert not any(item["lane"] == "E01" for item in view["blocked_on_others"])


def test_portal_view_keeps_own_unresolved_feedback_actionable(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    engineer = decide(tmp_path, doc, "E01", "engineering")
    engineer["feedback"] = [{"id": "F-001", "text": "Confirm retention"}]
    decide(tmp_path, doc, "E01", "product")
    write_manifest(manifest, doc)

    view = portal_view(manifest, "engineering")

    pending = next(item for item in view["pending_for_role"] if item["lane"] == "E01")
    assert pending["actions"] == ["resolve_feedback"]
    assert "unresolved feedback: engineering" in pending["reasons"]
    assert not any(item["lane"] == "E01" for item in view["blocked_on_others"])


def test_portal_view_keeps_current_approval_blocked_on_others(tmp_path: Path):
    from gate_reviews import portal_view

    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    write_manifest(manifest, doc)

    view = portal_view(manifest, "product")

    blocked = next(item for item in view["blocked_on_others"] if item["lane"] == "E01")
    assert blocked["actions"] == []
    assert blocked["decision"]["decision"] == "approve"
    assert not any(item["lane"] == "E01" for item in view["pending_for_role"])


def test_portal_view_questions_exclude_other_roles_and_answered_ones(tmp_path: Path):
    from gate_reviews import portal_view
    from test_gate_reviews import answer, question

    manifest, doc = manifest_fixture(tmp_path)
    question(doc, "E01", "product", qid="Q-001")
    question(doc, "E01", "engineering", qid="Q-002")
    answer(doc, "Q-001", "2026-11-21T12:00:00Z")
    write_manifest(manifest, doc)

    view = portal_view(manifest, "product")

    assert view["questions_for_role"] == []
