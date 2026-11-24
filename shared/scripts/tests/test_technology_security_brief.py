"""Technology and security decision brief integration tests."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def fake_model(tmp_path: Path, response: str) -> str:
    document = tmp_path / "model-output.md"
    document.write_text(response, encoding="utf-8")
    executable = tmp_path / "fake-model"
    executable.write_text(
        f"#!/bin/sh\ncat >/dev/null\ncat {shlex.quote(str(document))}\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    return str(executable)


def tech_brief(source: str) -> str:
    return (
        "# Technology and Security Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Build Options\nCloud-based [C1].\n\n"
        "## Custody/Keys\nCustomer-managed [C1].\n\n"
        "## Venue Connectivity\nDirect connect [C1].\n\n"
        "## Security Risks\nUnknown.\n\n"
        "## Hard Blockers\nnone yet.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nReview build options [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Build and custody approach.\n"
        f"- Source: {source}\n- Quote: Cloud-based with customer-managed keys and direct connect.\n"
    )


def run_tech(brd: Path, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_technology_security_brief.py"),
            "--brd",
            str(brd),
            "--out",
            str(out),
            *args,
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_valid_tech_brief_is_a_draft_with_provenance(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nCloud-based with customer-managed keys and direct connect.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    expected = tech_brief(str(brd))
    result = run_tech(brd, out, "--claude-bin", fake_model(tmp_path, expected))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == expected
    sidecar = json.loads(out.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"][0]["path"] == str(brd)
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"] is None


def test_none_yet_accepted_without_card_reference(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nCloud-based with customer-managed keys and direct connect.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = tech_brief(str(brd))
    result = run_tech(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_draft_cannot_claim_approval(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nCloud-based with customer-managed keys and direct connect.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = tech_brief(str(brd)).replace(
        "Review build options [C1].", "Architecture approved [C1]."
    )
    result = run_tech(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert not out.exists()
