#!/usr/bin/env python3
"""Generate a Markdown implementation plan from a validated backlog.

Reads the lock written by `validate_backlog.py`, verifies that every story, the
BRD and the PRD still match, checks the `backlog-to-implementation` review gate,
and only then assembles the prompt.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from backlog import parse_frontmatter
from gate_reviews import add_review_args, maybe_enforce_gate, verify_bundle
from workflow_common import (
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    add_common_args,
    bundle_documents,
    compose_prompt,
    display_path,
    exit_status,
    generate,
    project_path,
    read_text,
    reject_symlink,
    slug_from_path,
)


def load_lock(lock_path: Path, product: str) -> tuple[dict, list[Path]]:
    """Refuse an absent, foreign or stale lock before anything is generated."""
    try:
        data = json.loads(read_text(lock_path))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid backlog lock {display_path(lock_path)}: {exc}") from exc
    if data.get("schema_version") != 1 or data.get("product") != product:
        raise SystemExit(f"Backlog lock {display_path(lock_path)} is not for product '{product}'.")
    declared = [("brd", data.get("brd"), data.get("brd_sha256"))]
    prd_files = data.get("prd_files")
    if not isinstance(prd_files, dict) or not prd_files:
        raise SystemExit(f"Backlog lock {display_path(lock_path)} lists no PRD files.")
    declared += [("prd", key, digest) for key, digest in prd_files.items()]
    stories = data.get("stories")
    if not isinstance(stories, dict) or not stories:
        raise SystemExit(f"Backlog lock {display_path(lock_path)} lists no stories.")
    declared += [("story", key, digest) for key, digest in stories.items()]
    paths: list[Path] = []
    for kind, key, digest in declared:
        if not isinstance(key, str) or not isinstance(digest, str):
            raise SystemExit(f"Backlog lock {display_path(lock_path)} has a malformed entry.")
        path = Path(key)
        if not path.is_absolute():
            path = ROOT / path
        reject_symlink(path, "locked input")
        if not path.is_file():
            raise SystemExit(
                f"Locked {kind} is missing: {display_path(path)}. Re-run validate_backlog.py."
            )
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise SystemExit(
                f"Locked {kind} changed since validation: {display_path(path)}. "
                "Re-run validate_backlog.py and re-approve the backlog."
            )
        if kind == "story":
            paths.append(path)
    return data, sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument(
        "--technical-design",
        required=True,
        help="Path to the reviewed technical design.",
    )
    parser.add_argument("--backlog", help="Backlog directory. Default: 06-backlog/<product>/.")
    parser.add_argument("--out", help="Output implementation-plan path.")
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    technical_design = project_path(args.technical_design)
    product = slug_from_path(technical_design)
    backlog_dir = project_path(args.backlog) if args.backlog else ROOT / "06-backlog" / product
    lock_path = backlog_dir / "backlog.lock.json"
    lock, story_paths = load_lock(lock_path, product)

    epics = set()
    for path in story_paths:
        meta, _ = parse_frontmatter(read_text(path))
        epic = meta.get("epic")
        if not isinstance(epic, str) or not epic:
            print(f"Warning: {display_path(path)} has no epic; the whole gate will be checked.")
            epics = set()
            break
        epics.add(epic)

    sources = [technical_design, lock_path, *story_paths]
    statuses = maybe_enforce_gate(
        args,
        product,
        "backlog-to-implementation",
        sources,
        sorted(epics) if epics else None,
        output_product=product,
        search_from=backlog_dir,
        include_cross_cutting=bool(epics),
    )
    context = bundle_documents("Approved Inputs", sources)
    verify_bundle(context, statuses)

    prompt = compose_prompt(PROMPTS / "07-scaffold-code.md", None, context)
    default_out = ROOT / "07-implementation" / f"{product}-implementation-plan.md"
    output = project_path(args.out) if args.out else default_out
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
