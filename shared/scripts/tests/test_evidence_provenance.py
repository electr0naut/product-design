"""Evidence instructions and generation provenance contracts."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parents[1]
sys.path.insert(0, str(SCRIPTS))

from workflow_common import bundle_documents, compose_prompt, generate  # noqa: E402


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fake_cli(tmp_path: Path) -> str:
    executable = tmp_path / "fake-claude"
    executable.write_text(
        "#!/bin/sh\ncat >/dev/null\nprintf '# Generated draft\\n'\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    return str(executable)


def prompt_for(tmp_path: Path):
    source = tmp_path / "idea.md"
    source.write_bytes(b"# Idea\nCaf\xc3\xa9\n")
    instruction = tmp_path / "instruction.md"
    instruction.write_text("Analyze the idea.\n", encoding="utf-8")
    template = tmp_path / "template.md"
    template.write_text("# Draft\n", encoding="utf-8")
    prompt = compose_prompt(instruction, template, bundle_documents("Ideas", [source]))
    return prompt, source, instruction, template


def test_generated_document_has_actual_input_and_prompt_hashes(tmp_path: Path):
    prompt, source, instruction, template = prompt_for(tmp_path)
    output = tmp_path / "draft.md"
    assert generate(prompt, output, False, fake_cli(tmp_path)) == "wrote"
    sidecar = json.loads(output.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"] == [{"path": str(source), "sha256": digest(source.read_bytes())}]
    assert sidecar["instruction"] == {
        "path": str(instruction),
        "sha256": digest(instruction.read_bytes()),
    }
    assert sidecar["template"] == {"path": str(template), "sha256": digest(template.read_bytes())}
    assert sidecar["assembled_prompt_sha256"] == digest(str(prompt).encode("utf-8"))
    assert sidecar["document_sha256"] == digest(output.read_bytes())
    assert sidecar["model"] is None  # A CLI executable path is not a model identifier.
    assert datetime.fromisoformat(sidecar["generated_at"]).tzinfo == UTC
    assert "reviewer" not in sidecar
    assert "approved" not in sidecar
    assert sidecar["review_status"] == "draft"
    assert sidecar["review"]["decision_ids"] == {}


def test_policy_hash_tracks_lane_rules_not_unrelated_decisions(tmp_path: Path):
    from gate_reviews import review_provenance

    policy = {
        "roles": ["product", "engineering"],
        "artifacts": ["04-prd/demo/epics/E01.md"],
        "depends_on": [],
        "assumptions": ["A-001"],
        "epic": True,
    }
    data = {
        "gates": [{"id": "design-to-backlog", "lanes": {"E01": policy}}],
        "decisions": [{"id": "D-001", "gate": "design-to-backlog", "lane": "E01"}],
    }
    report = {
        "lanes": {
            "E01": {
                "ready": True,
                "decisions": {"product": {"id": "D-001"}, "engineering": {"id": "D-002"}},
            }
        }
    }
    first = review_provenance(data, "design-to-backlog", report)
    data["decisions"].append({"id": "D-999", "gate": "brd-to-prd", "lane": "legal"})
    second = review_provenance(data, "design-to-backlog", report)
    assert first == second
    assert first["decision_ids"] == {"E01": ["D-001", "D-002"]}
    assert len(first["policy_sha256"]["E01"]) == 64
    data["gates"][0]["lanes"]["E01"]["roles"].append("legal")
    assert (
        review_provenance(data, "design-to-backlog", report)["policy_sha256"]
        != first["policy_sha256"]
    )


def test_generated_document_records_gated_decisions(tmp_path: Path):
    from workflow_common import attach_review

    prompt, *_ = prompt_for(tmp_path)
    review = {
        "gate": "brd-to-prd",
        "lanes": ["product"],
        "decision_ids": {"product": ["D-001"]},
        "policy_sha256": {"product": "a" * 64},
    }
    attach_review(prompt, review)
    output = tmp_path / "prd.md"
    assert generate(prompt, output, False, fake_cli(tmp_path)) == "wrote"
    sidecar = json.loads(output.with_suffix(".provenance.json").read_text())
    assert sidecar["review_status"] == "gated"
    assert sidecar["review"] == review


def test_source_hash_matches_crlf_bytes_not_normalized_text(tmp_path: Path):
    prompt, source, *_ = prompt_for(tmp_path)
    source.write_bytes(b"# Idea\r\nSecond line\r\n")
    prompt = compose_prompt(
        tmp_path / "instruction.md", tmp_path / "template.md", bundle_documents("Ideas", [source])
    )
    output = tmp_path / "draft.md"
    assert generate(prompt, output, False, fake_cli(tmp_path)) == "wrote"
    sidecar = json.loads(output.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"][0]["sha256"] == digest(source.read_bytes())


def test_existing_sidecar_prevents_generation_without_force(tmp_path: Path):
    prompt, *_ = prompt_for(tmp_path)
    output = tmp_path / "draft.md"
    sidecar = output.with_suffix(".provenance.json")
    sidecar.write_bytes(b"reviewed metadata\n")
    assert generate(prompt, output, False, fake_cli(tmp_path)) == "skipped"
    assert not output.exists()
    assert sidecar.read_bytes() == b"reviewed metadata\n"
    assert generate(prompt, output, False, fake_cli(tmp_path), force=True) == "wrote"
    assert output.exists()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["document_sha256"] == digest(
        output.read_bytes()
    )


def test_existing_document_and_sidecar_remain_unchanged_without_force(tmp_path: Path):
    prompt, *_ = prompt_for(tmp_path)
    output = tmp_path / "draft.md"
    sidecar = output.with_suffix(".provenance.json")
    output.write_bytes(b"reviewed document\n")
    sidecar.write_bytes(b"reviewed metadata\n")
    assert generate(prompt, output, False, fake_cli(tmp_path)) == "skipped"
    assert output.read_bytes() == b"reviewed document\n"
    assert sidecar.read_bytes() == b"reviewed metadata\n"


def test_force_rejects_non_file_sidecar_before_overwriting_document(tmp_path: Path):
    prompt, *_ = prompt_for(tmp_path)
    output = tmp_path / "draft.md"
    output.write_bytes(b"reviewed document\n")
    output.with_suffix(".provenance.json").mkdir()
    with pytest.raises(SystemExit, match="regular file"):
        generate(prompt, output, False, fake_cli(tmp_path), force=True)
    assert output.read_bytes() == b"reviewed document\n"


@pytest.mark.parametrize("sidecar_present", [False, True])
@pytest.mark.parametrize("force", [False, True])
def test_sidecar_symlink_or_ancestor_rejected_before_document_write(
    tmp_path: Path, sidecar_present: bool, force: bool
):
    prompt, *_ = prompt_for(tmp_path)
    external = tmp_path / "external"
    external.mkdir()
    target = external / "draft.provenance.json"
    target.write_bytes(b"external metadata\n")
    if sidecar_present:
        output = tmp_path / "draft.md"
        output.with_suffix(".provenance.json").symlink_to(target)
    else:
        redirect = tmp_path / "redirect"
        redirect.symlink_to(external, target_is_directory=True)
        output = redirect / "draft.md"
    with pytest.raises(SystemExit, match="symlink"):
        generate(prompt, output, False, fake_cli(tmp_path), force=force)
    assert target.read_bytes() == b"external metadata\n"
    assert not (external / "draft.md").exists()


def test_no_sidecar_for_prompt_only_or_missing_cli_fallback(tmp_path: Path):
    prompt, *_ = prompt_for(tmp_path)
    output = tmp_path / "draft.md"
    assert generate(prompt, output, True, fake_cli(tmp_path)) == "wrote"
    assert not output.with_suffix(".provenance.json").exists()
    output.unlink()
    assert generate(prompt, output, False, "nonexistent-cli-for-provenance-test") == "fallback"
    assert not output.exists()
    assert output.with_suffix(".prompt.md").exists()
    assert not output.with_suffix(".provenance.json").exists()


@pytest.mark.parametrize("role", ["legal", "compliance"])
def test_role_prompt_and_template_require_sources_and_uncertainty(role: str):
    prompt = (ROOT / "shared" / "prompts" / f"02-analysis-{role}.md").read_text(encoding="utf-8")
    template = (ROOT / "02-analysis" / "templates" / f"{role}-template.md").read_text(
        encoding="utf-8"
    )
    for text in (prompt, template):
        assert "source" in text.lower()
        assert "uncertain" in text.lower()
        assert "jurisdiction" in text.lower()
        assert "human" in text.lower()


def test_analysis_cli_generates_sidecar_without_claiming_model(tmp_path: Path):
    idea = tmp_path / "idea.md"
    idea.write_text("# My idea\n", encoding="utf-8")
    out = tmp_path / "analysis"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_analysis.py"),
            "--idea",
            str(idea),
            "--out-dir",
            str(out),
            "--role",
            "legal",
            "--claude-bin",
            fake_cli(tmp_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    sidecars = list(out.rglob("*.provenance.json"))
    assert len(sidecars) == 1
    assert json.loads(sidecars[0].read_text(encoding="utf-8"))["model"] is None
