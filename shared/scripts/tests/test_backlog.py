"""Tests for the backlog parser, checks and the generation scripts.

Run with: python -m unittest discover shared/scripts/tests
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

from backlog import (  # noqa: E402
    Story,
    check_backlog,
    load_stories,
    parse_frontmatter,
    parse_requirements,
    parse_story_map,
    split_stories,
)
from workflow_common import markdown_files  # noqa: E402

BRD = textwrap.dedent(
    """\
    # Business Requirements Document: Invoicer

    ### 4.1 Functional Requirements
    | ID | Requirement | Priority | Source |
    |----|------------|----------|--------|
    | BR-001 | Users can create an account | Must | product |
    | BR-002 | Users can pay invoices by card | Must | finance |
    | BR-003 | Admins can export reports | Could | operations |

    ### 4.2 Non-Functional Requirements
    | ID | Requirement | Category | Target |
    |----|------------|----------|--------|
    | NFR-001 | Card data is never stored | Security | PCI SAQ-A |
    """
)

PRD = textwrap.dedent(
    """\
    # Product Requirements Document: Invoicer

    ## 1. Overview
    ### 1.2 Goals & Non-Goals
    **Goals:**
    - Get paid faster

    **Non-Goals:**
    - Report export (BR-003) waits until after the MVP.

    ## 3. Epics & Story Map

    ### E01: Accounts
    **Goal:** People can get in.
    **Traces to:** BR-001

    | ID | Story | Persona | Traces to | Priority |
    |----|-------|---------|-----------|----------|
    | US-001 | As a freelancer, I want to sign up with email, so that I can send invoices. | Freelancer | BR-001 | Must |
    | **US-002** | As a freelancer, I want to verify my email, so that my account is trusted. | Freelancer | BR-001 | Should |

    ### E02: Billing

    | ID | Story | Persona | Traces to | Priority |
    |----|-------|---------|-----------|----------|
    | US-003 | As a client, I want to pay an invoice by card, so that I pay quickly. | Client | BR-002, NFR-001 | Must Have |

    ## 4. Functional Specifications
    Nothing here yet.
    """
)

DESIGN = "# Technical Design: Invoicer\n\nComponents: auth-service, billing-service, users-table.\n"


def story_text(
    sid: str,
    title: str,
    epic: str,
    traces: str,
    depends: str = "",
    priority: str = "Must",
    estimate: str = "M",
) -> str:
    return textwrap.dedent(
        f"""\
        ---
        id: {sid}
        title: {title}
        epic: {epic}
        traces_to: [{traces}]
        depends_on: [{depends}]
        components: [auth-service]
        priority: {priority}
        estimate: {estimate}
        status: Draft
        ---

        # {sid}: {title}

        **As a** freelancer, **I want** this, **so that** that.

        ## Acceptance Criteria
        - [ ] Given a visitor, when they submit the form, then an account exists
        - [ ] Given a used email, when they submit, then they see an error

        ## Technical Notes
        - auth-service

        ## Tasks
        - [ ] Add the endpoint

        ## Open Questions
        - None
        """
    )


RESPONSES = {
    "E01": "Here are the stories for E01:\n\n<!-- story: US-001 -->\n"
    + story_text("US-001", "Sign up with email", "E01", "BR-001")
    + "\n<!-- story: US-002 -->\n```markdown\n"
    + story_text("US-002", "Verify email address", "E01", "BR-001", "US-001", "Should")
    + "```\n",
    "E02": "<!-- story: US-003 -->\n"
    + story_text(
        "US-003", "Pay an invoice by card (café test)", "E02", "BR-002, NFR-001", "US-001"
    ),
}

FAKE_CLAUDE = textwrap.dedent(
    """\
    import json, re, sys
    prompt = sys.stdin.buffer.read().decode("utf-8")
    responses = json.loads(open(sys.argv[1], encoding="utf-8").read())
    epic = re.search(r"Expand only epic (E\\d+)", prompt).group(1)
    sys.stdout.buffer.write(responses[epic].encode("utf-8"))
    """
)


def run_script(name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / name), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


class ParsingTests(unittest.TestCase):
    def test_requirements(self):
        requirements = parse_requirements(BRD)
        self.assertEqual(list(requirements), ["BR-001", "BR-002", "BR-003", "NFR-001"])
        self.assertEqual(requirements["BR-002"].text, "Users can pay invoices by card")

    def test_story_map(self):
        story_map = parse_story_map(PRD)
        self.assertEqual(list(story_map.epics), ["E01", "E02"])
        self.assertEqual(story_map.epics["E01"].name, "Accounts")
        self.assertEqual([s.id for s in story_map.epics["E01"].stories], ["US-001", "US-002"])
        us3 = story_map.stories["US-003"]
        self.assertEqual(us3.epic, "E02")
        self.assertEqual(us3.traces_to, ["BR-002", "NFR-001"])
        self.assertEqual(us3.persona, "Client")
        self.assertEqual(us3.priority, "Must Have")
        self.assertEqual(story_map.non_goals, ["BR-003"])
        self.assertEqual(story_map.unassigned, [])

    def test_story_rows_outside_epics_and_duplicates(self):
        text = (
            PRD
            + "\n| US-009 | Stray story | Admin | BR-001 | Could |\n| US-001 | Again | x | BR-001 | Must |\n"
        )
        story_map = parse_story_map(text)
        self.assertEqual(story_map.unassigned, ["US-009"])
        self.assertEqual(story_map.duplicates, ["US-001"])

    def test_frontmatter(self):
        meta, body = parse_frontmatter(
            '---\nid: US-004\ntitle: "Quoted: title"\ntraces_to: [BR-1, NFR-002]\n'
            "depends_on:\n  - US-001\n  - US-002\ncomponents: []\n---\n# Body\n"
        )
        self.assertEqual(meta["title"], "Quoted: title")
        self.assertEqual(meta["traces_to"], ["BR-1", "NFR-002"])
        self.assertEqual(meta["depends_on"], ["US-001", "US-002"])
        self.assertEqual(meta["components"], [])
        self.assertEqual(body.strip(), "# Body")
        self.assertEqual(parse_frontmatter("# No frontmatter")[0], {})

    def test_split_stories_drops_preamble_and_fences(self):
        chunks = split_stories(RESPONSES["E01"])
        self.assertEqual([sid for sid, _ in chunks], ["US-001", "US-002"])
        for _, content in chunks:
            self.assertTrue(content.startswith("---"))
            self.assertNotIn("```", content)
        whole = "```markdown\n" + RESPONSES["E02"] + "```"
        self.assertNotIn("```", split_stories(whole)[0][1])


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.requirements = parse_requirements(BRD)
        self.story_map = parse_story_map(PRD)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name: str, text: str) -> None:
        (self.dir / name).write_text(text, encoding="utf-8")

    def check(self):
        return check_backlog(self.requirements, self.story_map, load_stories(self.dir), self.dir)

    def write_clean_backlog(self):
        self.write("US-001-sign-up.md", story_text("US-001", "Sign up", "E01", "BR-001"))
        self.write(
            "US-002-verify.md", story_text("US-002", "Verify", "E01", "BR-001", "US-001", "Should")
        )
        self.write("US-003-pay.md", story_text("US-003", "Pay", "E02", "BR-002, NFR-001", "US-001"))

    def test_clean_backlog_passes(self):
        self.write_clean_backlog()
        result = self.check()
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])
        self.assertEqual(result.coverage["BR-001"], ["US-001", "US-002"])
        self.assertEqual([s.id for s in result.build_order], ["US-001", "US-003", "US-002"])

    def test_broken_references_are_errors(self):
        self.write("US-001-sign-up.md", story_text("US-001", "Sign up", "E01", "BR-001, BR-042"))
        self.write("US-002-verify.md", story_text("US-002", "Verify", "E01", "BR-001", "US-077"))
        self.write("US-003-pay.md", story_text("US-003", "Pay", "E02", ""))
        errors = "\n".join(self.check().errors)
        self.assertIn("US-001: traces to BR-042, which is not in the BRD", errors)
        self.assertIn("US-002: depends on US-077", errors)
        self.assertIn("US-003: `traces_to` is empty", errors)
        self.assertIn("BR-002: no story covers it", errors)
        self.assertNotIn("BR-003", errors)  # listed as a PRD non-goal

    def test_dependency_cycle(self):
        self.write("US-001-a.md", story_text("US-001", "A", "E01", "BR-001", "US-003"))
        self.write("US-002-b.md", story_text("US-002", "B", "E01", "BR-001", priority="Should"))
        self.write("US-003-c.md", story_text("US-003", "C", "E02", "BR-002", "US-001"))
        result = self.check()
        self.assertIn("Dependency cycle: US-001 -> US-003 -> US-001.", result.errors)
        self.assertEqual([s.id for s in result.build_order], ["US-002"])

    def test_duplicates_and_sync_warnings(self):
        self.write_clean_backlog()
        self.write("US-003-copy.md", story_text("US-003", "Copy", "E02", "BR-002"))
        self.write("US-004-extra.md", story_text("US-004", "Extra", "E01", "BR-001", estimate="XL"))
        (self.dir / "US-001-sign-up.md").unlink()
        self.write("US-001-sign-up.md", story_text("US-001", "Sign up", "E02", "BR-001", "US-002"))
        result = self.check()
        self.assertTrue(any("duplicate ID" in e for e in result.errors))
        warnings = "\n".join(result.warnings)
        self.assertIn("US-004: not in the PRD story map", warnings)
        self.assertIn("US-004: is XL", warnings)
        self.assertIn("US-001: epic is E02 but the PRD story map puts it in E01", warnings)
        self.assertIn("US-001 (Must) depends on US-002 (Should)", warnings)

    def test_missing_story_files_are_warnings(self):
        self.write("US-001-sign-up.md", story_text("US-001", "Sign up", "E01", "BR-001"))
        result = self.check()
        self.assertEqual(result.errors, [])  # BR-002 is planned by US-003
        self.assertIn("US-003: in the PRD story map but has no story file yet.", result.warnings)
        self.assertEqual(result.planned["BR-002"], ["US-003"])

    def test_story_quality_warnings(self):
        self.write_clean_backlog()
        self.write(
            "US-002-verify.md",
            "---\nid: US-002\nepic: E01\ntraces_to: [BR-001]\npriority: Should\nestimate: S\n---\nNo criteria.\n",
        )
        warnings = self.check().warnings
        self.assertIn("US-002: no Given/When/Then acceptance criteria.", warnings)
        self.assertIn("US-002: no tasks.", warnings)


class ScriptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        for name, text in {"brd.md": BRD, "prd.md": PRD, "design.md": DESIGN}.items():
            (self.dir / name).write_text(text, encoding="utf-8")
        self.backlog = self.dir / "backlog"

    def tearDown(self):
        self.tmp.cleanup()

    def fake_claude(self) -> str:
        import json

        responses = self.dir / "responses.json"
        responses.write_text(json.dumps(RESPONSES), encoding="utf-8")
        script = self.dir / "fake_claude.py"
        script.write_text(FAKE_CLAUDE, encoding="utf-8")
        if os.name == "nt":
            wrapper = self.dir / "fake_claude.cmd"
            wrapper.write_text(
                f'@"{sys.executable}" "{script}" "{responses}"\r\n', encoding="utf-8"
            )
        else:
            wrapper = self.dir / "fake_claude"
            wrapper.write_text(
                f'#!/bin/sh\nexec "{sys.executable}" "{script}" "{responses}"\n', encoding="utf-8"
            )
            wrapper.chmod(0o755)
        return str(wrapper)

    def stories_args(self, *extra: str) -> list[str]:
        return [
            "--prd",
            str(self.dir / "prd.md"),
            "--technical-design",
            str(self.dir / "design.md"),
            "--out-dir",
            str(self.backlog),
            *extra,
        ]

    def test_generate_validate_and_no_overwrite(self):
        claude = self.fake_claude()
        result = run_script("generate_stories.py", *self.stories_args("--claude-bin", claude))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        files = sorted(
            p.relative_to(self.backlog).as_posix() for p in self.backlog.rglob("US-*.md")
        )
        self.assertEqual(
            files,
            [
                "E01-accounts/US-001-sign-up-with-email.md",
                "E01-accounts/US-002-verify-email-address.md",
                "E02-billing/US-003-pay-an-invoice-by-card-caf-test.md",
            ],
        )
        us3 = Story.load(self.backlog / "E02-billing" / "US-003-pay-an-invoice-by-card-caf-test.md")
        self.assertIn("café", us3.title)

        validate = run_script(
            "validate_backlog.py",
            "--brd",
            str(self.dir / "brd.md"),
            "--prd",
            str(self.dir / "prd.md"),
            "--backlog",
            str(self.backlog),
            "--strict",
        )
        self.assertEqual(validate.returncode, 0, validate.stdout + validate.stderr)
        report = (self.backlog / "traceability.md").read_text(encoding="utf-8")
        self.assertIn("| BR-001 | Users can create an account | US-001, US-002 |", report)
        self.assertIn("| BR-003 | Admins can export reports | PRD non-goal |", report)
        self.assertIn("| 2 | US-003 |", report)

        edited = self.backlog / "E01-accounts" / "US-001-sign-up-with-email.md"
        edited.write_text(
            edited.read_text(encoding="utf-8") + "\nReviewed by PM.\n", encoding="utf-8"
        )
        again = run_script("generate_stories.py", *self.stories_args("--claude-bin", claude))
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("Skipped E01", again.stdout)
        self.assertIn("Reviewed by PM.", edited.read_text(encoding="utf-8"))

        forced = run_script(
            "generate_stories.py",
            *self.stories_args("--claude-bin", claude, "--epic", "E01", "--force"),
        )
        self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
        self.assertNotIn("Reviewed by PM.", edited.read_text(encoding="utf-8"))

    def test_prompt_only_and_response_import(self):
        result = run_script("generate_stories.py", *self.stories_args("--prompt-only"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (self.backlog / "prompts" / "E02-billing.prompt.md").read_text(encoding="utf-8")
        self.assertIn("Expand only epic E02: Billing", prompt)
        self.assertIn("| US-003 |", prompt)

        response = self.dir / "e01.md"
        response.write_text(RESPONSES["E01"], encoding="utf-8")
        imported = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
        self.assertEqual(len(list((self.backlog / "E01-accounts").glob("US-*.md"))), 2)

        bad = self.dir / "bad.md"
        bad.write_text("Sorry, I cannot help with that.", encoding="utf-8")
        failed = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E02", "--response", str(bad))
        )
        self.assertEqual(failed.returncode, 1)
        self.assertTrue((self.backlog / "prompts" / "E02-billing.response.md").exists())

    def test_response_import_rejects_unknown_story_id_without_writing_files(self):
        response = self.dir / "unknown-story.md"
        response.write_text(
            RESPONSES["E01"]
            + "\n<!-- story: US-999 -->\n"
            + story_text("US-999", "Unknown", "E01", "BR-001"),
            encoding="utf-8",
        )
        result = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [])

    def test_response_import_rejects_missing_expected_story_id_without_writing_files(self):
        response = self.dir / "missing-story.md"
        response.write_text(
            "<!-- story: US-001 -->\n"
            + story_text("US-001", "Sign up with email", "E01", "BR-001"),
            encoding="utf-8",
        )
        result = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [])

    def test_response_import_rejects_duplicate_marker_without_writing_files(self):
        duplicate = "<!-- story: US-001 -->\n" + story_text(
            "US-001", "Sign up again", "E01", "BR-001"
        )
        response = self.dir / "duplicate-marker.md"
        response.write_text(RESPONSES["E01"] + "\n" + duplicate, encoding="utf-8")
        result = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [])

    def test_response_import_rejects_frontmatter_id_mismatch_without_writing_files(self):
        response = self.dir / "frontmatter-id-mismatch.md"
        response.write_text(RESPONSES["E01"].replace("id: US-002", "id: US-001"), encoding="utf-8")
        result = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [])

    def test_response_import_rejects_frontmatter_epic_mismatch_without_writing_files(self):
        response = self.dir / "frontmatter-epic-mismatch.md"
        response.write_text(RESPONSES["E01"].replace("epic: E01", "epic: E02"), encoding="utf-8")
        result = run_script(
            "generate_stories.py", *self.stories_args("--epic", "E01", "--response", str(response))
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [])

    def test_rejected_response_preserves_existing_story_byte_for_byte(self):
        existing = self.backlog / "E01-accounts" / "US-001-existing.md"
        existing.parent.mkdir(parents=True)
        original = story_text("US-001", "Existing story", "E01", "BR-001") + "\nReviewed by PM.\n"
        existing.write_text(original, encoding="utf-8")
        response = self.dir / "invalid-after-valid-story.md"
        response.write_text(
            "<!-- story: US-001 -->\n"
            + story_text("US-001", "Replacement", "E01", "BR-001")
            + "\n<!-- story: US-999 -->\n"
            + story_text("US-999", "Unknown", "E01", "BR-001"),
            encoding="utf-8",
        )
        result = run_script(
            "generate_stories.py",
            *self.stories_args("--epic", "E01", "--response", str(response), "--force"),
        )
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(existing.read_text(encoding="utf-8"), original)
        self.assertEqual(list(self.backlog.rglob("US-*.md")), [existing])

    def test_missing_cli_writes_every_analysis_prompt(self):
        idea = self.dir / "my-product.md"
        idea.write_text("# Idea Canvas: My Product\n", encoding="utf-8")
        result = run_script(
            "generate_analysis.py",
            "--idea",
            str(idea),
            "--out-dir",
            str(self.dir / "analysis"),
            "--claude-bin",
            "definitely-not-installed-claude",
        )
        self.assertEqual(result.returncode, 1)
        prompts = list((self.dir / "analysis").rglob("*.prompt.md"))
        self.assertEqual(len(prompts), 7)

    def test_brd_uses_only_this_products_exact_reviewed_analyses(self):
        analysis = self.dir / "analysis"
        (analysis / "legal").mkdir(parents=True)
        (analysis / "legal" / "my-product-legal-analysis.md").write_text("MINE", encoding="utf-8")
        (analysis / "legal" / "my-product-legal-analysis.prompt.md").write_text(
            "PROMPT", encoding="utf-8"
        )
        (analysis / "legal" / "my-product-v2-legal-analysis.md").write_text(
            "PREFIX NEIGHBOUR", encoding="utf-8"
        )
        (analysis / "legal" / "other-product-legal-analysis.md").write_text(
            "OTHER", encoding="utf-8"
        )
        files = markdown_files(analysis, names={"my-product-legal-analysis.md"})
        self.assertEqual([p.name for p in files], ["my-product-legal-analysis.md"])

        idea = self.dir / "my-product.md"
        idea.write_text("# Idea\n", encoding="utf-8")
        result = run_script(
            "generate_brd.py",
            "--idea",
            str(idea),
            "--analysis",
            str(analysis),
            "--out",
            str(self.dir / "out-brd.md"),
            "--prompt-only",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        prompt = (self.dir / "out-brd.prompt.md").read_text(encoding="utf-8")
        self.assertIn("MINE", prompt)
        self.assertNotIn("PREFIX NEIGHBOUR", prompt)
        self.assertNotIn("OTHER", prompt)
        self.assertNotIn("PROMPT", prompt)

    def test_brd_rejects_symlinked_analysis_document(self):
        analysis = self.dir / "analysis" / "legal"
        analysis.mkdir(parents=True)
        external = self.dir / "external-analysis.md"
        external.write_text("EXTERNAL", encoding="utf-8")
        (analysis / "my-product-legal-analysis.md").symlink_to(external)
        idea = self.dir / "my-product.md"
        idea.write_text("# Idea\n", encoding="utf-8")

        result = run_script(
            "generate_brd.py",
            "--idea",
            str(idea),
            "--analysis",
            str(analysis.parent),
            "--out",
            str(self.dir / "out-brd.md"),
            "--prompt-only",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())

    def test_brd_rejects_symlinked_output_without_changing_external_target(self):
        analysis = self.dir / "analysis" / "legal"
        analysis.mkdir(parents=True)
        (analysis / "my-product-legal-analysis.md").write_text("MINE", encoding="utf-8")
        idea = self.dir / "my-product.md"
        idea.write_text("# Idea\n", encoding="utf-8")
        external = self.dir / "external-brd.md"
        original = "reviewed external document\n"
        external.write_text(original, encoding="utf-8")
        output = self.dir / "out-brd.md"
        output.symlink_to(external)
        claude = self.dir / "fake_brd_claude"
        claude.write_text("#!/bin/sh\nprintf '# Generated BRD\\n'\n", encoding="utf-8")
        claude.chmod(0o755)

        result = run_script(
            "generate_brd.py",
            "--idea",
            str(idea),
            "--analysis",
            str(analysis.parent),
            "--out",
            str(output),
            "--claude-bin",
            str(claude),
            "--force",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())
        self.assertEqual(external.read_text(encoding="utf-8"), original)

    def test_brd_rejects_output_below_symlinked_ancestor_directory(self):
        analysis = self.dir / "analysis" / "legal"
        analysis.mkdir(parents=True)
        (analysis / "my-product-legal-analysis.md").write_text("MINE", encoding="utf-8")
        idea = self.dir / "my-product.md"
        idea.write_text("# Idea\n", encoding="utf-8")
        external_dir = self.dir / "external-output"
        external_dir.mkdir()
        redirected = self.dir / "redirected"
        redirected.symlink_to(external_dir, target_is_directory=True)
        output = redirected / "nested" / "out-brd.md"

        result = run_script(
            "generate_brd.py",
            "--idea",
            str(idea),
            "--analysis",
            str(analysis.parent),
            "--out",
            str(output),
            "--prompt-only",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr.lower())
        self.assertFalse((external_dir / "nested" / "out-brd.prompt.md").exists())


if __name__ == "__main__":
    unittest.main()
