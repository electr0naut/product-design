#!/usr/bin/env python3
"""Split a monolithic PRD into core.md and one file per epic.

The split files become the reviewed artifacts; epic lanes hash only their own
file, so editing E02 no longer stales E01. The splitter refuses ambiguous
layouts and writes nothing on failure.
"""

from __future__ import annotations

import argparse
import re

from workflow_common import display_path, project_path, read_text, write_text

EPIC = re.compile(r"^###\s+(E\d{1,3})\s*[:.\-]\s*(.+?)\s*$")
H2 = re.compile(r"^##\s+")


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--prd", required=True, help="Monolithic PRD path")
    parser.add_argument("--out", help="Output directory. Default: <prd parent>/<product>/")
    args = parser.parse_args()

    prd = project_path(args.prd)
    text = read_text(prd)
    lines = text.splitlines(keepends=True)
    starts = [(index, match) for index, line in enumerate(lines) if (match := EPIC.match(line))]
    if not starts:
        raise SystemExit(
            f"No '### E01: Name' epic headings in {display_path(prd)}; nothing to split."
        )
    ids = [match.group(1) for _, match in starts]
    duplicates = sorted({eid for eid in ids if ids.count(eid) > 1})
    if duplicates:
        raise SystemExit(f"Duplicate epic IDs in {display_path(prd)}: {', '.join(duplicates)}")
    if starts[0][0] == 0:
        raise SystemExit("The PRD starts with an epic; a core section is required.")
    for line in lines[starts[0][0] : starts[-1][0]]:
        if H2.match(line):
            raise SystemExit(
                "Epic sections must be contiguous; found a level-2 heading between epics."
            )

    out = project_path(args.out) if args.out else prd.parent / prd.stem.replace("-prd", "")
    if (out / "epics").is_dir() and any((out / "epics").glob("*.md")):
        raise SystemExit(f"{display_path(out)} already contains epics; refusing to overwrite.")

    blocks: dict[str, list[str]] = {}
    for index, match in starts:
        end = len(lines)
        for later in range(index + 1, len(lines)):
            if EPIC.match(lines[later]) or H2.match(lines[later]):
                end = later
                break
        blocks[match.group(1)] = lines[index:end]

    core = "".join(lines[: starts[0][0]]).rstrip() + "\n"
    core += (
        "\n> Epics are split into separate files: "
        + ", ".join(f"`epics/{eid}.md`" for eid in sorted(blocks))
        + ". Edit one epic without restaling the others.\n"
    )
    write_text(out / "core.md", core)
    for eid, block in sorted(blocks.items()):
        write_text(out / "epics" / f"{eid}.md", "".join(block).strip() + "\n")
    print(f"Split {display_path(prd)} into {display_path(out)} ({len(blocks)} epics).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
