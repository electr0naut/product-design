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
PROMPT_SUFFIX = ".prompt.md"
TEMPLATE_INTRO = "Return the final document in this exact template structure:"

# Outcomes of generate().
WROTE = "wrote"
SKIPPED = "skipped"
FALLBACK = "fallback"
FAILED = "failed"


def project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def reject_symlink(path: Path, kind: str) -> None:
    """Check each lexical component; an existing descendant does not end the walk."""
    absolute = path if path.is_absolute() else ROOT / path
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        if part == "..":
            raise SystemExit(f"Refusing parent traversal in {kind}: {display_path(path)}")
        current /= part
        # System-level aliases are common (/tmp on some Linux installations,
        # /var on macOS); all descendants are still checked independently.
        if current.is_symlink() and current not in (Path("/tmp"), Path("/var")):
            raise SystemExit(f"Refusing symlinked {kind}: {display_path(current)}")


def read_text(path: Path) -> str:
    reject_symlink(path, "input")
    if not path.exists():
        raise SystemExit(f"Missing file: {display_path(path)}")
    if not path.is_file():
        raise SystemExit(f"Expected regular file: {display_path(path)}")
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    reject_symlink(path, "output")
    reject_symlink(path.parent, "output parent directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def plural(count: int, word: str, many: str | None = None) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {many or word + 's'}"


def slugify(text: str, fallback: str = "item") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or fallback


def slug_from_path(path: Path) -> str:
    stem = path.stem.lower()
    stem = re.sub(r"-(analysis|brd|prd|technical-design)$", "", stem)
    return slugify(stem, fallback="product")


def is_prompt_file(path: Path) -> bool:
    return path.name.endswith(PROMPT_SUFFIX)


def markdown_files(
    path: Path, product: str | None = None, names: set[str] | None = None
) -> list[Path]:
    """Return reviewed, regular Markdown documents in `path`.

    Skips templates, hidden files and assembled `.prompt.md` files. With
    `product`, keeps only files named `<product>.md` or `<product>-*.md`; pass
    `names` when a caller accepts an exact set of artefact names.
    """
    reject_symlink(path, "input")
    if path.is_file():
        if names is not None and path.name not in names:
            return []
        if is_prompt_file(path):
            return []
        return [path]
    if not path.exists():
        raise SystemExit(f"Missing directory: {display_path(path)}")
    files = []
    for item in sorted(path.rglob("*.md")):
        relative = item.relative_to(path)
        if "templates" in relative.parts or item.name.startswith("."):
            continue
        if is_prompt_file(item):
            continue
        if names is not None and item.name not in names:
            continue
        if product and not (item.stem == product or item.stem.startswith(f"{product}-")):
            continue
        reject_symlink(item, "discovered input")
        if not item.is_file():
            raise SystemExit(f"Expected regular file: {display_path(item)}")
        files.append(item)
    return files


def bundle_documents(title: str, paths: list[Path]) -> str:
    sections = [f"# {title}"]
    for path in paths:
        sections.append(f"\n## Source: {display_path(path)}\n\n{read_text(path)}")
    return "\n".join(sections)


def compose_prompt(
    instruction: Path,
    template: Path | None,
    context: str,
    template_intro: str = TEMPLATE_INTRO,
) -> str:
    today = dt.date.today().isoformat()
    parts = [
        read_text(instruction),
        f"\nCurrent date: {today}",
        "\nUse the source documents below as the system of record.",
    ]
    if template is not None:
        parts.append(f"\n{template_intro}\n\n" + read_text(template))
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
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite documents that already exist (they may hold reviewed edits).",
    )


def run_claude(prompt: str, claude_bin: str, fallback: Path, force: bool = False) -> str | None:
    """Run `claude -p` on the prompt and return its output.

    If the CLI is not installed, write the prompt to `fallback` for manual use
    and return None.
    """
    executable = shutil.which(claude_bin)
    if executable is None:
        reject_symlink(fallback, "fallback prompt")
        if fallback.exists() and not force:
            print(
                f"Claude CLI '{claude_bin}' not found. Existing prompt preserved: "
                f"{display_path(fallback)} (use --force to overwrite).",
                file=sys.stderr,
            )
            return None
        write_text(fallback, prompt)
        print(
            f"Claude CLI '{claude_bin}' not found. Wrote prompt for manual use: "
            f"{display_path(fallback)}",
            file=sys.stderr,
        )
        return None

    result = subprocess.run(
        [executable, "-p"],
        input=prompt,
        cwd=ROOT,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout


def generate(
    prompt: str,
    output: Path,
    prompt_only: bool,
    claude_bin: str,
    force: bool = False,
) -> str:
    """Write the prompt (prompt-only) or the generated document to `output`.

    Never overwrites an existing document unless `force` is set, because
    documents are reviewed and edited by people after generation.
    """
    reject_symlink(output, "output")
    if prompt_only:
        if output.exists() and not force:
            print(f"Skipped {display_path(output)}: it already exists (use --force to overwrite).")
            return SKIPPED
        write_text(output, prompt)
        print(f"Wrote prompt: {display_path(output)}")
        return WROTE

    if output.exists() and not force:
        print(f"Skipped {display_path(output)}: it already exists (use --force to overwrite).")
        return SKIPPED

    text = run_claude(prompt, claude_bin, output.with_suffix(PROMPT_SUFFIX), force)
    if text is None:
        return FALLBACK

    write_text(output, text)
    print(f"Wrote document: {display_path(output)}")
    return WROTE


def exit_status(outcomes: list[str]) -> None:
    """Exit non-zero if any document could not be generated."""
    if FALLBACK in outcomes or FAILED in outcomes:
        raise SystemExit(1)
