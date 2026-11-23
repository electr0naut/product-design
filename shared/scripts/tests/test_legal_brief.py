"""Legal decision brief integration tests."""

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


def legal_brief(source: str) -> str:
    return (
        "# Legal Decision Brief: Demo\n\n"
        "Draft for human review; not a legal conclusion.\n\n"
        "## Claim Relied On\nConsent is required [C1].\n\n"
        "## Citation\nGDPR Art. 6(1)(a) [C1].\n\n"
        "## Jurisdiction\nEU [C1].\n\n"
        "## Main Legal Risk\nUnknown.\n\n"
        "## Decision Needed\nConsent required [C1].\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Consent requirement.\n"
        f"- Source: {source}\n- Quote: Consent required under GDPR Art. 6(1)(a) in the EU.\n"
    )


def run_legal(brd: Path, out: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "generate_legal_brief.py"),
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


def test_valid_legal_brief_is_a_draft_with_provenance(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    expected = legal_brief(str(brd))
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, expected))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == expected
    sidecar = json.loads(out.with_suffix(".provenance.json").read_text(encoding="utf-8"))
    assert sidecar["inputs"][0]["path"] == str(brd)
    assert sidecar["output_review_status"]["status"] == "draft"
    assert sidecar["input_gate_readiness"] is None


