#!/usr/bin/env python3
"""Propose manifest questions from PRD and story Open Questions sections.

This command only prints JSON. The maintainer chooses owners and accepts the
proposals into the review manifest; no question or decision is recorded here.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from backlog import prd_sources, story_files
from workflow_common import project_path, read_text

HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BULLET = re.compile(r"^\s*[-*]\s+(?:\[ \]\s*)?(.+?)\s*$")
FENCE = re.compile(r"^\s*(?:```|~~~)")
EPIC = re.compile(r"^E\d{2,3}$")


def open_questions(path: Path) -> list[str]:
    """Extract bullet text only from an Open Questions section, not code fences."""
    inside = False
    level = 0
    fenced = False
    found = []
    for line in read_text(path).splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING.match(line)
        if heading:
            current = len(heading.group(1))
            if inside and current <= level:
                inside = False
            if heading.group(2).strip().lower() == "open questions":
                inside, level = True, current
            continue
        if inside and (bullet := BULLET.match(line)):
            found.append(bullet.group(1))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--prd", required=True, help="PRD file or split directory")
    parser.add_argument("--backlog", help="Directory of story files")
    parser.add_argument("--manifest", required=True, help="Existing review manifest")
    parser.add_argument("--role", required=True, help="Proposed owner; maintainer must verify")
    parser.add_argument("--gate", default="design-to-backlog", help="Proposed gate")
    parser.add_argument("--lane", help="Lane for core/monolithic questions")
    args = parser.parse_args()

    manifest = project_path(args.manifest)
    root = manifest.parent.parent
    data = json.loads(read_text(manifest))
    existing = data.get("questions", [])
    next_number = max((int(q["id"].split("-")[1]) for q in existing), default=0) + 1
    seen = {(q.get("source", {}).get("artifact"), q.get("text")) for q in existing}
    paths = prd_sources(project_path(args.prd))
    if args.backlog:
        paths.extend(story_files(project_path(args.backlog)))
    proposals = []
    for path in paths:
        lane = path.stem if EPIC.fullmatch(path.stem) else args.lane
        if path.name.startswith("US-"):
            from backlog import parse_frontmatter

            meta, _ = parse_frontmatter(read_text(path))
            lane = meta.get("epic") if isinstance(meta.get("epic"), str) else args.lane
        for text in open_questions(path):
            if not lane:
                continue  # Core questions need an explicit cross-cutting --lane.
            try:
                artifact = path.relative_to(root).as_posix()
            except ValueError as exc:
                raise SystemExit(f"Question source outside product: {path}") from exc
            if (artifact, text) in seen:
                continue
            seen.add((artifact, text))
            proposals.append(
                {
                    "id": f"Q-{next_number:03d}",
                    "gate": args.gate,
                    "lane": lane,
                    "role": args.role,
                    "text": text,
                    "source": {"artifact": artifact, "heading": "Open Questions"},
                }
            )
            next_number += 1
    print(json.dumps({"proposals": proposals}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
