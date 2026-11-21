#!/usr/bin/env python3
"""Expand each PRD epic into implementation-ready user story files (phase 06).

Makes one Claude call per epic, with the approved PRD and technical design as
context, and writes one file per story to
`06-backlog/<product>/<E01-epic-name>/US-001-<title>.md`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from backlog import (
    Epic,
    StoryRef,
    files_for_story,
    normalize_epic_id,
    parse_frontmatter,
    parse_story_map_path,
    prd_sources,
    split_stories,
    table_cell,
)
from gate_reviews import add_review_args, maybe_enforce_gate, verify_bundle
from workflow_common import (
    FAILED,
    FALLBACK,
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    SKIPPED,
    WROTE,
    add_common_args,
    bundle_documents,
    check_draft_out,
    compose_prompt,
    display_path,
    draft_path,
    exit_status,
    generate,
    plural,
    project_path,
    read_text,
    reject_symlink,
    run_claude,
    slug_from_path,
    slugify,
    write_text,
)

STORY_TEMPLATE = ROOT / "06-backlog" / "templates" / "story-template.md"
TEMPLATE_INTRO = "Write each story in exactly this template structure, frontmatter included:"


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--prd", required=True, help="Path to the approved PRD.")
    parser.add_argument(
        "--technical-design", required=True, help="Path to the approved technical design."
    )
    parser.add_argument(
        "--epic",
        action="append",
        help="Epic to expand, e.g. E02. Repeat for several. Default: every epic.",
    )
    parser.add_argument("--out-dir", help="Backlog directory. Default: 06-backlog/<product>/.")
    parser.add_argument(
        "--response",
        help="Split a saved model response into story files instead of calling Claude "
        "(use with exactly one --epic).",
    )
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    prd = project_path(args.prd)
    design = project_path(args.technical_design)
    product = prd.name if prd.is_dir() else slug_from_path(prd)
    out_dir = project_path(args.out_dir) if args.out_dir else ROOT / "06-backlog" / product
    check_draft_out(out_dir, draft=args.draft, explicit=args.out_dir is not None)

    try:
        prd_files = prd_sources(prd)
        story_map = parse_story_map_path(prd)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    if not story_map.epics:
        raise SystemExit(
            f"No epics found in {display_path(prd)}. Expected headings like "
            "'### E01: Name' followed by a story table (see 04-prd/templates/prd-template.md)."
        )
    epics = select_epics(story_map.epics, args.epic)
    if args.response and len(epics) != 1:
        raise SystemExit("--response needs exactly one --epic.")
    core = prd_files[0]
    epic_files = {path.stem: path for path in prd_files[1:] if path.stem.startswith("E")}
    selected_files = [core] + [epic_files[e.id] for e in epics if e.id in epic_files]
    statuses = maybe_enforce_gate(
        args,
        product,
        "design-to-backlog",
        [*selected_files, design],
        [epic.id for epic in epics] if args.epic else None,
        output_product=slug_from_path(out_dir),
        search_from=out_dir,
        include_cross_cutting=bool(args.epic),
    )
    out_dir = draft_path(out_dir) if args.draft else out_dir
    for sid in story_map.unassigned:
        print(f"Warning: {sid} is not under an epic heading in the PRD; it will not be generated.")

    context = bundle_documents("Approved Inputs", [*selected_files, design])
    verify_bundle(context, statuses)
    outcomes = [expand_epic(epic, context, out_dir, args) for epic in epics]

    if WROTE in outcomes and not args.prompt_only:
        print(
            "\nNext: review the stories, then check traceability with\n"
            f"  python shared/scripts/validate_backlog.py --brd <approved BRD> --prd {display_path(prd)}"
        )
    exit_status(outcomes)


def select_epics(epics: dict[str, Epic], wanted: list[str] | None) -> list[Epic]:
    if not wanted:
        return list(epics.values())
    selected = []
    for value in wanted:
        eid = normalize_epic_id(value)
        if eid not in epics:
            known = ", ".join(epics) or "none"
            raise SystemExit(f"Unknown epic '{value}'. Epics in the PRD: {known}.")
        selected.append(epics[eid])
    return selected


def epic_brief(epic: Epic) -> str:
    rows = "\n".join(
        f"| {s.id} | {table_cell(s.summary)} | {table_cell(s.persona)} | "
        f"{', '.join(s.traces_to)} | {table_cell(s.priority)} |"
        for s in epic.stories
    )
    return (
        "\n\n# Epic To Expand\n\n"
        f"Expand only epic {epic.id}: {epic.name}. Write one story for each of these "
        "stories, keeping their IDs:\n\n"
        "| ID | Story | Persona | Traces to | Priority |\n"
        "|----|-------|---------|-----------|----------|\n"
        f"{rows}\n"
    )


def expand_epic(epic: Epic, context: str, out_dir: Path, args: argparse.Namespace) -> str:
    if not epic.stories:
        print(f"Skipped {epic.id}: it has no stories in the PRD story map.")
        return SKIPPED

    epic_dir = out_dir / f"{epic.id}-{slugify(epic.name, 'epic')[:50].strip('-')}"
    prompt_path = out_dir / "prompts" / f"{epic_dir.name}{PROMPT_SUFFIX}"
    missing = [s.id for s in epic.stories if not files_for_story(out_dir, s.id)]
    if not missing and not (args.force or args.prompt_only or args.response):
        print(
            f"Skipped {epic.id}: all {len(epic.stories)} stories already exist "
            "(use --force to regenerate)."
        )
        return SKIPPED

    prompt = compose_prompt(
        PROMPTS / "06-generate-stories.md",
        STORY_TEMPLATE,
        context + epic_brief(epic),
        template_intro=TEMPLATE_INTRO,
    )
    if args.prompt_only:
        return generate(prompt, prompt_path, True, args.claude_bin, args.force)

    if args.response:
        response = read_text(project_path(args.response))
    else:
        print(f"Generating {epic.id} ({len(epic.stories)} stories)...")
        response = run_claude(prompt, args.claude_bin, prompt_path, args.force)
        if response is None:
            return FALLBACK
    return write_stories(epic, epic_dir, out_dir, response, args.force)


def write_stories(epic: Epic, epic_dir: Path, out_dir: Path, response: str, force: bool) -> str:
    try:
        chunks = split_stories(response)
    except ValueError as exc:
        print(f"Error: rejected response for {epic.id}: {exc}", file=sys.stderr)
        return FAILED
    if not chunks:
        saved = out_dir / "prompts" / f"{epic_dir.name}.response.md"
        reject_symlink(saved, "saved response")
        if saved.exists() and not force:
            detail = f"Existing response at {display_path(saved)} was preserved"
            next_step = (
                "Fix the input and re-import (or use --force to replace the saved response)."
            )
        else:
            write_text(saved, response)
            detail = f"Saved the response to {display_path(saved)}"
            next_step = (
                f"Fix it and re-import with --epic {epic.id} --response {display_path(saved)}"
            )
        print(
            f"Error: found no stories in the response for {epic.id} "
            "(expected '<!-- story: US-001 -->' markers). "
            f"{detail}; {next_step}",
            file=sys.stderr,
        )
        return FAILED

    expected = {s.id: s for s in epic.stories}
    if not validate_story_response(epic, chunks, expected):
        return FAILED

    planned = []
    for sid, content in chunks:
        meta, _ = parse_frontmatter(content)
        existing = files_for_story(out_dir, sid)
        title_value = meta.get("title")
        title = title_value if isinstance(title_value, str) else ""
        name = slugify(title or expected[sid].summary, "story")[:60].strip("-")
        target = epic_dir / f"{sid}-{name}.md"
        reject_symlink(target, "story output")
        planned.append((sid, content, existing, target))

    written = skipped = 0
    for sid, content, existing, target in planned:
        if existing and not force:
            print(
                f"Skipped {sid}: {display_path(existing[0])} already exists (use --force to overwrite)."
            )
            skipped += 1
            continue
        for path in existing:
            reject_symlink(path, "story deletion")
            path.unlink()
        write_text(target, content)
        written += 1

    print(
        f"{epic.id}: wrote {plural(written, 'story', 'stories')} "
        f"to {display_path(epic_dir)}, skipped {skipped}."
    )
    return WROTE if written else SKIPPED


def validate_story_response(
    epic: Epic, chunks: list[tuple[str, str]], expected: dict[str, StoryRef]
) -> bool:
    """Reject incomplete or contradictory imports before changing story files."""
    marker_ids = [sid for sid, _ in chunks]
    marker_set = set(marker_ids)
    errors: list[str] = []

    duplicates = sorted({sid for sid in marker_ids if marker_ids.count(sid) > 1})
    if duplicates:
        errors.append(f"duplicate story marker IDs: {', '.join(duplicates)}")

    unknown = sorted(marker_set - expected.keys())
    if unknown:
        errors.append(f"story IDs not in {epic.id}: {', '.join(unknown)}")

    missing = sorted(expected.keys() - marker_set)
    if missing:
        errors.append(f"missing story IDs for {epic.id}: {', '.join(missing)}")

    for sid, content in chunks:
        meta, _ = parse_frontmatter(content)
        if not meta:
            errors.append(f"{sid}: missing frontmatter")
            continue
        if meta.get("id") != sid:
            errors.append(f"{sid}: frontmatter id is {meta.get('id')!r}")
        if meta.get("epic") != epic.id:
            errors.append(f"{sid}: frontmatter epic is {meta.get('epic')!r}, expected {epic.id}")

    if not errors:
        return True
    print(
        f"Error: rejected response for {epic.id}; no story files were changed:\n"
        + "\n".join(f"- {error}" for error in errors),
        file=sys.stderr,
    )
    return False


if __name__ == "__main__":
    main()
