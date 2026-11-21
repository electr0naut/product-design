"""Behavior tests for scoped, version-bound stakeholder gates."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))


def normalize(doc: dict) -> dict:
    """Fill schema-v2 collections so fixtures stay focused on their subject."""
    doc["schema_version"] = 2
    for key in ("feedback_events", "change_events", "questions", "question_answers"):
        doc.setdefault(key, [])
    for change in doc.get("changes", []):
        change.pop("status", None)
        change.pop("resolved_at", None)
    for decision in doc.get("decisions", []):
        for comment in decision.get("feedback", []):
            comment.pop("status", None)
            comment.pop("resolution", None)
    return doc


def write_manifest(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(normalize(doc)), encoding="utf-8")


def manifest_fixture(root: Path) -> tuple[Path, dict]:
    (root / "review").mkdir()
    (root / "review" / "accounts.md").write_text("Accounts v1\n", encoding="utf-8")
    (root / "review" / "billing.md").write_text("Billing v1\n", encoding="utf-8")
    doc = {
        "schema_version": 1,
        "product": "demo",
        "gates": [
            {
                "id": "design-to-backlog",
                "lanes": {
                    "E01": {
                        "roles": ["product", "engineering"],
                        "artifacts": ["review/accounts.md"],
                        "depends_on": [],
                        "assumptions": [],
                        "epic": True,
                    },
                    "E02": {
                        "roles": ["product", "legal"],
                        "artifacts": ["review/billing.md"],
                        "depends_on": [{"gate": "design-to-backlog", "lane": "E01"}],
                        "assumptions": [],
                        "epic": True,
                    },
                },
            }
        ],
        "decisions": [],
        "changes": [],
        "assumptions": [],
    }
    path = root / "review" / "demo.json"
    return path, doc


def decide(root: Path, doc: dict, lane: str, role: str, *, decision: str = "approve") -> dict:
    artifact = f"review/{'accounts' if lane == 'E01' else 'billing'}.md"
    payload = {
        "id": f"D-{len(doc['decisions']) + 1:03}",
        "gate": "design-to-backlog",
        "lane": lane,
        "role": role,
        "reviewer": f"Reviewer ({role})",
        "decision": decision,
        "recorded_at": "2026-11-21T12:00:00Z",
        "artifact_sha256": {artifact: hashlib.sha256((root / artifact).read_bytes()).hexdigest()},
        "evidence": "review-ticket-001",
        "feedback": [],
    }
    doc["decisions"].append(payload)
    return payload


def check(root: Path, doc: dict, gate: str = "design-to-backlog", lane: str | None = None) -> dict:
    from gate_reviews import evaluate_gate

    path = root / "review" / "demo.json"
    write_manifest(path, doc)
    return evaluate_gate(path, gate, lane)


def test_approved_lane_proceeds_while_other_lane_waits():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decide(root, doc, "E01", "product")
        decide(root, doc, "E01", "engineering")
        result = check(root, doc)
        assert result["ready"] is False
        assert result["lanes"]["E01"]["ready"] is True
        assert result["lanes"]["E02"]["ready"] is False
        assert "missing approval: legal" in result["lanes"]["E02"]["reasons"]
        assert check(root, doc, lane="E01")["ready"] is True


def test_newer_negative_decision_and_unresolved_feedback_override_approval():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decide(root, doc, "E01", "product")
        engineer = decide(root, doc, "E01", "engineering")
        engineer["feedback"] = [{"id": "F-001", "text": "Confirm retention"}]
        result = check(root, doc, lane="E01")
        assert result["ready"] is False
        assert "unresolved feedback: engineering" in result["lanes"]["E01"]["reasons"]
        doc["feedback_events"].append(
            {
                "id": "FE-001",
                "feedback_id": "F-001",
                "action": "resolve",
                "text": "Documented in BR-001",
                "at": "2026-11-21T12:10:00Z",
                "by": "engineering",
                "evidence": "ticket-002",
            }
        )
        assert check(root, doc, lane="E01")["ready"] is True
        decide(root, doc, "E01", "engineering", decision="request_changes")
        result = check(root, doc, lane="E01")
        assert result["ready"] is False
        assert "not approved: engineering" in result["lanes"]["E01"]["reasons"]


def test_new_approval_cannot_hide_an_older_unresolved_comment():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decide(root, doc, "E01", "product")
        first = decide(root, doc, "E01", "engineering", decision="request_changes")
        first["feedback"].append({"id": "F-001", "text": "Fix this"})
        decide(root, doc, "E01", "engineering")
        assert (
            "unresolved feedback: engineering"
            in check(root, doc, lane="E01")["lanes"]["E01"]["reasons"]
        )
        doc["feedback_events"].append(
            {
                "id": "FE-001",
                "feedback_id": "F-001",
                "action": "resolve",
                "text": "Fixed in the reviewed artifact",
                "at": "2026-11-21T12:10:00Z",
                "by": "engineering",
                "evidence": "ticket-002",
            }
        )
        assert check(root, doc, lane="E01")["ready"] is True


def test_changed_artifact_blocks_its_lane_and_dependent_lane_only():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        for lane, roles in (("E01", ("product", "engineering")), ("E02", ("product", "legal"))):
            for role in roles:
                decide(root, doc, lane, role)
        assert check(root, doc)["ready"] is True
        (root / "review" / "accounts.md").write_text("Accounts v2\n", encoding="utf-8")
        result = check(root, doc)
        assert result["lanes"]["E01"]["ready"] is False
        assert result["lanes"]["E02"]["ready"] is False
        assert any("dependency" in reason for reason in result["lanes"]["E02"]["reasons"])


def test_change_requires_resolution_and_new_approval_only_in_affected_lane():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        for lane, roles in (("E01", ("product", "engineering")), ("E02", ("product", "legal"))):
            for role in roles:
                decide(root, doc, lane, role)
        change = {
            "id": "CHG-001",
            "source": "regulator-notice-001",
            "raised_at": "2026-11-21T12:30:00Z",
            "effective_at": "2026-12-01",
            "affected": [{"gate": "design-to-backlog", "lane": "E02"}],
        }
        doc["changes"].append(change)
        result = check(root, doc)
        assert result["lanes"]["E01"]["ready"] is True
        assert result["lanes"]["E02"]["ready"] is False
        assert "open change: CHG-001" in result["lanes"]["E02"]["reasons"]
        doc["change_events"].append(
            {
                "id": "CE-001",
                "change_id": "CHG-001",
                "action": "resolve",
                "text": "Scoped and documented",
                "at": "2026-11-21T12:45:00Z",
                "by": "legal",
                "evidence": "legal-memo-002",
            }
        )
        result = check(root, doc, lane="E02")
        assert (
            "reapproval required after change: CHG-001 (product)"
            in result["lanes"]["E02"]["reasons"]
        )
        for role in ("product", "legal"):
            decide(root, doc, "E02", role)["recorded_at"] = "2026-11-21T13:00:00Z"
        assert check(root, doc)["ready"] is True


def test_expired_assumption_blocks_only_scopes_that_reference_it():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        for lane, roles in (("E01", ("product", "engineering")), ("E02", ("product", "legal"))):
            for role in roles:
                decide(root, doc, lane, role)
        doc["assumptions"] = [
            {
                "id": "A-001",
                "statement": "Retention is 30 days",
                "source": "legal-memo-1",
                "checked_at": "2000-01-01",
                "review_by": "2001-01-01",
            }
        ]
        doc["gates"][0]["lanes"]["E02"]["assumptions"] = ["A-001"]
        result = check(root, doc)
        assert result["lanes"]["E01"]["ready"] is True
        assert "expired assumption: A-001" in result["lanes"]["E02"]["reasons"]


@pytest.mark.parametrize("artifact", ["../outside.md", "/etc/passwd", "review/link.md"])
def test_invalid_or_symlinked_artifact_is_rejected(artifact: str):
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        path, doc = manifest_fixture(root)
        if artifact == "review/link.md":
            (root / artifact).symlink_to(root / "review" / "accounts.md")
        doc["gates"][0]["lanes"]["E01"]["artifacts"] = [artifact]
        with pytest.raises(ValueError, match="artifact"):
            check(root, doc, lane="E01")


def test_dependency_cycle_is_rejected():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        doc["gates"][0]["lanes"]["E01"]["depends_on"] = [
            {"gate": "design-to-backlog", "lane": "E02"}
        ]
        with pytest.raises(ValueError, match="cycle"):
            check(root, doc, lane="E01")


@pytest.mark.parametrize(
    "flaw",
    ["empty_roles", "unknown_role", "bad_hash", "bad_decision", "unknown_change", "bad_feedback"],
)
def test_invalid_review_records_fail_closed(flaw: str):
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decision = decide(root, doc, "E01", "product")
        if flaw == "empty_roles":
            doc["gates"][0]["lanes"]["E01"]["roles"] = []
        elif flaw == "unknown_role":
            decision["role"] = "stranger"
        elif flaw == "bad_hash":
            decision["artifact_sha256"]["review/accounts.md"] = "123"
        elif flaw == "bad_decision":
            decision["decision"] = "waived"
        elif flaw == "unknown_change":
            doc["changes"] = [
                {
                    "id": "CHG-001",
                    "source": "notice",
                    "raised_at": "2026-11-21T12:30:00Z",
                    "effective_at": "2026-12-01",
                    "status": "open",
                    "affected": [{"gate": "missing", "lane": "E01"}],
                }
            ]
        elif flaw == "bad_feedback":
            decision["feedback"].append({"id": "F-1", "text": "", "status": "resolved"})
        with pytest.raises(ValueError):
            check(root, doc, lane="E01")


def test_not_applicable_never_silently_counts_as_required_approval():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decide(root, doc, "E01", "product")
        decide(root, doc, "E01", "engineering", decision="not_applicable")
        assert check(root, doc, lane="E01")["ready"] is False


def test_cli_exposes_pending_roles_and_scoped_artifacts_for_future_portal():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        decide(root, doc, "E01", "product")
        write_manifest(manifest, doc)
        command = [
            sys.executable,
            str(SCRIPTS / "check_gate.py"),
            "--manifest",
            str(manifest),
            "--gate",
            "design-to-backlog",
            "--lane",
            "E01",
            "--json",
        ]
        blocked = subprocess.run(command, text=True, capture_output=True, check=False)
        assert blocked.returncode == 1
        result = json.loads(blocked.stdout)
        assert result["lanes"]["E01"]["required_roles"] == ["product", "engineering"]
        assert result["lanes"]["E01"]["artifacts"] == ["review/accounts.md"]
        assert result["lanes"]["E01"]["decisions"]["product"]["decision"] == "approve"
        decide(root, doc, "E01", "engineering")
        write_manifest(manifest, doc)
        ready = subprocess.run(command, text=True, capture_output=True, check=False)
        assert ready.returncode == 0
        assert json.loads(ready.stdout)["ready"] is True


def test_prd_generation_refuses_blocked_gate_and_requires_its_real_source():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "03-brd").mkdir()
        brd = root / "03-brd" / "demo-brd.md"
        brd.write_text("# BRD\n", encoding="utf-8")
        doc["gates"] = [
            {
                "id": "brd-to-prd",
                "lanes": {
                    "all": {
                        "roles": ["product"],
                        "artifacts": ["03-brd/demo-brd.md"],
                        "depends_on": [],
                        "assumptions": [],
                    }
                },
            }
        ]
        write_manifest(manifest, doc)
        output = root / "04-prd" / "demo-prd.prompt.md"
        command = [
            sys.executable,
            str(SCRIPTS / "generate_prd.py"),
            "--brd",
            str(brd),
            "--out",
            str(root / "04-prd" / "demo-prd.md"),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        blocked = subprocess.run(command, text=True, capture_output=True, check=False)
        assert blocked.returncode != 0
        assert not output.exists()
        doc["gates"][0]["lanes"]["all"]["artifacts"] = ["review/accounts.md"]
        write_manifest(manifest, doc)
        not_the_source = subprocess.run(command, text=True, capture_output=True, check=False)
        assert not_the_source.returncode != 0
        assert not output.exists()
        doc["gates"][0]["lanes"]["all"]["artifacts"] = ["03-brd/demo-brd.md"]
        doc["decisions"].append(
            {
                "id": "D-001",
                "gate": "brd-to-prd",
                "lane": "all",
                "role": "product",
                "reviewer": "Owner",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {
                    "03-brd/demo-brd.md": hashlib.sha256(brd.read_bytes()).hexdigest()
                },
                "evidence": "review-ticket-001",
                "feedback": [],
            }
        )
        write_manifest(manifest, doc)
        allowed = subprocess.run(command, text=True, capture_output=True, check=False)
        assert allowed.returncode == 0, allowed.stderr
        assert output.exists()


def test_backlog_expands_only_approved_epic_and_draft_override_is_explicit():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "04-prd").mkdir()
        (root / "05-technical-design").mkdir()
        prd = root / "04-prd" / "demo-prd.md"
        prd.write_text(
            "### E01: Accounts\n| ID | Story | Persona | Traces to | Priority |\n"
            "|----|-------|---------|-----------|----------|\n"
            "| US-001 | Create account | User | BR-001 | Must |\n\n"
            "### E02: Billing\n| ID | Story | Persona | Traces to | Priority |\n"
            "|----|-------|---------|-----------|----------|\n"
            "| US-002 | Pay bill | User | BR-002 | Must |\n",
            encoding="utf-8",
        )
        design = root / "05-technical-design" / "demo-technical-design.md"
        design.write_text("# Design\n", encoding="utf-8")
        for lane in ("E01", "E02"):
            doc["gates"][0]["lanes"][lane]["artifacts"] = [
                "04-prd/demo-prd.md",
                "05-technical-design/demo-technical-design.md",
            ]
        decide(root, doc, "E01", "product")
        decide(root, doc, "E01", "engineering")
        for decision in doc["decisions"]:
            decision["artifact_sha256"] = {
                "04-prd/demo-prd.md": hashlib.sha256(prd.read_bytes()).hexdigest(),
                "05-technical-design/demo-technical-design.md": hashlib.sha256(
                    design.read_bytes()
                ).hexdigest(),
            }
        write_manifest(manifest, doc)
        out = root / "06-backlog" / "demo"
        command = [
            sys.executable,
            str(SCRIPTS / "generate_stories.py"),
            "--prd",
            str(prd),
            "--technical-design",
            str(design),
            "--out-dir",
            str(out),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        all_epics = subprocess.run(command, text=True, capture_output=True, check=False)
        assert all_epics.returncode != 0
        assert not out.exists()
        accounts = subprocess.run(
            [*command, "--epic", "E01"], text=True, capture_output=True, check=False
        )
        assert accounts.returncode == 0, accounts.stderr
        assert (out / "prompts" / "E01-accounts.prompt.md").exists()
        billing = subprocess.run(
            [*command, "--epic", "E02"], text=True, capture_output=True, check=False
        )
        assert billing.returncode != 0
        assert not (out / "prompts" / "E02-billing.prompt.md").exists()
        refused = subprocess.run(
            [*command, "--epic", "E02", "--draft"], text=True, capture_output=True, check=False
        )
        assert refused.returncode != 0
        assert "--draft refuses" in refused.stderr
        draft_out = out.with_name(out.name + ".draft")
        draft_command = [str(draft_out) if item == str(out) else item for item in command]
        draft = subprocess.run(
            [*draft_command, "--epic", "E02", "--draft"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert draft.returncode == 0, draft.stderr
        assert "DRAFT ONLY" in draft.stderr
        assert (draft_out / "prompts" / "E02-billing.prompt.md").exists()
        assert not (out / "prompts" / "E02-billing.prompt.md").exists()


@pytest.mark.parametrize(
    "phase,script,source_dir,source_name,extra",
    [
        (
            "ideation-to-analysis",
            "generate_analysis.py",
            "01-ideation",
            "demo.md",
            ["--role", "legal"],
        ),
        ("analysis-to-brd", "generate_brd.py", "01-ideation", "demo.md", []),
        ("prd-to-design", "generate_technical_design.py", "04-prd", "demo-prd.md", []),
    ],
)
def test_other_generation_phases_require_configured_reviews(
    phase, script, source_dir, source_name, extra
):
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / source_dir).mkdir()
        source = root / source_dir / source_name
        source.write_text("# Source\n", encoding="utf-8")
        sources = [source]
        if phase == "analysis-to-brd":
            (root / "02-analysis").mkdir()
            for role in (
                "bizdev",
                "compliance",
                "finance",
                "legal",
                "operations",
                "product",
                "risk",
            ):
                analysis = root / "02-analysis" / f"demo-{role}-analysis.md"
                analysis.write_text("# Analysis\n", encoding="utf-8")
                sources.append(analysis)
        lane = "legal" if phase == "ideation-to-analysis" else "all"
        doc["gates"] = [
            {
                "id": phase,
                "lanes": {
                    lane: {
                        "roles": ["owner"],
                        "artifacts": [str(s.relative_to(root)) for s in sources],
                        "depends_on": [],
                        "assumptions": [],
                    }
                },
            }
        ]
        write_manifest(manifest, doc)
        out = root / "result.md"
        flag = {
            "ideation-to-analysis": "--idea",
            "analysis-to-brd": "--idea",
            "prd-to-design": "--prd",
        }[phase]
        command = [
            sys.executable,
            str(SCRIPTS / script),
            flag,
            str(source),
            "--review-manifest",
            str(manifest),
            "--prompt-only",
            *extra,
        ]
        if phase == "analysis-to-brd":
            command += ["--analysis", str(root / "02-analysis")]
        if phase == "ideation-to-analysis":
            command += ["--out-dir", str(root / "02-analysis")]
            out = root / "02-analysis" / "legal" / "demo-legal-analysis.prompt.md"
        else:
            target = (
                root / "03-brd" / "demo-brd.md"
                if phase == "analysis-to-brd"
                else root / "05-technical-design" / "architecture" / "demo-technical-design.md"
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            command += ["--out", str(target)]
            out = target.with_suffix(".prompt.md")
        assert subprocess.run(command, text=True, capture_output=True, check=False).returncode != 0
        assert not out.exists()
        approved = {
            "id": "D-001",
            "gate": phase,
            "lane": lane,
            "role": "owner",
            "reviewer": "Owner",
            "decision": "approve",
            "recorded_at": "2026-11-21T12:00:00Z",
            "artifact_sha256": {
                str(s.relative_to(root)): hashlib.sha256(s.read_bytes()).hexdigest()
                for s in sources
            },
            "evidence": "ticket-001",
            "feedback": [],
        }
        doc["decisions"] = [approved]
        write_manifest(manifest, doc)
        result = subprocess.run(command, text=True, capture_output=True, check=False)
        assert result.returncode == 0, result.stderr
        assert out.exists()


def test_partial_brd_cannot_claim_gate_release_even_if_subset_was_approved():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "01-ideation").mkdir()
        (root / "02-analysis").mkdir()
        idea = root / "01-ideation" / "demo.md"
        analysis = root / "02-analysis" / "demo-legal-analysis.md"
        idea.write_text("# Idea\n", encoding="utf-8")
        analysis.write_text("# Legal\n", encoding="utf-8")
        paths = ["01-ideation/demo.md", "02-analysis/demo-legal-analysis.md"]
        doc["gates"] = [
            {
                "id": "analysis-to-brd",
                "lanes": {
                    "all": {
                        "roles": ["owner"],
                        "artifacts": paths,
                        "depends_on": [],
                        "assumptions": [],
                    }
                },
            }
        ]
        doc["decisions"] = [
            {
                "id": "D-001",
                "gate": "analysis-to-brd",
                "lane": "all",
                "role": "owner",
                "reviewer": "Owner",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {
                    p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in paths
                },
                "evidence": "ticket-001",
                "feedback": [],
            }
        ]
        write_manifest(manifest, doc)
        output = root / "03-brd" / "demo-brd.prompt.md"
        command = [
            sys.executable,
            str(SCRIPTS / "generate_brd.py"),
            "--idea",
            str(idea),
            "--analysis",
            str(root / "02-analysis"),
            "--out",
            str(root / "03-brd" / "demo-brd.md"),
            "--allow-partial-analysis",
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        blocked = subprocess.run(command, capture_output=True, text=True, check=False)
        assert blocked.returncode != 0
        assert not output.exists()
        draft_out = root / "03-brd" / "demo-brd.draft.md"
        draft_command = [
            str(draft_out) if item == str(root / "03-brd" / "demo-brd.md") else item
            for item in command
        ]
        draft = subprocess.run(
            [*draft_command, "--draft"], capture_output=True, text=True, check=False
        )
        assert draft.returncode == 0, draft.stderr
        assert "DRAFT ONLY" in draft.stderr
        assert (root / "03-brd" / "demo-brd.draft.prompt.md").exists()
        assert not output.exists()


def test_duplicate_json_keys_are_rejected():
    from gate_reviews import load_manifest

    raw = (
        '{"schema_version": 1, "product": "demo", "product": "demo", "gates": ['
        '{"id": "g", "lanes": {"E01": {"roles": ["a"], "artifacts": ["x.md"],'
        ' "depends_on": [], "assumptions": []}}}],'
        ' "decisions": [], "changes": [], "assumptions": []}'
    )
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        manifest = Path(name) / "review" / "demo.json"
        manifest.parent.mkdir()
        manifest.write_text(raw, encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate"):
            load_manifest(manifest)


def test_duplicate_keys_inside_one_record_are_rejected():
    from gate_reviews import load_manifest

    raw = (
        '{"schema_version": 1, "product": "demo", "gates": [{"id": "g", "lanes": '
        '{"E01": {"roles": ["a"], "roles": ["b"], "artifacts": ["x.md"], "depends_on": [],'
        ' "assumptions": []}}}], "decisions": [], "changes": [], "assumptions": []}'
    )
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        manifest = Path(name) / "review" / "demo.json"
        manifest.parent.mkdir()
        manifest.write_text(raw, encoding="utf-8")
        with pytest.raises(ValueError, match="duplicate"):
            load_manifest(manifest)


def test_whole_gate_check_includes_non_epic_cross_cutting_lane():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "04-prd").mkdir()
        (root / "05-technical-design").mkdir()
        prd = root / "04-prd" / "demo-prd.md"
        prd.write_text(
            "### E01: Accounts\n| ID | Story | Persona | Traces to | Priority |\n"
            "|----|-------|---------|-----------|----------|\n"
            "| US-001 | Create account | User | BR-001 | Must |\n",
            encoding="utf-8",
        )
        design = root / "05-technical-design" / "demo-technical-design.md"
        design.write_text("# Design\n", encoding="utf-8")
        shared = ["04-prd/demo-prd.md", "05-technical-design/demo-technical-design.md"]
        doc["gates"][0]["lanes"].pop("E02")
        doc["gates"][0]["lanes"]["E01"]["artifacts"] = shared
        doc["gates"][0]["lanes"]["security"] = {
            "roles": ["security"],
            "artifacts": shared,
            "depends_on": [],
            "assumptions": [],
        }
        for role in ("product", "engineering"):
            decide(root, doc, "E01", role)
        for decision in doc["decisions"]:
            decision["artifact_sha256"] = {
                p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in shared
            }
        write_manifest(manifest, doc)
        out = root / "06-backlog" / "demo"
        base = [
            sys.executable,
            str(SCRIPTS / "generate_stories.py"),
            "--prd",
            str(prd),
            "--technical-design",
            str(design),
            "--out-dir",
            str(out),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        whole = subprocess.run(base, capture_output=True, text=True, check=False)
        assert whole.returncode != 0
        assert "security" in whole.stdout + whole.stderr
        scoped = subprocess.run(
            [*base, "--epic", "E01"], capture_output=True, text=True, check=False
        )
        assert scoped.returncode != 0
        assert "security" in scoped.stdout + scoped.stderr
        assert not (out / "prompts" / "E01-accounts.prompt.md").exists()


def test_renamed_input_copy_cannot_bypass_the_products_gate():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "04-prd").mkdir()
        original = root / "04-prd" / "demo-prd.md"
        original.write_text("# PRD\n", encoding="utf-8")
        copy = root / "04-prd" / "demo-copy-prd.md"
        copy.write_text("# PRD\n", encoding="utf-8")
        doc["gates"][0]["lanes"]["all"] = {
            "roles": ["product"],
            "artifacts": ["04-prd/demo-prd.md"],
            "depends_on": [],
            "assumptions": [],
        }
        write_manifest(manifest, doc)
        command = [
            sys.executable,
            str(SCRIPTS / "generate_technical_design.py"),
            "--prd",
            str(copy),
            "--out",
            str(root / "05-technical-design" / "demo-technical-design.md"),
            "--prompt-only",
        ]
        blocked = subprocess.run(command, capture_output=True, text=True, check=False)
        assert blocked.returncode != 0
        assert not (root / "05-technical-design" / "demo-technical-design.prompt.md").exists()


def test_explicit_manifest_must_name_the_product_being_generated():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "03-brd").mkdir()
        brd = root / "03-brd" / "other-brd.md"
        brd.write_text("# BRD\n", encoding="utf-8")
        write_manifest(manifest, doc)
        command = [
            sys.executable,
            str(SCRIPTS / "generate_prd.py"),
            "--brd",
            str(brd),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode != 0
        assert "product" in (result.stdout + result.stderr).lower()


def test_unknown_gate_and_lane_report_actionable_errors():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        write_manifest(manifest, doc)
        from gate_reviews import evaluate_gate

        with pytest.raises(ValueError, match="unknown gate"):
            evaluate_gate(manifest, "no-such-gate")
        with pytest.raises(ValueError, match="unknown lane"):
            evaluate_gate(manifest, "design-to-backlog", "E99")


def test_future_decision_timestamp_is_rejected():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        decision = decide(root, doc, "E01", "product")
        decision["recorded_at"] = "2999-01-01T00:00:00Z"
        with pytest.raises(ValueError, match="future"):
            check(root, doc, lane="E01")


def test_cycle_between_unselected_lanes_is_still_rejected():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        _, doc = manifest_fixture(root)
        doc["gates"][0]["lanes"]["E01"]["depends_on"] = [
            {"gate": "design-to-backlog", "lane": "E02"}
        ]
        doc["gates"][0]["lanes"]["E02"]["depends_on"] = [
            {"gate": "design-to-backlog", "lane": "E01"}
        ]
        doc["gates"][0]["lanes"]["other"] = {
            "roles": ["owner"],
            "artifacts": ["review/accounts.md"],
            "depends_on": [],
            "assumptions": [],
        }
        with pytest.raises(ValueError, match="cycle"):
            check(root, doc, lane="other")


def test_sources_split_across_lanes_bundle_without_false_staleness():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "04-prd").mkdir()
        (root / "05-technical-design").mkdir()
        prd = root / "04-prd" / "demo-prd.md"
        prd.write_text(
            "### E01: Accounts\n| ID | Story | Persona | Traces to | Priority |\n"
            "|----|-------|---------|-----------|----------|\n"
            "| US-001 | Create account | User | BR-001 | Must |\n\n"
            "### E02: Billing\n| ID | Story | Persona | Traces to | Priority |\n"
            "|----|-------|---------|-----------|----------|\n"
            "| US-002 | Pay bill | User | BR-002 | Must |\n",
            encoding="utf-8",
        )
        design = root / "05-technical-design" / "demo-technical-design.md"
        design.write_text("# Design\n", encoding="utf-8")
        doc["gates"][0]["lanes"]["E01"]["artifacts"] = ["04-prd/demo-prd.md"]
        doc["gates"][0]["lanes"]["E02"]["artifacts"] = [
            "05-technical-design/demo-technical-design.md"
        ]
        for lane in ("E01", "E02"):
            for role in doc["gates"][0]["lanes"][lane]["roles"]:
                decide(root, doc, lane, role)
        for decision in doc["decisions"]:
            lane = decision["lane"]
            artifacts = doc["gates"][0]["lanes"][lane]["artifacts"]
            decision["artifact_sha256"] = {
                p: hashlib.sha256((root / p).read_bytes()).hexdigest() for p in artifacts
            }
        write_manifest(manifest, doc)
        out = root / "06-backlog" / "demo"
        command = [
            sys.executable,
            str(SCRIPTS / "generate_stories.py"),
            "--prd",
            str(prd),
            "--technical-design",
            str(design),
            "--out-dir",
            str(out),
            "--prompt-only",
            "--review-manifest",
            str(manifest),
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode == 0, result.stderr
        assert (out / "prompts" / "E01-accounts.prompt.md").exists()


def test_output_product_manifest_is_enforced_over_the_input_products():
    with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as name:
        root = Path(name)
        manifest, doc = manifest_fixture(root)
        (root / "03-brd").mkdir()
        brd = root / "03-brd" / "demo-brd.md"
        brd.write_text("# BRD\n", encoding="utf-8")
        doc["gates"] = [
            {
                "id": "brd-to-prd",
                "lanes": {
                    "all": {
                        "roles": ["product"],
                        "artifacts": ["03-brd/demo-brd.md"],
                        "depends_on": [],
                        "assumptions": [],
                    }
                },
            }
        ]
        doc["decisions"] = [
            {
                "id": "D-001",
                "gate": "brd-to-prd",
                "lane": "all",
                "role": "product",
                "reviewer": "Owner",
                "decision": "approve",
                "recorded_at": "2026-11-21T12:00:00Z",
                "artifact_sha256": {
                    "03-brd/demo-brd.md": hashlib.sha256(brd.read_bytes()).hexdigest()
                },
                "evidence": "ticket-001",
                "feedback": [],
            }
        ]
        write_manifest(manifest, doc)
        other = dict(doc)
        other["product"] = "other"
        other["decisions"] = []
        write_manifest(root / "review" / "other.json", other)
        command = [
            sys.executable,
            str(SCRIPTS / "generate_prd.py"),
            "--brd",
            str(brd),
            "--out",
            str(root / "04-prd" / "other-prd.md"),
            "--prompt-only",
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        assert result.returncode != 0
        assert "other" in result.stdout + result.stderr
