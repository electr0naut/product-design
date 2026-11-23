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
        "## Ledger Model\nActivity recorded in the main ledger [C1].\n\n"
        "## Billing\nMonthly billing cycle [C1].\n\n"
        "## Activity Reflection\nActivity reflected quarterly [C2].\n\n"
        "## Report Producing\nUnknown.\n\n"
        "## Collateralisation Proofs\nUnknown.\n\n"
        "## Main Uncertainty\nUnknown.\n\n"
        "## Decision Needed\nReview ledger model [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Ledger and billing structure.\n"
        f"- Source: {source}\n- Quote: Activity recorded in the main ledger with monthly billing.\n"
        "### C2\n- Claim: Activity reflection period.\n"
        f"- Source: {source}\n- Quote: Activity reflected quarterly.\n"
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
        "# Demo BRD\nActivity recorded in the main ledger with monthly billing.\nActivity reflected quarterly.\n",
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


def test_unsupported_numeric_suffix_does_not_escape_validation(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nBilling amount is $10,000–$15,000.\nActivity reflected quarterly.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = finance_brief(str(brd)).replace(
        "Activity recorded in the main ledger [C1].", "Billing amount is $10M [C1]."
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_substring_is_not_a_supported_amount(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000–$15,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = finance_brief(str(brd)).replace("$10,000–$15,000 [C1].", "$10 [C1].")
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_period_must_match_the_cited_quote(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs $10,000 per year.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("$10,000–$15,000 [C1].", "$10,000 per month [C1].")
        .replace("Study costs $10,000–$15,000.", "Study costs $10,000 per year.")
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_currency_code_prefix_must_match_quote(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nStudy costs USD 10,000.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("$10,000–$15,000 [C1].", "EUR 10,000 [C1].")
        .replace("Study costs $10,000–$15,000.", "Study costs USD 10,000.")
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


@pytest.mark.parametrize(
    ("quoted", "asserted"),
    [("10 hours", "10 minutes"), ("$10 million", "$10 billion")],
)
def test_separated_unit_or_scale_must_match_quote(
    tmp_path: Path, quoted: str, asserted: str
) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        f"# Demo BRD\nStudy costs {quoted}.\nStudy duration is one quarter.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("$10,000–$15,000 [C1].", f"{asserted} [C1].")
        .replace("Study costs $10,000–$15,000.", f"Study costs {quoted}.")
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_plain_prose_after_amount_does_not_become_a_unit(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nBilling amount is $10,000 for the pilot.\nActivity reflected quarterly.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("Activity recorded in the main ledger [C1].", "Billing amount is $10,000 [C1].")
        .replace(
            "Activity recorded in the main ledger with monthly billing.",
            "Billing amount is $10,000 for the pilot.",
        )
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == response


def test_percent_is_not_supported_by_bare_number(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nBilling amount is 10.\nActivity reflected quarterly.\n", encoding="utf-8"
    )
    out = tmp_path / "demo.draft.md"
    response = (
        finance_brief(str(brd))
        .replace("Activity recorded in the main ledger [C1].", "Billing amount is 10% [C1].")
        .replace(
            "Activity recorded in the main ledger with monthly billing.",
            "Billing amount is 10.",
        )
    )
    result = run_finance(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "numeric literal" in result.stderr
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_draft_cannot_claim_approval_in_decision_layer(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nActivity recorded in the main ledger with monthly billing.\nActivity reflected quarterly.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = finance_brief(str(brd)).replace(
        "Review ledger model [C1].", "Finance approval granted [C1]."
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


def test_prompt_only_rejects_output_outside_configured_product_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import generate_finance_brief as finance_cli

    root = tmp_path / "product"
    root.mkdir()
    brd = root / "demo-brd.md"
    brd.write_text("# Demo BRD\nStudy costs $10,000–$15,000.\n", encoding="utf-8")
    out = tmp_path / "elsewhere" / "demo.draft.md"
    monkeypatch.setattr(
        finance_cli,
        "maybe_enforce_gate",
        lambda *args, **kwargs: {"root": str(root), "lanes": {}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_finance_brief.py", "--brd", str(brd), "--out", str(out), "--prompt-only"],
    )
    with pytest.raises(SystemExit, match="outside the review manifest product root"):
        finance_cli.main()
    assert not out.with_suffix(".prompt.md").exists()


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
