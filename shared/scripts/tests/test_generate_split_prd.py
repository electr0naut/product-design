"""PRD generation can emit the physical split layout without silent truncation."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def fake_claude(tmp_path: Path, text: str) -> Path:
    content = tmp_path / "response.md"
    content.write_text(text, encoding="utf-8")
    executable = tmp_path / "fake-claude"
    executable.write_text(f"#!/bin/sh\ncat >/dev/null\ncat '{content}'\n", encoding="utf-8")
    executable.chmod(0o755)
    return executable


def test_generates_split_prd_with_draft_sidecars(tmp_path: Path):
    brd = tmp_path / "03-brd" / "demo-brd.md"
    brd.parent.mkdir()
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    output = tmp_path / "04-prd" / "demo"
    response = (
        "# Demo PRD\n\n## Overview\nShared context.\n\n"
        "### E01: Accounts\n| ID | Story | Persona | Traces to | Priority |\n"
        "|----|-------|---------|-----------|----------|\n"
        "| US-001 | Sign up | User | BR-001 | Must |\n\n"
        "## Release Plan\nLaunch phases.\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_prd.py"),
            "--brd",
            str(brd),
            "--out",
            str(output),
            "--format",
            "split",
            "--draft",
            "--claude-bin",
            str(fake_claude(tmp_path, response)),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Launch phases." in (output / "core.md").read_text()
    assert "Sign up" in (output / "epics" / "E01.md").read_text()
    for file in (output / "core.md", output / "epics" / "E01.md"):
        receipt = json.loads(file.with_suffix(".provenance.json").read_text())
        assert receipt["review_status"] == "draft"
        assert receipt["document_sha256"]
    assert not (output / "draft.md").exists()


def test_invalid_split_response_writes_no_artifacts(tmp_path: Path):
    brd = tmp_path / "03-brd" / "demo-brd.md"
    brd.parent.mkdir()
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    output = tmp_path / "04-prd" / "demo"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_prd.py"),
            "--brd",
            str(brd),
            "--out",
            str(output),
            "--format",
            "split",
            "--draft",
            "--claude-bin",
            str(fake_claude(tmp_path, "# No epics\n")),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert not output.exists()


def test_technical_design_reads_split_prd_files(tmp_path: Path):
    prd = tmp_path / "04-prd" / "demo"
    (prd / "epics").mkdir(parents=True)
    (prd / "core.md").write_text("# Core\nShared context.\n", encoding="utf-8")
    (prd / "epics" / "E01.md").write_text("### E01: Accounts\nStory data.\n", encoding="utf-8")
    output = tmp_path / "05-technical-design" / "demo-technical-design.md"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_technical_design.py"),
            "--prd",
            str(prd),
            "--out",
            str(output),
            "--prompt-only",
            "--draft",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    prompt = output.with_suffix(".prompt.md").read_text()
    assert "Shared context." in prompt
    assert "Story data." in prompt
