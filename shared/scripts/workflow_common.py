"""Shared helpers for phase-generation scripts."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "shared" / "prompts"


def project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def slug_from_path(path: Path) -> str:
    stem = path.stem.lower()
    stem = re.sub(r"-(analysis|brd|prd|technical-design)$", "", stem)
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem or "product"


def markdown_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.exists():
        raise FileNotFoundError(f"Missing directory: {path.relative_to(ROOT)}")
    return sorted(
        item
        for item in path.rglob("*.md")
        if "templates" not in item.parts and not item.name.startswith(".")
    )


def bundle_documents(title: str, paths: list[Path]) -> str:
    sections = [f"# {title}"]
    for path in paths:
        rel = path.relative_to(ROOT)
        sections.append(f"\n## Source: {rel}\n\n{read_text(path)}")
    return "\n".join(sections)


def compose_prompt(instruction: Path, template: Path | None, context: str) -> str:
    today = dt.date.today().isoformat()
    parts = [
        read_text(instruction),
        f"\nCurrent date: {today}",
        "\nUse the source documents below as the system of record.",
    ]
    if template is not None:
        parts.append(
            "\nReturn the final document in this exact template structure:\n\n"
            + read_text(template)
        )
    parts.append("\nSource documents:\n\n" + context)
    return "\n\n---\n\n".join(parts)


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Write the assembled prompt instead of invoking Claude.",
    )
    parser.add_argument(
        "--claude-bin",
        default="claude",
        help="Claude CLI executable to use when generating content.",
    )


def generate(prompt: str, output: Path, prompt_only: bool, claude_bin: str) -> None:
    if prompt_only:
        write_text(output, prompt)
        print(f"Wrote prompt: {display_path(output)}")
        return

    if shutil.which(claude_bin) is None:
        prompt_output = output.with_suffix(".prompt.md")
        write_text(prompt_output, prompt)
        raise SystemExit(
            f"Claude CLI not found. Wrote prompt for manual use: "
            f"{display_path(prompt_output)}"
        )

    result = subprocess.run(
        [claude_bin, "-p", prompt],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)

    write_text(output, result.stdout)
    print(f"Wrote document: {display_path(output)}")