def test_unsupported_citation_is_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace("GDPR Art. 6(1)(a) [C1].", "CCPA §1798.100 [C1].")
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_unsupported_jurisdiction_is_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace("EU [C1].", "US [C1].")
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_citation_must_match_complete_token(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 60(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace(
            "- Quote: Consent required under GDPR Art. 6(1)(a) in the EU.",
            "- Quote: Consent required under GDPR Art. 60(1)(a) in the EU.",
        )
        .replace("GDPR Art. 6(1)(a) [C1].", "GDPR Art. 6 [C1].")
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_hyphenated_citation_must_match_quote(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6-1 in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace(
            "- Quote: Consent required under GDPR Art. 6(1)(a) in the EU.",
            "- Quote: Consent required under GDPR Art. 6-1 in the EU.",
        )
        .replace("GDPR Art. 6(1)(a) [C1].", "GDPR Art. 6-2 [C1].")
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_adjacent_abbreviations_are_checked_separately(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under EU GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace(
            "- Quote: Consent required under GDPR Art. 6(1)(a) in the EU.",
            "- Quote: Consent required under EU GDPR Art. 6(1)(a) in the EU.",
        )
        .replace(
            "## Citation\nGDPR Art. 6(1)(a) [C1].",
            "## Citation\nEU GDPR Art. 6(1)(a) [C1].",
        )
        .replace(
            "## Claim Relied On\nConsent is required [C1].",
            "## Claim Relied On\nEU consent is required [C1].",
        )
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == response


def test_paraphrased_claim_is_supported_by_cited_quote(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "## Claim Relied On\nConsent is required [C1].",
        "## Claim Relied On\nThe requirement is consent [C1].",
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == response


def test_titlecase_jurisdiction_is_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "## Jurisdiction\nEU [C1].", "## Jurisdiction\nCA [C1]."
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "jurisdiction" in result.stderr.lower() or "citation" in result.stderr.lower()
    assert not out.exists()


def test_citation_subsection_must_match_quote(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace("GDPR Art. 6(1)(a) [C1].", "GDPR Art. 6(1)(b) [C1].")
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_unknown_must_fill_the_section(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "## Jurisdiction\nEU [C1].",
        "## Jurisdiction\nUnknown.\nEU [C1].",
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert not out.exists()


def test_card_claim_cannot_assert_approval(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "- Claim: Consent requirement.", "- Claim: Legal approval granted."
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert not out.exists()


def test_draft_cannot_claim_approval_in_decision_layer(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "Consent required [C1].", "Legal approval granted [C1]."
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "approval" in result.stderr.lower()
    assert not out.exists()


@pytest.mark.parametrize(
    "change",
    [
        lambda text: text.replace(
            "- Quote: Consent required under GDPR Art. 6(1)(a) in the EU.",
            "- Quote: Invented citation.",
        ),
        lambda text: text.replace("- Source: ", "- Source: other.md "),
        lambda text: text.replace("[C1]", "[C3]"),
        lambda text: text.replace("### C1", "### C1\n### C1"),
    ],
)
def test_unsourced_or_malformed_claims_leave_no_files(tmp_path: Path, change) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    result = run_legal(
        brd, out, "--claude-bin", fake_model(tmp_path, change(legal_brief(str(brd))))
    )
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_prompt_only_rejects_output_outside_configured_product_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.syspath_prepend(str(SCRIPTS))
    import generate_legal_brief as legal_cli

    root = tmp_path / "product"
    root.mkdir()
    brd = root / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "elsewhere" / "demo.draft.md"
    monkeypatch.setattr(
        legal_cli,
        "maybe_enforce_gate",
        lambda *args, **kwargs: {"root": str(root), "lanes": {}},
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["generate_legal_brief.py", "--brd", str(brd), "--out", str(out), "--prompt-only"],
    )
    with pytest.raises(SystemExit, match="outside the review manifest product root"):
        legal_cli.main()
    assert not out.with_suffix(".prompt.md").exists()


def test_prompt_only_excludes_sibling_and_has_no_sidecar(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    (tmp_path / "demo-v2-brd.md").write_text("PRIVATE SIBLING", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    result = run_legal(brd, out, "--prompt-only")
    assert result.returncode == 0, result.stderr
    prompt = out.with_suffix(".prompt.md")
    text = prompt.read_text(encoding="utf-8")
    assert "Consent required under GDPR Art. 6(1)(a) in the EU." in text
    assert "PRIVATE SIBLING" not in text
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


@pytest.mark.parametrize("name", ["demo.md", "other.draft.md"])
def test_canonical_or_other_product_output_is_rejected(tmp_path: Path, name: str) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    out = tmp_path / name
    result = run_legal(brd, out, "--prompt-only")
    assert result.returncode != 0
    assert not out.exists()
    assert not out.with_suffix(".prompt.md").exists()


def test_existing_document_is_preserved_without_force(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text("# Demo BRD\n", encoding="utf-8")
    out = tmp_path / "demo.draft.md"
    out.write_text("Human-reviewed draft", encoding="utf-8")
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, "Invalid"))
    assert result.returncode == 0, result.stderr
    assert out.read_text(encoding="utf-8") == "Human-reviewed draft"
    assert not out.with_suffix(".provenance.json").exists()


def test_blocked_manifest_rejects_legal_generation(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
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
                                "roles": ["legal"],
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
    model = fake_model(tmp_path, legal_brief(str(brd)))
    result = run_legal(brd, out, "--review-manifest", str(manifest), "--claude-bin", model)
    assert result.returncode != 0
    assert "blocked" in result.stderr.lower()
    assert not out.exists()
    assert not out.with_suffix(".provenance.json").exists()


def test_titlecase_country_absent_from_quote_is_rejected(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in the EU.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = legal_brief(str(brd)).replace(
        "## Jurisdiction\nEU [C1].", "## Jurisdiction\nCanada [C1]."
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "canada" in result.stderr.lower()
    assert not out.exists()


def test_titlecase_country_present_in_quote_is_accepted(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nConsent required under GDPR Art. 6(1)(a) in Canada.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace(
            "Consent required under GDPR Art. 6(1)(a) in the EU.",
            "Consent required under GDPR Art. 6(1)(a) in Canada.",
        )
        .replace("## Jurisdiction\nEU [C1].", "## Jurisdiction\nCanada [C1].")
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert "## Jurisdiction\nCanada [C1]." in out.read_text(encoding="utf-8")


def test_citation_followed_by_sentence_period_is_accepted(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        """# Demo BRD
In the EU, consent required under GDPR Art. 6-1.
""",
        encoding="utf-8",
    )
    response = (
        "# Legal Decision Brief: Demo\n\n"
        "Draft for human review; not a legal conclusion.\n\n"
        "## Claim Relied On\nConsent required [C1].\n\n"
        "## Citation\nGDPR Art. 6-1 [C1].\n\n"
        "## Jurisdiction\nEU [C1].\n\n"
        "## Main Legal Risk\nRisk under GDPR Art. 6-1 [C1].\n\n"
        "## Decision Needed\nUnknown.\n\n"
        "## Evidence Cards\n"
        "### C1\n- Claim: Consent requirement.\n"
        f"- Source: {brd}\n- Quote: In the EU, consent required under GDPR Art. 6-1.\n"
    )
    out = tmp_path / "demo.draft.md"
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr


def test_declared_citation_cannot_pass_as_a_prefix(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nIn the EU, consent required under GDPR Art. 6-1.\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace("## Citation\nGDPR Art. 6(1)(a) [C1].", "## Citation\nGDPR Art. 6 [C1].")
        .replace(
            "Consent required under GDPR Art. 6(1)(a) in the EU.",
            "In the EU, consent required under GDPR Art. 6-1.",
        )
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "not in a cited brd quote" in result.stderr.lower()
    assert not out.exists()


def test_declared_citation_cannot_drop_a_subsection(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nIn the EU, consent required under GDPR Art. 6(1)(a).\n",
        encoding="utf-8",
    )
    out = tmp_path / "demo.draft.md"
    response = (
        legal_brief(str(brd))
        .replace("## Citation\nGDPR Art. 6(1)(a) [C1].", "## Citation\nGDPR Art. 6(1) [C1].")
        .replace(
            "Consent required under GDPR Art. 6(1)(a) in the EU.",
            "In the EU, consent required under GDPR Art. 6(1)(a).",
        )
    )
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode != 0
    assert "not in a cited brd quote" in result.stderr.lower()
    assert not out.exists()


def test_citation_mid_sentence_is_accepted(tmp_path: Path) -> None:
    brd = tmp_path / "demo-brd.md"
    brd.write_text(
        "# Demo BRD\nGDPR Art. 6(1)(a). This applies in the EU.\n",
        encoding="utf-8",
    )
    response = (
        legal_brief(str(brd))
        .replace(
            "Consent required under GDPR Art. 6(1)(a) in the EU.",
            "GDPR Art. 6(1)(a). This applies in the EU.",
        )
        .replace(
            "## Claim Relied On\nConsent is required [C1].",
            "## Claim Relied On\nConsent is required [C1].",
        )
    )
    out = tmp_path / "demo.draft.md"
    result = run_legal(brd, out, "--claude-bin", fake_model(tmp_path, response))
    assert result.returncode == 0, result.stderr
    assert "## Citation\nGDPR Art. 6(1)(a) [C1]." in out.read_text(encoding="utf-8")
