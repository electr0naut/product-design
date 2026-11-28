"""Draft outputs never land on canonical paths, and promotion only copies bytes."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from workflow_common import (  # noqa: E402
    canonical_path,
    draft_path,
    is_draft_path,
)


def fake_cli(tmp_path: Path) -> str:
    executable = tmp_path / "fake-claude"
    executable.write_text(
        "#!/bin/sh\ncat >/dev/null\nprintf '# Generated draft\n'\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    return str(executable)


def run(script: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *arguments],
        capture_output=True,
        text=True,
        check=False,
    )


def test_draft_path_names_files_and_directories_visibly():
    assert draft_path(Path("04-prd/demo-prd.md")) == Path("04-prd/demo-prd.draft.md")
    assert draft_path(Path("06-backlog/demo")) == Path("06-backlog/demo.draft")
    assert draft_path(Path("06-backlog/demo.draft")) == Path("06-backlog/demo.draft")
    assert is_draft_path(Path("x.draft.md")) and is_draft_path(Path("x.draft"))
    assert not is_draft_path(Path("x.md"))
    assert canonical_path(Path("04-prd/demo-prd.draft.md")) == Path("04-prd/demo-prd.md")
    assert canonical_path(Path("06-backlog/demo.draft")) == Path("06-backlog/demo")


def test_draft_never_needs_a_manifest_and_lands_on_a_draft_path(tmp_path: Path):
    brd = tmp_path / "03-brd" / "demo-brd.md"
    brd.parent.mkdir(parents=True)
    brd.write_text("# BRD\n", encoding="utf-8")
    out = tmp_path / "04-prd" / "demo-prd.draft.md"

    result = run(
        "generate_prd.py",
        "--brd",
        str(brd),
        "--out",
        str(out),
        "--draft",
        "--claude-bin",
        fake_cli(tmp_path),
    )

    assert result.returncode == 0, result.stderr
    assert out.is_file()
    assert not (tmp_path / "04-prd" / "demo-prd.md").exists()
    sidecar = json.loads(out.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["output_review_status"]["artifact"].endswith("demo-prd.draft.md")
    assert sidecar["input_gate_readiness"] is None


def test_draft_refuses_a_canonical_out_and_writes_nothing(tmp_path: Path):
    brd = tmp_path / "03-brd" / "demo-brd.md"
    brd.parent.mkdir(parents=True)
    brd.write_text("# BRD\n", encoding="utf-8")
    out = tmp_path / "04-prd" / "demo-prd.md"

    result = run(
        "generate_prd.py",
        "--brd",
        str(brd),
        "--out",
        str(out),
        "--draft",
        "--claude-bin",
        fake_cli(tmp_path),
    )

    assert result.returncode != 0
    assert "--draft refuses" in result.stderr
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_default_output_is_suffixed_without_touching_the_canonical_file(tmp_path: Path):
    canonical = tmp_path / "04-prd" / "demo-prd.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# Approved words\n", encoding="utf-8")

    assert draft_path(canonical) == tmp_path / "04-prd" / "demo-prd.draft.md"
    assert canonical.read_text(encoding="utf-8") == "# Approved words\n"


def test_split_prd_routes_draft_output_to_a_draft_directory(tmp_path: Path):
    prd = tmp_path / "04-prd" / "demo-prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text(
        "# Demo\n\n### E01: First epic\n\nBody one.\n\n### E02: Second epic\n\nBody two.\n",
        encoding="utf-8",
    )

    result = run("split_prd.py", "--prd", str(prd), "--draft")

    assert result.returncode == 0, result.stderr
    split = tmp_path / "04-prd" / "demo.draft"
    assert (split / "core.md").is_file()
    assert (split / "epics" / "E01.md").is_file()
    assert not (tmp_path / "04-prd" / "demo").exists()


def test_split_prd_refuses_a_canonical_out_when_drafting(tmp_path: Path):
    prd = tmp_path / "04-prd" / "demo-prd.md"
    prd.parent.mkdir(parents=True)
    prd.write_text("### E01: First epic\n\nBody.\n", encoding="utf-8")
    out = tmp_path / "04-prd" / "demo"

    result = run("split_prd.py", "--prd", str(prd), "--out", str(out), "--draft")

    assert result.returncode != 0
    assert "--draft refuses" in result.stderr
    assert not out.exists()


def test_promote_copies_bytes_and_never_writes_review_records(tmp_path: Path):
    draft = tmp_path / "04-prd" / "demo-prd.draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text("# Drafted words\n", encoding="utf-8")
    draft.with_suffix(".provenance.json").write_text(
        json.dumps(
            {
                "snapshot_version": 1,
                "output_review_status": {"status": "draft", "artifact": str(draft)},
            }
        ),
        encoding="utf-8",
    )
    review = tmp_path / "review"
    review.mkdir()
    (review / "demo.json").write_text('{"product": "demo"}', encoding="utf-8")
    before = (review / "demo.json").read_bytes()

    result = run("promote.py", str(draft))

    canonical = tmp_path / "04-prd" / "demo-prd.md"
    assert result.returncode == 0, result.stderr
    assert canonical.read_bytes() == b"# Drafted words\n"
    assert (review / "demo.json").read_bytes() == before
    sidecar = json.loads(canonical.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["output_review_status"]["status"] == "draft"


def test_promote_refuses_to_overwrite_and_refuses_non_draft_sources(tmp_path: Path):
    draft = tmp_path / "04-prd" / "demo-prd.draft.md"
    draft.parent.mkdir(parents=True)
    draft.write_text("# Drafted words\n", encoding="utf-8")
    canonical = tmp_path / "04-prd" / "demo-prd.md"
    canonical.write_text("# Edited by hand\n", encoding="utf-8")

    refused = run("promote.py", str(draft))
    assert refused.returncode != 0
    assert "already exists" in refused.stderr
    assert canonical.read_text(encoding="utf-8") == "# Edited by hand\n"

    forced = run("promote.py", str(draft), "--force")
    assert forced.returncode == 0, forced.stderr
    assert canonical.read_text(encoding="utf-8") == "# Drafted words\n"

    plain = tmp_path / "04-prd" / "notes.md"
    plain.write_text("# Notes\n", encoding="utf-8")
    result = run("promote.py", str(plain))
    assert result.returncode != 0
    assert "not a draft path" in result.stderr


def test_promote_copies_a_draft_directory(tmp_path: Path):
    draft = tmp_path / "04-prd" / "demo.draft"
    (draft / "epics").mkdir(parents=True)
    (draft / "core.md").write_text("# Core\n", encoding="utf-8")
    (draft / "epics" / "E01.md").write_text("# E01\n", encoding="utf-8")

    result = run("promote.py", str(draft))

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "04-prd" / "demo" / "core.md").read_text(encoding="utf-8") == "# Core\n"
    assert (tmp_path / "04-prd" / "demo" / "epics" / "E01.md").is_file()
