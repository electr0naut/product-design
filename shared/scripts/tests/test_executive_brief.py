"""Executive decision brief: one role-shaped draft with verifiable BRD excerpts."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from executive_brief import validate_executive_brief  # noqa: E402
from workflow_common import generate, sha256  # noqa: E402


def run_brief(brd: Path, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_executive_brief.py"),
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


def fake_model(tmp_path: Path, response: str) -> str:
    document = tmp_path / "model-output.md"
    document.write_text(response, encoding="utf-8")
    executable = tmp_path / "fake-model"
    executable.write_text(
        f"#!/bin/sh\ncat >/dev/null\ncat {shlex.quote(str(document))}\n", encoding="utf-8"
    )
    executable.chmod(0o755)
    return str(executable)


def brief(source: str, quote: str = "Budget estimate: $12,000.") -> str:
    fixture = Path(__file__).parent / "fixtures" / "executive-brief.md"
    return fixture.read_text(encoding="utf-8").format(source=source, quote=quote)


def test_template_disclaimer_produces_a_valid_brief(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    template = (
        SCRIPTS.parents[1] / "03-brd" / "templates" / "executive-brief-template.md"
    ).read_text(encoding="utf-8")
    disclaimer = template.splitlines()[2]
    out = tmp_path / "demo.draft.md"
    response = brief(str(brd)).replace("Draft for human review; not an approval.", disclaimer)
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert out.exists()


def test_approval_preamble_is_rejected(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    forged = brief(str(brd)).replace(
        "Draft for human review; not an approval.",
        "APPROVED BY EXECUTIVES. Launch immediately.\n\nDraft for human review; not an approval.",
    )
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, forged))
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_approval_claim_in_decision_layer_is_rejected(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    forged = brief(str(brd)).replace("Start small [C1].", "Approved by executives [C1].")
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, forged))
    assert result.returncode != 0
    assert not out.exists()


def test_unknown_does_not_hide_an_uncited_assertion(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    forged = brief(str(brd)).replace(
        "## Main Risk\nUnknown.", "## Main Risk\nUnknown budget. Guaranteed savings of $5m."
    )
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, forged))
    assert result.returncode != 0
    assert not out.exists()


def test_duplicate_option_numbers_are_rejected(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    forged = brief(str(brd)).replace("- Option 2: Defer [C1].", "- Option 1: Defer [C1].")
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, forged))
    assert result.returncode != 0
    assert not out.exists()


def test_valid_model_writes_draft_and_historical_provenance(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, brief(str(brd))))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == brief(str(brd))
    sidecar = json.loads(out.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"][0]["path"] == str(brd)
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"] is None


@pytest.mark.parametrize(
    "change",
    [
        lambda text: text.replace("Start small [C1].", "Start small [C1].\nGuaranteed savings."),
        lambda text: text.replace("Start small [C1].", "Start small [C1]. [C0]"),
    ],
)
def test_uncited_decision_lines_are_rejected(tmp_path: Path, change):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, change(brief(str(brd)))))
    assert result.returncode != 0
    assert "card" in result.stderr.lower() or "reference" in result.stderr.lower()
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_invalid_quote_rejected_without_output(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    model = fake_model(tmp_path, brief(str(brd), "Invented estimate: $99,000."))
    result = run_brief(brd, out, "--claude-bin", model)
    assert result.returncode != 0
    assert "quote" in result.stderr.lower()
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_blocked_manifest_cannot_generate_a_brief(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
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
                                "roles": ["executive"],
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
    model = fake_model(tmp_path, brief(str(brd)))
    result = run_brief(brd, out, "--review-manifest", str(manifest), "--claude-bin", model)
    assert result.returncode != 0
    assert "blocked" in result.stderr.lower()
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()
    draft = run_brief(
        brd, out, "--review-manifest", str(manifest), "--draft", "--claude-bin", model
    )
    assert draft.returncode == 0, draft.stderr
    assert "DRAFT ONLY" in draft.stderr
    assert (
        json.loads(out.with_suffix(".provenance.json").read_text())["input_gate_readiness"] is None
    )


def test_snapshot_time_brd_change_rejected_before_document_write(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    expected = sha256(brd.read_bytes())
    out = tmp_path / "demo.draft.md"

    def validate(content: str) -> None:
        validate_executive_brief(content, brd, expected)

    def change_source(_document_sha256: str) -> dict:
        brd.write_text("# Demo BRD\nBudget estimate: $99,000.\n", encoding="utf-8")
        return {}

    with pytest.raises(SystemExit, match="BRD changed"):
        generate(
            "input prompt",
            out,
            False,
            fake_model(tmp_path, brief(str(brd))),
            snapshot=change_source,
            validate=validate,
        )
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_model_cannot_write_after_brd_changes_during_generation(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    response = tmp_path / "model-output.md"
    response.write_text(brief(str(brd)), encoding="utf-8")
    model = tmp_path / "model-mutates-brd"
    model.write_text(
        f"#!/bin/sh\ncat >/dev/null\nprintf 'Changed\\n' >> {shlex.quote(str(brd))}\ncat {shlex.quote(str(response))}\n",
        encoding="utf-8",
    )
    model.chmod(0o755)
    result = run_brief(brd, out, "--claude-bin", str(model))
    assert result.returncode != 0
    assert "BRD changed" in result.stderr
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


@pytest.mark.parametrize("name", ["demo.md", "other.draft.md"])
def test_canonical_or_other_product_output_rejected(tmp_path: Path, name: str):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / name
    result = run_brief(brd, out, "--prompt-only")
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".prompt.md").exists()


@pytest.mark.parametrize(
    "change",
    [
        lambda text: text.replace("## Cost of Saying No", "## Cost of Refusal"),
        lambda text: text.replace("- Option 2:", "- Another option:"),
        lambda text: text.replace("### C1", "### C2"),
        lambda text: text.replace(
            "### C1", "### C1\n- Claim: Duplicate\n- Source: x\n- Quote: x\n### C1"
        ),
        lambda text: text.replace("- Source: ", "- Source: other.md "),
    ],
)
def test_bad_structure_or_cards_rejected(tmp_path: Path, change):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_brief(brd, out, "--claude-bin", fake_model(tmp_path, change(brief(str(brd)))))
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_prompt_only_uses_only_named_brd_and_creates_no_provenance(tmp_path: Path):
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\nBudget estimate: $12,000.\n", encoding="utf-8")
    other = tmp_path / "demo-v2-brd.md"
    other.write_text("SECRET SIBLING INPUT", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_brief(brd, out, "--prompt-only")
    assert result.returncode == 0, result.stderr
    prompt = out.with_suffix(".prompt.md")
    assert prompt.is_file()
    assert "Budget estimate: $12,000." in prompt.read_text(encoding="utf-8")
    assert "SECRET SIBLING INPUT" not in prompt.read_text(encoding="utf-8")
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()
