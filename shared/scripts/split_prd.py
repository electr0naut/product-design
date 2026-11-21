#!/usr/bin/env python3
"""Split a monolithic PRD into core.md and one file per epic.

The split files become the reviewed artifacts; epic lanes hash only their own
file, so editing E02 no longer stales E01. Layout is validated before anything
is written; content outside the epic blocks stays in core.md.
"""

from __future__ import annotations

import argparse
import re

from backlog import EPIC_HEADING, epic_id
from workflow_common import display_path, project_path, read_text, write_text

H2 = re.compile(r"^##\s+")
FENCE = re.compile(r"^\s*(```|~~~)")


def headings(lines: list[str]) -> list[tuple[int, re.Match[str]]]:
    """Epic headings at level 3, ignoring fenced code."""
    found = []
    fenced = False
    for index, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = EPIC_HEADING.match(line)
        if match and len(match.group(1)) == 3:
            found.append((index, match))
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--prd", required=True, help="Monolithic PRD path")
    parser.add_argument("--out", help="Output directory. Default: <prd parent>/<product>/")
    args = parser.parse_args()

    prd = project_path(args.prd)
    text = read_text(prd)
    lines = text.splitlines(keepends=True)
    starts = headings(lines)
    if not starts:
        raise SystemExit(
            f"No '### E01: Name' epic headings in {display_path(prd)}; nothing to split."
        )
    ids = [epic_id(match.group(2)) for _, match in starts]
    duplicates = sorted({eid for eid in ids if ids.count(eid) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate epic IDs in {display_path(prd)}: {', '.join(duplicates)}")
    if starts[0][0] == 0:
        raise SystemExit("The PRD starts with an epic; a core section is required.")

    blocks: dict[str, list[str]] = {}
    for position, (index, match) in enumerate(starts):
        eid = epic_id(match.group(2))
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        for later in range(index + 1, end):
            if H2.match(lines[later]):
                if position + 1 < len(starts):
                    raise SystemExit(
                        "Epic sections must be contiguous; found a level-2 heading "
                        f"between {eid} and {ids[position + 1]}."
                    )
                end = later
                break
        blocks[eid] = lines[index:end]

    tail = lines[starts[-1][0] + len(blocks[ids[-1]]) :]
    core = "".join(lines[: starts[0][0]]).rstrip() + "\n"
    core += (
        "\n> Epics are split into separate files: "
        + ", ".join(f"`epics/{eid}.md`" for eid in sorted(blocks))
        + ". Edit one epic without restaling the others.\n"
    )
    if tail:
        core += "\n" + "".join(tail).lstrip("\n")

    out = project_path(args.out) if args.out else prd.parent / prd.stem.replace("-prd", "")
    if (out / "core.md").exists() or (
        (out / "epics").is_dir() and any((out / "epics").glob("*.md"))
    ):
        raise SystemExit(f"{display_path(out)} already looks split; refusing to overwrite.")

    write_text(out / "core.md", core)
    for eid, block in sorted(blocks.items()):
        write_text(out / "epics" / f"{eid}.md", "".join(block).strip() + "\n")
    print(f"Split {display_path(prd)} into {display_path(out)} ({len(blocks)} epics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
