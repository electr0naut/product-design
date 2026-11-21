"""Generation sidecars snapshot review state; they never grant approval."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from gate_reviews import artifact_status, generation_receipt, maybe_enforce_gate  # noqa: E402
from test_gate_reviews import decide, manifest_fixture, write_manifest  # noqa: E402
from workflow_common import bundle_documents, compose_prompt, generate  # noqa: E402

PRD = "04-prd/demo-prd.md"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fake_cli(tmp_path: Path) -> str:
    executable = tmp_path / "fake-claude"
    executable.write_text(
        "#!/bin/sh\ncat >/dev/null\nprintf '# Generated draft\n'\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    return str(executable)


def enrol_prd(doc: dict, lane: str = "E01") -> list[str]:
    policy = doc["gates"][0]["lanes"][lane]
    policy["artifacts"].append(PRD)
    return list(policy["roles"])


def review_args(manifest: Path | None, *, draft: bool = False) -> argparse.Namespace:
    return argparse.Namespace(draft=draft, review_manifest=manifest)


def prompt_fixture(tmp_path: Path):
    source = tmp_path / "idea.md"
    source.write_text("# Idea\n", encoding="utf-8")
    instruction = tmp_path / "instruction.md"
    instruction.write_text("Generate a PRD.\n", encoding="utf-8")
    return compose_prompt(instruction, None, bundle_documents("Ideas", [source]))


def test_unwritten_enrolled_output_is_projected_from_an_assumed_hash(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    enrol_prd(doc)
    write_manifest(manifest, doc)
    artifact = tmp_path / PRD
    assert not artifact.exists()

    result = artifact_status(manifest, artifact, assume_sha256="a" * 64)

    assert result["status"] == "in_review"
    assert result["scopes"][0]["lane"] == "E01"
    assert not artifact.exists()


def test_assumed_bytes_bind_to_decisions_instead_of_filenames(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    enrol_prd(doc)
    artifact = tmp_path / PRD
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"# Reviewed PRD\n")
    expected = digest(artifact.read_bytes())
    for role in ("product", "engineering"):
        decide(tmp_path, doc, "E01", role)["artifact_sha256"][PRD] = expected
    write_manifest(manifest, doc)

    assert artifact_status(manifest, artifact, assume_sha256=expected)["status"] == "approved"
    assert artifact_status(manifest, artifact)["status"] == "approved"

    changed = artifact_status(manifest, artifact, assume_sha256=digest(b"# New PRD\n"))
    assert changed["status"] == "needs_reapproval"


def test_assumed_hash_requires_lowercase_hex_digest(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)

    with pytest.raises(ValueError, match="lowercase hex SHA-256"):
        artifact_status(manifest, tmp_path / PRD, assume_sha256="A" * 64)
    with pytest.raises(ValueError, match="lowercase hex SHA-256"):
        artifact_status(manifest, tmp_path / PRD, assume_sha256="abc")


def test_assumed_hash_never_bypasses_symlink_safety(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    enrol_prd(doc)
    write_manifest(manifest, doc)
    external = tmp_path / "external.md"
    external.write_text("External\n", encoding="utf-8")
    link = tmp_path / PRD
    link.parent.mkdir(parents=True)
    link.symlink_to(external)

    with pytest.raises(ValueError, match="unsafe artifact"):
        artifact_status(manifest, link, assume_sha256="a" * 64)


def test_assumed_hash_rejects_directories_and_broken_symlinks(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    write_manifest(manifest, doc)
    directory = tmp_path / PRD
    directory.mkdir(parents=True)

    with pytest.raises(ValueError, match="nonregular artifact"):
        artifact_status(manifest, directory, assume_sha256="a" * 64)

    broken = tmp_path / "broken.md"
    broken.symlink_to(tmp_path / "missing.md")
    with pytest.raises(ValueError, match="unsafe artifact"):
        artifact_status(manifest, broken, assume_sha256="a" * 64)


def test_generation_receipt_separates_input_gate_from_output_status(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    doc["gates"][0]["lanes"]["E02"]["artifacts"].append(PRD)
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    report = maybe_enforce_gate(
        review_args(manifest),
        "demo",
        "design-to-backlog",
        [tmp_path / "review" / "accounts.md"],
        ["E01"],
    )

    snapshot = generation_receipt(report, tmp_path / PRD, today=dt.date(2026, 11, 21))
    fields = snapshot("b" * 64)

    status = fields["output_review_status"]
    assert status["status"] == "in_review"
    assert status["artifact"] == PRD
    assert [scope["lane"] for scope in status["scopes"]] == ["E02"]
    assert status["evaluated_at"] == "2026-11-21"
    assert status["manifest"] == {
        "path": "review/demo.json",
        "sha256": digest(manifest.read_bytes()),
    }
    gate = fields["input_gate_readiness"]
    assert gate["gate"] == "design-to-backlog"
    assert gate["lanes_evaluated"] == ["E01"]
    assert gate["gate_complete"] is False
    assert gate["lanes"]["E01"]["ready"] is True
    assert gate["lanes"]["E01"]["decision_ids"] == ["D-001", "D-002"]
    assert len(gate["lanes"]["E01"]["policy_sha256"]) == 64
    assert fields["snapshot_version"] == 1
    assert "historical" in fields["snapshot_semantics"]


def test_draft_generation_snapshot_is_draft_without_input_gate_evidence(tmp_path: Path):
    fields = generation_receipt(None, tmp_path / PRD, today=dt.date(2026, 11, 21))("c" * 64)

    status = fields["output_review_status"]
    assert status["status"] == "draft"
    assert status["manifest"] is None
    assert status["evaluated_at"] == "2026-11-21"
    assert fields["input_gate_readiness"] is None


def test_generation_receipt_refuses_output_outside_product(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    report = maybe_enforce_gate(
        review_args(manifest),
        "demo",
        "design-to-backlog",
        [tmp_path / "review" / "accounts.md"],
        ["E01"],
    )

    with pytest.raises(SystemExit, match="outside the review manifest product root"):
        generation_receipt(report, tmp_path.parent / "elsewhere" / "demo-prd.md")


def test_generate_writes_snapshot_fields_and_actual_document_hash(tmp_path: Path):
    prompt = prompt_fixture(tmp_path)
    output = tmp_path / "04-prd" / "demo-prd.md"

    outcome = generate(
        prompt,
        output,
        False,
        fake_cli(tmp_path),
        snapshot=generation_receipt(None, output),
    )

    assert outcome == "wrote"
    sidecar = json.loads(output.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["document_sha256"] == digest(output.read_bytes())
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["output_review_status"]["artifact"].endswith(PRD)
    assert sidecar["input_gate_readiness"] is None
    assert sidecar["output_review_status"]["status"] != "approved"
    assert "approved" not in json.dumps(sidecar)


def test_ready_input_gate_with_unenrolled_output_stays_draft(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    report = maybe_enforce_gate(
        review_args(manifest),
        "demo",
        "design-to-backlog",
        [tmp_path / "review" / "accounts.md"],
        ["E01"],
    )
    output = tmp_path / PRD

    generate(
        prompt_fixture(tmp_path),
        output,
        False,
        fake_cli(tmp_path),
        snapshot=generation_receipt(report, output),
    )

    sidecar = json.loads(output.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"]["lanes"]["E01"]["ready"] is True
    assert sidecar["input_gate_readiness"]["gate_complete"] is False


def test_manifest_changed_during_generation_fails_closed(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    report = maybe_enforce_gate(
        review_args(manifest),
        "demo",
        "design-to-backlog",
        [tmp_path / "review" / "accounts.md"],
        ["E01"],
    )
    snapshot = generation_receipt(report, tmp_path / PRD)

    decide(tmp_path, doc, "E02", "product")
    write_manifest(manifest, doc)

    output = tmp_path / PRD
    with pytest.raises(ValueError, match="changed during generation"):
        generate(prompt_fixture(tmp_path), output, False, fake_cli(tmp_path), snapshot=snapshot)
    assert not output.exists()
    assert not output.with_suffix(".provenance.json").exists()


def test_revoked_input_artifacts_fail_closed(tmp_path: Path):
    manifest, doc = manifest_fixture(tmp_path)
    decide(tmp_path, doc, "E01", "product")
    decide(tmp_path, doc, "E01", "engineering")
    write_manifest(manifest, doc)
    report = maybe_enforce_gate(
        review_args(manifest),
        "demo",
        "design-to-backlog",
        [tmp_path / "review" / "accounts.md"],
        ["E01"],
    )
    snapshot = generation_receipt(report, tmp_path / PRD)

    (tmp_path / "review" / "accounts.md").write_text("Edited after approval\n", encoding="utf-8")

    output = tmp_path / PRD
    with pytest.raises(ValueError, match="changed during generation"):
        generate(prompt_fixture(tmp_path), output, False, fake_cli(tmp_path), snapshot=snapshot)
    assert not output.exists()
    assert not output.with_suffix(".provenance.json").exists()


def test_snapshot_failure_writes_neither_document_nor_sidecar(tmp_path: Path):
    output = tmp_path / "04-prd" / "demo-prd.md"

    def exploding_snapshot(_document_sha256: str) -> dict:
        raise ValueError("manifest changed during generation")

    with pytest.raises(ValueError, match="manifest changed"):
        generate(
            prompt_fixture(tmp_path), output, False, fake_cli(tmp_path), snapshot=exploding_snapshot
        )
    assert not output.exists()
    assert not output.with_suffix(".provenance.json").exists()


def test_document_write_failure_leaves_no_sidecar(tmp_path: Path):
    output = tmp_path / "04-prd" / "demo-prd.md"
    output.parent.mkdir(parents=True)
    output.parent.chmod(0o500)
    try:
        with pytest.raises(OSError):
            generate(
                prompt_fixture(tmp_path),
                output,
                False,
                fake_cli(tmp_path),
                snapshot=generation_receipt(None, output),
            )
        assert not output.with_suffix(".provenance.json").exists()
    finally:
        output.parent.chmod(0o700)


def test_cli_generation_records_snapshot_fields(tmp_path: Path):
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
    sidecar = json.loads(sidecars[0].read_text(encoding="utf-8"))
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"] is None
    assert sidecar["output_review_status"]["manifest"] is None
