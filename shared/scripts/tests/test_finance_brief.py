"""Finance decision brief integration tests."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

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


def finance_brief(source: str) -> str:
    return (
        "# Finance Decision Brief: Demo\n\n"
        "Draft for human review; not an approval.\n\n"
        "## Ask\nFund a limited study [C1].\n\n"
        "## Spend Range\n$10,000–$15,000 [C1].\n\n"
        "## Assumptions\nStudy covers one quarter [C2].\n\n"
        "## Funding Source\nUnknown.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nReview study funding [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Study funding estimate.\n"
        f"- Source: {source}\n- Quote: Study costs $10,000–$15,000.\n"
        "### C2\n- Claim: Duration.\n"
        f"- Source: {source}\n- Quote: Study duration is one quarter.\n"
    )


def run_finance(brd: Path, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_finance_brief.py"),
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


def test_valid_finance_brief_is_a_draft_with_provenance(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000–$15,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    expected = finance_brief(str(brd))
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, expected))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == expected
    sidecar = json.loads(out.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"][0]["path"] == str(brd)
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"] is None


def test_percent_is_not_supported_by_bare_number(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs 10.\nStudy duration is one quarter.\n", encoding="utf-8"
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("$10,000–$15,000 [C1].", "10% [C1].")
        .replace("Study costs $10,000–$15,000.", "Study costs 10.")
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "numeric literal" in result.stderr
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_draft_cannot_claim_approval_in_decision_layer(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000–$15,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = finance_brief(str(brd)).replace(
        "Review study funding [C1].", "Finance approval granted [C1]."
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert not out.exists()


@pytest.mark.parametrize(
    "change",
    [
        lambda text: text.replace("$10,000–$15,000 [C1]", "$10,000–$99,000 [C1]"),
        lambda text: text.replace("$10,000–$15,000 [C1]", "$10,000 per month [C1]"),
        lambda text: text.replace("$10,000–$15,000 [C1]", "€10,000–€15,000 [C1]"),
        lambda text: text.replace(
            "Unknown.\n\n## Main Uncertainty", "Unknown. Funds secured.\n\n## Main Uncertainty"
        ),
        lambda text: text.replace(
            "- Quote: Study costs $10,000–$15,000.", "- Quote: Invented cost."
        ),
        lambda text: text.replace("### C2", "### C1"),
        lambda text: text.replace("- Source: ", "- Source: other.md "),
        lambda text: text.replace("[C1]", "[C3]"),
    ],
)
def test_unsourced_or_malformed_claims_leave_no_files(tmp_path: Path, change) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000–$15,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    result = run_finance(
        brd, out, "--claude-bin", fake_model(tmp_path, change(finance_brief(str(brd))))
    )
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_prompt_only_excludes_sibling_and_has_no_sidecar(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nStudy costs $10,000–$15,000.\n", encoding="utf-8")
    (tmp_path / "demo-v2-brd.md").write_text("PRIVATE SIBLING", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_finance(brd, out, "--prompt-only")
    assert result.returncode == 0, result.stderr
    prompt = out.with_suffix(".prompt.md")
    text = prompt.read_text(encoding="utf-8")
    assert "Study costs $10,000–$15,000." in text
    assert "PRIVATE SIBLING" not in text
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


@pytest.mark.parametrize("name", ["demo.md", "other.draft.md"])
def test_canonical_or_other_product_output_is_rejected(tmp_path: Path, name: str) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    out = tmp_path / name
    result = run_finance(brd, out, "--prompt-only")
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".prompt.md").exists()


def test_existing_document_is_preserved_without_force(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    out.write_text("Human-reviewed draft", encoding="utf-8")
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, "Invalid"))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == "Human-reviewed draft"
    assert not out.with_suffix(".provenance.json").exists()


def test_blocked_manifest_rejects_finance_generation(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000–$15,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    review = tmp_path / "review"
    review.mkdir()
    manifest = review / "demo.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "product": "demo",
                "gates": [
                    {
                        "id": "brd-to-prd",
                        "lanes": {
                            "core": {
                                "roles": ["finance"],
                                "artifacts": ["demo-brd.md"],
                                "depends_on": [],
                                "assumptions": [],
                            }
                        },
                    }
                ],
                "decisions": [],
                "feedback_events": [],
                "changes": [],
                "change_events": [],
                "assumptions": [],
                "questions": [],
                "question_answers": [],
            }
        ),
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    model = fake_model(tmp_path, finance_brief(str(brd)))
    result = run_finance(brd, out, "--review-manifest", str(manifest), "--claude-bin", model)
    assert result.returncode != 0
    assert "blocked" in result.stderr.lower()
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()
