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
    files_for_story,
    normalize_epic_id,
    parse_frontmatter,
    parse_story_map,
    split_stories,
)
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
    compose_prompt,
    display_path,
    exit_status,
    plural,
    project_path,
    read_text,
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
    args = parser.parse_args()

    prd = project_path(args.prd)
    design = project_path(args.technical_design)
    out_dir = (
        project_path(args.out_dir) if args.out_dir else ROOT / "06-backlog" / slug_from_path(prd)
    )

    story_map = parse_story_map(read_text(prd))
    if not story_map.epics:
        raise SystemExit(
            f"No epics found in {display_path(prd)}. Expected headings like "
            "'### E01: Name' followed by a story table (see 04-prd/templates/prd-template.md)."
        )
    epics = select_epics(story_map.epics, args.epic)
    if args.response and len(epics) != 1:
        raise SystemExit("--response needs exactly one --epic.")
    for sid in story_map.unassigned:
        print(f"Warning: {sid} is not under an epic heading in the PRD; it will not be generated.")

    context = bundle_documents("Approved Inputs", [prd, design])
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
        f"| {s.id} | {s.summary} | {s.persona} | {', '.join(s.traces_to)} | {s.priority} |"
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
        write_text(prompt_path, prompt)
        print(f"Wrote prompt: {display_path(prompt_path)}")
        return WROTE

    if args.response:
        response = read_text(project_path(args.response))
    else:
        print(f"Generating {epic.id} ({len(epic.stories)} stories)...")
        response = run_claude(prompt, args.claude_bin, prompt_path)
        if response is None:
            return FALLBACK
    return write_stories(epic, epic_dir, out_dir, response, args.force)


def write_stories(epic: Epic, epic_dir: Path, out_dir: Path, response: str, force: bool) -> str:
    chunks = split_stories(response)
    if not chunks:
        saved = out_dir / "prompts" / f"{epic_dir.name}.response.md"
        write_text(saved, response)
        print(
            f"Error: found no stories in the response for {epic.id} "
            "(expected '<!-- story: US-001 -->' markers). "
            f"Saved the response to {display_path(saved)}; fix it and re-import with "
            f"--epic {epic.id} --response {display_path(saved)}",
            file=sys.stderr,
        )
        return FAILED

    expected = {s.id: s for s in epic.stories}
    seen: set[str] = set()
    written = skipped = 0
    for sid, content in chunks:
        if not sid or sid in seen:
            print(f"Warning: skipped a duplicate or unreadable story marker ({sid or 'no ID'}).")
            continue
        seen.add(sid)
        if sid not in expected:
            print(f"Warning: {sid} is not in {epic.id} in the PRD story map; writing it anyway.")

        meta, _ = parse_frontmatter(content)
        if not meta:
            print(f"Warning: {sid} has no frontmatter; validate_backlog.py will flag it.")
        elif str(meta.get("id", "")).upper() not in {"", sid}:
            print(f"Warning: {sid} has id '{meta.get('id')}' in its frontmatter.")

        existing = files_for_story(out_dir, sid)
        if existing and not force:
            print(
                f"Skipped {sid}: {display_path(existing[0])} already exists (use --force to overwrite)."
            )
            skipped += 1
            continue
        for path in existing:
            path.unlink()

        title_value = meta.get("title")
        title = title_value if isinstance(title_value, str) else ""
        if not title and sid in expected:
            title = expected[sid].summary
        name = slugify(title or "", "story")[:60].strip("-")
        target = epic_dir / f"{sid}-{name}.md"
        write_text(target, content)
        written += 1

    for sid in expected:
        if sid not in seen:
            print(f"Warning: the response has no story for {sid}; re-run with --epic {epic.id}.")
    print(
        f"{epic.id}: wrote {plural(written, 'story', 'stories')} "
        f"to {display_path(epic_dir)}, skipped {skipped}."
    )
    return WROTE if written else SKIPPED


if __name__ == "__main__":
    main()
