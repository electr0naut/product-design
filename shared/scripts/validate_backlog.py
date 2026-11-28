#!/usr/bin/env python3
"""Check that the phase-06 backlog traces to the BRD and PRD, and write a report.

Errors (exit code 1): stories tracing to requirements that are not in the BRD,
BRD requirements no story covers, unknown or circular dependencies, duplicate
IDs. Warnings: stories missing acceptance criteria or tasks, XL estimates,
stories out of sync with the PRD story map. The report, with a coverage matrix
and a dependency-ordered build plan, goes to `<backlog>/traceability.md`.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

from backlog import (
    Check,
    StoryMap,
    check_backlog,
    load_stories,
    parse_requirements,
    parse_story_map_path,
    prd_sources,
    table_cell,
)
from workflow_common import (
    ROOT,
    display_path,
    plural,
    project_path,
    read_text,
    slug_from_path,
    write_text,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--brd", required=True, help="Path to the approved BRD.")
    parser.add_argument("--prd", required=True, help="Path to the approved PRD.")
    parser.add_argument("--backlog", help="Backlog directory. Default: 06-backlog/<product>/.")
    parser.add_argument("--report", help="Report path. Default: <backlog>/traceability.md.")
    parser.add_argument("--lock", help="Lock path. Default: <backlog>/backlog.lock.json.")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings too.")
    args = parser.parse_args()

    brd = project_path(args.brd)
    prd = project_path(args.prd)
    slug = prd.name if prd.is_dir() else slug_from_path(prd)
    backlog_dir = project_path(args.backlog) if args.backlog else ROOT / "06-backlog" / slug
    if not backlog_dir.is_dir():
        raise SystemExit(
            f"No backlog at {display_path(backlog_dir)}. Generate it first with "
            "shared/scripts/generate_stories.py."
        )
    report_path = project_path(args.report) if args.report else backlog_dir / "traceability.md"
    lock_path = project_path(args.lock) if args.lock else backlog_dir / "backlog.lock.json"

    requirements = parse_requirements(read_text(brd))
    if not requirements:
        raise SystemExit(f"No BR-xxx or NFR-xxx requirement rows found in {display_path(brd)}.")
    try:
        prd_files = prd_sources(prd)
        story_map = parse_story_map_path(prd)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    stories = load_stories(backlog_dir)
    check = check_backlog(requirements, story_map, stories, backlog_dir)

    sources = [display_path(p) for p in (brd, *prd_files, backlog_dir)]
    write_text(report_path, render_report(slug, sources, requirements, story_map, check))

    print(
        f"Backlog check for '{slug}': {plural(len(check.errors), 'error')}, "
        f"{plural(len(check.warnings), 'warning')}."
    )
    for message in check.errors:
        print(f"  ERROR    {message}")
    for message in check.warnings:
        print(f"  WARNING  {message}")
    print(f"Report: {display_path(report_path)}")

    if check.errors or (args.strict and check.warnings):
        if lock_path.exists():
            lock_path.unlink()
            print("Removed the stale backlog lock.", file=sys.stderr)
        print("Lock not written: the backlog did not pass.", file=sys.stderr)
        raise SystemExit(1)
    write_lock(lock_path, slug, brd, prd_files, check.stories)
    print(f"Lock: {display_path(lock_path)}")


def path_key(path: Path) -> str:
    """Repository-relative when possible, absolute otherwise (tests, external inputs)."""
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def write_lock(lock_path: Path, slug: str, brd: Path, prd_files: list[Path], stories: dict) -> None:
    """Record the exact validated backlog so the implementation phase can bind to it."""
    entries = {
        path_key(Path(story.path)): hashlib.sha256(Path(story.path).read_bytes()).hexdigest()
        for story in stories.values()
        if getattr(story, "path", None)
    }
    payload = {
        "schema_version": 1,
        "product": slug,
        "brd": path_key(brd),
        "brd_sha256": hashlib.sha256(brd.read_bytes()).hexdigest(),
        "prd_files": {
            path_key(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in prd_files
        },
        "stories": entries,
    }
    content = json.dumps(payload, indent=2, sort_keys=True)
    if lock_path.is_file() and read_text(lock_path).rstrip() == content:
        return
    write_text(lock_path, content)


def render_report(
    slug: str, sources: list[str], requirements, story_map: StoryMap, check: Check
) -> str:
    today = dt.date.today().isoformat()
    br_count = sum(1 for r in requirements if r.startswith("BR-"))
    nfr_count = len(requirements) - br_count
    result = "FAIL" if check.errors else "PASS"
    lines = [
        f"# Backlog Traceability: {slug}",
        "",
        f"Generated by `shared/scripts/validate_backlog.py` on {today} from "
        + ", ".join(f"`{s}`" for s in sources)
        + ". Do not edit; re-run the script.",
        "",
        "## Summary",
        f"- Requirements: {br_count} BR, {nfr_count} NFR",
        f"- Stories: {len(check.stories)} story files; the PRD story map lists "
        f"{len(story_map.stories)} in {len(story_map.epics)} epics",
        f"- Result: **{result}** with {plural(len(check.errors), 'error')} and "
        f"{plural(len(check.warnings), 'warning')}",
        "",
    ]
    if check.errors:
        lines += ["## Errors", *[f"- {m}" for m in check.errors], ""]
    if check.warnings:
        lines += ["## Warnings", *[f"- {m}" for m in check.warnings], ""]

    lines += [
        "## Requirement Coverage",
        "| Requirement | Description | Stories |",
        "|-------------|-------------|---------|",
    ]
    for req_id, requirement in requirements.items():
        lines.append(
            f"| {req_id} | {table_cell(requirement.text)} | {_coverage(req_id, story_map, check)} |"
        )
    lines.append("")

    lines += [
        "## Build Order",
        "Dependencies first, then by priority, epic and ID.",
        "",
        "| # | Story | Title | Epic | Priority | Estimate | Depends on |",
        "|---|-------|-------|------|----------|----------|------------|",
    ]
    for number, story in enumerate(check.build_order, start=1):
        lines.append(
            f"| {number} | {story.id} | {table_cell(story.title)} | {story.epic or '-'} | "
            f"{table_cell(story.priority) or '-'} | {story.estimate or '-'} | "
            f"{', '.join(story.depends_on) or '-'} |"
        )
    lines.append("")

    lines += ["## Epics"]
    for epic in story_map.epics.values():
        generated = sum(1 for s in epic.stories if s.id in check.stories)
        lines.append(
            f"- {epic.id}: {epic.name} ({generated} of {len(epic.stories)} stories generated)"
        )
    return "\n".join(lines)


def _coverage(req_id: str, story_map: StoryMap, check: Check) -> str:
    parts = []
    if check.coverage.get(req_id):
        parts.append(", ".join(check.coverage[req_id]))
    if check.planned.get(req_id):
        parts.append(f"planned: {', '.join(check.planned[req_id])} (no story file yet)")
    if req_id in story_map.non_goals:
        parts.append("PRD non-goal")
    if parts:
        return "; ".join(parts)
    return "**None**" if req_id.startswith("BR-") else "-"


if __name__ == "__main__":
    main()
