"""Question proposals are deterministic and never mutate review decisions."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]


def test_extracts_questions_with_stable_ids_without_writing_manifest(tmp_path: Path):
    prd = tmp_path / "04-prd" / "demo"
    (prd / "epics").mkdir(parents=True)
    (prd / "core.md").write_text("# Demo\n", encoding="utf-8")
    (prd / "epics" / "E01.md").write_text(
        "### E01: Accounts\n## Open Questions\n"
        "- Which market launches first?\n- Is email verification mandatory?\n",
        encoding="utf-8",
    )
    story = tmp_path / "06-backlog" / "demo" / "E01-accounts" / "US-001.md"
    story.parent.mkdir(parents=True)
    story.write_text(
        "---\nid: US-001\nepic: E01\n---\n# Story\n"
        "## Open Questions\n- What is the retry policy?\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "review" / "demo.json"
    manifest.parent.mkdir()
    manifest.write_text(json.dumps({"questions": [{"id": "Q-003", "text": "Existing"}]}))
    before = manifest.read_bytes()
    command = [
        sys.executable,
        str(SCRIPTS / "extract_questions.py"),
        "--prd",
        str(prd),
        "--backlog",
        str(story.parent.parent),
        "--manifest",
        str(manifest),
        "--role",
        "product",
    ]
    first = subprocess.run(command, capture_output=True, text=True, check=False)
    second = subprocess.run(command, capture_output=True, text=True, check=False)
    assert first.returncode == second.returncode == 0, first.stderr
    assert first.stdout == second.stdout
    proposals = json.loads(first.stdout)["proposals"]
    assert [q["id"] for q in proposals] == ["Q-004", "Q-005", "Q-006"]
    assert [q["text"] for q in proposals] == [
        "Which market launches first?",
        "Is email verification mandatory?",
        "What is the retry policy?",
    ]
    assert proposals[0]["source"]["heading"] == "Open Questions"
    assert proposals[0]["lane"] == "E01"
    assert proposals[2]["lane"] == "E01"
    assert manifest.read_bytes() == before
