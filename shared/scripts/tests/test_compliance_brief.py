"""Tests for compliance decision brief validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def compliance_brief(brd_path: str) -> str:
    """Generate a valid compliance brief for testing."""
    source = brd_path
    return (
        "# Compliance Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Regulatory Requirements\nMiFID II applies [C1].\n\n"
        "## Compliance Obligations\nMiFID II client categorisation required [C1].\n\n"
        "## Meeting Obligations\nImplement client onboarding process [C2].\n\n"
        "## Gaps/Blockers\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nReview MiFID II scope [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Regulatory scope.\n"
        f"- Source: {source}\n- Quote: MiFID II applies to this product.\n"
        "### C2\n- Claim: Compliance obligation.\n"
        f"- Source: {source}\n- Quote: Client onboarding process required.\n"
    )


def fake_model(tmp_path: Path, response: str) -> Path:
    """Create a fake claude binary that returns the response."""
    script = tmp_path / "fake_claude.py"
    script.write_text(
        f"#!/usr/bin/env python3\nimport sys\nprint({response!r})",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return script


def run_compliance(brd: Path, out: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run compliance brief validation."""
    return subprocess.run(
        [
            sys.executable,
            "shared/scripts/compliance_brief.py",
            str(out),
            str(brd),
            *extra,
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent.parent,
    )


def test_valid_compliance_brief_is_a_draft_with_provenance(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nMiFID II applies to this product.\nClient onboarding process required.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = compliance_brief(str(brd))
    out.write_text(response, encoding="utf-8")
    result = run_compliance(brd, out)
    assert result.returncode == 0, result.stderr


def test_none_yet_accepted_without_card_reference(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nSome text.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    response = (
        "# Compliance Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Regulatory Requirements\nUnknown.\n\n"
        "## Compliance Obligations\nUnknown.\n\n"
        "## Meeting Obligations\nUnknown.\n\n"
        "## Gaps/Blockers\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nUnknown.\n\n"
        "## Evidence Cards\n"
    )
    out.write_text(response, encoding="utf-8")
    result = run_compliance(brd, out)
    assert result.returncode == 0, result.stderr


def test_draft_cannot_claim_approval(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nMiFID II applies to this product.\nClient onboarding process required.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = compliance_brief(str(brd)).replace(
        "Review MiFID II scope [C1].", "Compliance approved [C1]."
    )
    out.write_text(response, encoding="utf-8")
    result = run_compliance(brd, out)
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()


def test_all_unknown_with_unstructured_evidence_cards_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nSome text.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    response = (
        "# Compliance Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Regulatory Requirements\nUnknown.\n\n"
        "## Compliance Obligations\nUnknown.\n\n"
        "## Meeting Obligations\nUnknown.\n\n"
        "## Gaps/Blockers\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nUnknown.\n\n"
        "## Evidence Cards\n"
        "- Claim: Unstructured text without card heading.\n"
    )
    out.write_text(response, encoding="utf-8")
    result = run_compliance(brd, out)
    assert result.returncode != 0
    assert "empty Evidence Cards" in result.stderr
