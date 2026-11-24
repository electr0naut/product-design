"""Tests for risk decision brief validation."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def risk_brief(brd_path: str) -> str:
    """Generate a valid risk brief for testing."""
    source = brd_path
    return (
        "# Risk Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Risk Categories\nMarket risk applies [C1].\n\n"
        "## Risk Models\nVaR model for market risk [C1].\n\n"
        "## Risk Limits\nVaR limit set at 5% [C2].\n\n"
        "## Risk Controls\nDaily monitoring [C2].\n\n"
        "## Risk Measurement\nUnknown.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nReview market risk model [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Market risk scope.\n"
        f"- Source: {source}\n- Quote: Market risk applies to this product.\n"
        "### C2\n- Claim: Risk limits.\n"
        f"- Source: {source}\n- Quote: VaR limit set at 5 percent with daily monitoring.\n"
    )


def run_risk(brd: Path, out: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    """Run risk brief validation."""
    return subprocess.run(
        [
            sys.executable,
            "shared/scripts/risk_brief.py",
            str(out),
            str(brd),
            *extra,
        ],
        capture_output=True,
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent.parent,
    )


def test_valid_risk_brief_is_a_draft_with_provenance(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nMarket risk applies to this product.\nVaR limit set at 5 percent with daily monitoring.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = risk_brief(str(brd))
    out.write_text(response, encoding="utf-8")
    result = run_risk(brd, out)
    assert result.returncode == 0, result.stderr


def test_none_yet_accepted_without_card_reference(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nSome text.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    response = (
        "# Risk Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Risk Categories\nUnknown.\n\n"
        "## Risk Models\nUnknown.\n\n"
        "## Risk Limits\nUnknown.\n\n"
        "## Risk Controls\nUnknown.\n\n"
        "## Risk Measurement\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nUnknown.\n\n"
        "## Evidence Cards\n"
    )
    out.write_text(response, encoding="utf-8")
    result = run_risk(brd, out)
    assert result.returncode == 0, result.stderr


def test_draft_cannot_claim_approval(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nMarket risk applies to this product.\nVaR limit set at 5 percent with daily monitoring.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = risk_brief(str(brd)).replace(
        "Review market risk model [C1].", "Risk model approved [C1]."
    )
    out.write_text(response, encoding="utf-8")
    result = run_risk(brd, out)
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()


def test_all_unknown_with_unstructured_evidence_cards_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nSome text.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    response = (
        "# Risk Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Risk Categories\nUnknown.\n\n"
        "## Risk Models\nUnknown.\n\n"
        "## Risk Limits\nUnknown.\n\n"
        "## Risk Controls\nUnknown.\n\n"
        "## Risk Measurement\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nUnknown.\n\n"
        "## Evidence Cards\n"
        "- Claim: Unstructured text without card heading.\n"
    )
    out.write_text(response, encoding="utf-8")
    result = run_risk(brd, out)
    assert result.returncode != 0
    assert "empty Evidence Cards" in result.stderr
