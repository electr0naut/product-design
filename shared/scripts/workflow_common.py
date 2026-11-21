"""Shared helpers for phase-generation scripts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
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


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class SourceBundle(str):
    """Context text with the exact source files used to assemble it."""

    sources: list[dict[str, str]]

    def __new__(cls, text: str, sources: list[dict[str, str]]) -> SourceBundle:
        result = super().__new__(cls, text)
        result.sources = sources
        return result


class AssembledPrompt(str):
    """Prompt text with a snapshot of its provenance (not model claims)."""

    provenance: dict[str, object]

    def __new__(cls, text: str, provenance: dict[str, object]) -> AssembledPrompt:
        result = super().__new__(cls, text)
        result.provenance = provenance
        return result


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
    return path.read_bytes().decode("utf-8")


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


def bundle_documents(title: str, paths: list[Path]) -> SourceBundle:
    sections = [f"# {title}"]
    sources = []
    for path in paths:
        text = read_text(path)
        sections.append(f"\n## Source: {display_path(path)}\n\n{text}")
        sources.append({"path": display_path(path), "sha256": sha256(text.encode("utf-8"))})
    return SourceBundle("\n".join(sections), sources)


def compose_prompt(
    instruction: Path,
    template: Path | None,
    context: str,
    template_intro: str = TEMPLATE_INTRO,
) -> AssembledPrompt:
    today = dt.date.today().isoformat()
    instruction_text = read_text(instruction)
    parts = [
        instruction_text,
        f"\nCurrent date: {today}",
        "\nUse the source documents below as the system of record.",
    ]
    template_text = read_text(template) if template is not None else None
    if template_text is not None:
        parts.append(f"\n{template_intro}\n\n" + template_text)
    parts.append("\nSource documents:\n\n" + context)
    text = "\n\n---\n\n".join(parts)
    return AssembledPrompt(
        text,
        {
            "inputs": getattr(context, "sources", []),
            "instruction": {
                "path": str(instruction),
                "sha256": sha256(instruction_text.encode("utf-8")),
            },
            "template": (
                {"path": str(template), "sha256": sha256(template_text.encode("utf-8"))}
                if template is not None and template_text is not None
                else None
            ),
            "assembled_prompt_sha256": sha256(text.encode("utf-8")),
        },
    )


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

    sidecar = output.with_suffix(".provenance.json")
    reject_symlink(sidecar, "provenance sidecar")
    for target in (output, sidecar):
        if target.exists() and not target.is_file():
            raise SystemExit(f"Expected regular file: {display_path(target)}")
    if (output.exists() or sidecar.exists()) and not force:
        print(
            f"Skipped {display_path(output)}: document or provenance already exists (use --force to overwrite)."
        )
        return SKIPPED

    text = run_claude(prompt, claude_bin, output.with_suffix(PROMPT_SUFFIX), force)
    if text is None:
        return FALLBACK

    content = text.rstrip() + "\n"
    provenance = dict(getattr(prompt, "provenance", {}))
    provenance.update(
        {
            "document_sha256": sha256(content.encode("utf-8")),
            "model": None,  # `claude -p` plain text does not report the selected model.
            "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        }
    )
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | (os.O_TRUNC if force else os.O_EXCL)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(sidecar, flags, 0o666), "w", encoding="utf-8") as file:
        json.dump(provenance, file, indent=2, sort_keys=True)
        file.write("\n")
    write_text(output, content)
    print(f"Wrote document: {display_path(output)}")
    return WROTE


def exit_status(outcomes: list[str]) -> None:
    """Exit non-zero if any document could not be generated."""
    if FALLBACK in outcomes or FAILED in outcomes:
        raise SystemExit(1)
