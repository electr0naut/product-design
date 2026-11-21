"""Read and check the phase-06 backlog.

Parses BRD requirement IDs, the PRD story map (epics and story rows) and the
story files in `06-backlog/<product>/`, and checks that they trace to each
other. Standard library only.
"""

from __future__ import annotations

import heapq
import re
from dataclasses import dataclass, field
from pathlib import Path

from workflow_common import is_prompt_file, read_text, reject_symlink

REQUIREMENT_REF = re.compile(r"\b(BR|NFR)-(\d+)\b", re.IGNORECASE)
STORY_REF = re.compile(r"\bUS-(\d+)\b", re.IGNORECASE)
EPIC_HEADING = re.compile(
    r"^(#{2,6})\s*(?:Epic\s+)?E-?(\d+)\b\s*[:.\-–—]?\s*(.*?)\s*$",
    re.IGNORECASE,
)
HEADING = re.compile(r"^(#{1,6})\s")
CELL_SEPARATOR = re.compile(r"(?<!\\)(?:\\\\)*\|")
STORY_MARKER = re.compile(
    r"^[ \t]*<!--\s*story:\s*(US-\d+)\s*-->[ \t]*$", re.IGNORECASE | re.MULTILINE
)
STORY_MARKER_LIKE = re.compile(r"<!--\s*story\s*:", re.IGNORECASE)
GIVEN_WHEN_THEN = re.compile(r"\bgiven\b.*\bwhen\b.*\bthen\b", re.IGNORECASE)

PRIORITY_RANK = {"must": 0, "should": 1, "could": 2, "won't": 3, "wont": 3}


# ---------------------------------------------------------------------------
# IDs


def requirement_id(prefix: str, number: str) -> str:
    return f"{prefix.upper()}-{int(number):03d}"


def story_id(number: str) -> str:
    return f"US-{int(number):03d}"


def epic_id(number: str) -> str:
    return f"E{int(number):02d}"


def normalize_epic_id(value: str) -> str:
    match = re.search(r"\bE-?(\d+)\b", value or "", re.IGNORECASE)
    return epic_id(match.group(1)) if match else ""


def requirement_refs(text: str) -> list[str]:
    return _unique(requirement_id(p, n) for p, n in REQUIREMENT_REF.findall(text or ""))


def story_refs(text: str) -> list[str]:
    return _unique(story_id(n) for n in STORY_REF.findall(text or ""))


def priority_rank(value: str) -> int:
    word = (value or "").replace("’", "'").strip().lower().split(" ")[0].strip(".,;:*")
    return PRIORITY_RANK.get(word, len(PRIORITY_RANK))


def _unique(items) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        seen.setdefault(item, None)
    return list(seen)


# ---------------------------------------------------------------------------
# BRD


@dataclass
class Requirement:
    id: str
    text: str


def parse_requirements(brd_text: str) -> dict[str, Requirement]:
    """Return BR-xxx and NFR-xxx rows from the BRD requirement tables."""
    requirements: dict[str, Requirement] = {}
    for line in brd_text.splitlines():
        cells = _table_cells(line)
        if not cells:
            continue
        match = REQUIREMENT_REF.fullmatch(cells[0])
        if not match:
            continue
        req_id = requirement_id(*match.groups())
        text = cells[1] if len(cells) > 1 else ""
        requirements.setdefault(req_id, Requirement(req_id, text))
    return requirements


# ---------------------------------------------------------------------------
# PRD story map


@dataclass
class StoryRef:
    """One row of the PRD story map."""

    id: str
    epic: str
    summary: str
    persona: str
    traces_to: list[str]
    priority: str


@dataclass
class Epic:
    id: str
    name: str
    stories: list[StoryRef] = field(default_factory=list)


@dataclass
class StoryMap:
    epics: dict[str, Epic] = field(default_factory=dict)
    stories: dict[str, StoryRef] = field(default_factory=dict)
    duplicates: list[str] = field(default_factory=list)
    unassigned: list[str] = field(default_factory=list)
    non_goals: list[str] = field(default_factory=list)


def parse_story_map(prd_text: str) -> StoryMap:
    """Read epics (`### E01: Name`) and their story table rows (`| US-001 | ...`)."""
    story_map = StoryMap(non_goals=_non_goal_refs(prd_text))
    current: Epic | None = None
    epic_level = 0
    header: list[str] | None = None

    for line in prd_text.splitlines():
        heading = EPIC_HEADING.match(line)
        if heading:
            level, number, name = heading.groups()
            eid = epic_id(number)
            current = story_map.epics.setdefault(eid, Epic(eid, name.strip() or eid))
            epic_level = len(level)
            header = None
            continue
        other = HEADING.match(line)
        if other and current is not None and len(other.group(1)) <= epic_level:
            current = None
            header = None
            continue

        cells = _table_cells(line)
        if not cells:
            continue
        if cells[0].lower() in {"id", "story id", "story"} and len(cells) > 1:
            header = [cell.lower() for cell in cells]
            continue
        if not STORY_REF.fullmatch(cells[0]):
            continue

        ref = _story_row(cells, header, current.id if current else "")
        if ref.id in story_map.stories:
            story_map.duplicates.append(ref.id)
            continue
        story_map.stories[ref.id] = ref
        if current is None:
            story_map.unassigned.append(ref.id)
        else:
            current.stories.append(ref)
    return story_map


def _story_row(cells: list[str], header: list[str] | None, epic: str) -> StoryRef:
    def column(names: tuple[str, ...], default: int) -> str:
        index = default
        if header:
            for position, title in enumerate(header):
                if position > 0 and any(name in title for name in names):
                    index = position
                    break
        return cells[index] if index < len(cells) else ""

    traces_cell = column(("trace", "requirement", "br"), 3)
    traces = requirement_refs(traces_cell) or requirement_refs(" ".join(cells[1:]))
    match = STORY_REF.fullmatch(cells[0])
    if match is None:
        raise ValueError(f"Invalid story ID cell: {cells[0]!r}")
    return StoryRef(
        id=story_id(match.group(1)),
        epic=epic,
        summary=column(("story", "summary", "title"), 1),
        persona=column(("persona", "user"), 2),
        traces_to=traces,
        priority=column(("priority",), 4),
    )


def _non_goal_refs(prd_text: str) -> list[str]:
    """Requirement IDs the PRD lists under Non-Goals (out of scope on purpose)."""
    match = re.search(
        r"Non-Goals\b(.*?)(?=^#|\Z)", prd_text, re.IGNORECASE | re.DOTALL | re.MULTILINE
    )
    return requirement_refs(match.group(1)) if match else []


def _table_cells(line: str) -> list[str]:
    """Cells of a markdown table row; the first (ID) cell loses bold/code marks.

    Splits only on unescaped pipes, so `\\|` inside a cell (as in "delimiter
    `\\|`") stays in the cell, unescaped to `|`.
    """
    stripped = line.strip()
    if not stripped.startswith("|"):
        return []
    parts = []
    start = 0
    for separator in CELL_SEPARATOR.finditer(stripped):
        backslashes = separator.end() - separator.start() - 1
        parts.append(stripped[start : separator.start()] + "\\" * (backslashes // 2))
        start = separator.end()
    parts.append(stripped[start:])
    parts = parts[1:]  # drop the empty text before the leading pipe
    if len(parts) > 1 and not parts[-1].strip():
        parts = parts[:-1]  # drop the empty text after the trailing pipe
    cells = [
        re.sub(r"(\\+)\|", lambda match: "\\" * (len(match.group(1)) // 2) + "|", part.strip())
        for part in parts
    ]
    cells[0] = cells[0].strip("*`_ ")
    return cells


def table_cell(text: str) -> str:
    """Escape text for one markdown table cell."""
    normalized = (text or "").replace("\n", " ").strip()
    return re.sub(
        r"(\\*)\|",
        lambda match: "\\" * (2 * len(match.group(1)) + 1) + "|",
        normalized,
    )


# ---------------------------------------------------------------------------
# Story files


def parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """Parse a small YAML subset: `key: value`, `key: [a, b]` and `- item` lists."""
    lines = text.lstrip("﻿").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return {}, text

    meta: dict[str, object] = {}
    key = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        item = re.match(r"^\s*-\s+(.*)$", raw)
        if item and key is not None:
            items = meta.get(key)
            if not isinstance(items, list):
                items = []
                meta[key] = items
            items.append(_scalar(item.group(1)))
            continue
        pair = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", raw)
        if not pair:
            continue
        key = pair.group(1).lower().replace("-", "_")
        value = pair.group(2).strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            meta[key] = [_scalar(v) for v in inner.split(",") if v.strip()] if inner else []
        else:
            meta[key] = _scalar(value)
    return meta, "\n".join(lines[end + 1 :])


def _scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


@dataclass
class Story:
    path: Path
    meta: dict[str, object]
    body: str

    @classmethod
    def load(cls, path: Path) -> Story:
        meta, body = parse_frontmatter(read_text(path))
        return cls(path, meta, body)

    def text(self, key: str) -> str:
        value = self.meta.get(key, "")
        return ", ".join(value) if isinstance(value, list) else str(value)

    @property
    def id(self) -> str:
        value = self.text("id")
        return value if re.fullmatch(r"US-\d{3}", value) else ""

    @property
    def title(self) -> str:
        return self.text("title")

    @property
    def epic(self) -> str:
        value = self.text("epic")
        return value if re.fullmatch(r"E\d{2}", value) else ""

    @property
    def traces_to(self) -> list[str]:
        return requirement_refs(self.text("traces_to"))

    @property
    def depends_on(self) -> list[str]:
        return story_refs(self.text("depends_on"))

    @property
    def priority(self) -> str:
        return self.text("priority")

    @property
    def estimate(self) -> str:
        return self.text("estimate").upper()

    def has_acceptance_criteria(self) -> bool:
        return any(GIVEN_WHEN_THEN.search(line) for line in self.body.splitlines())

    def has_tasks(self) -> bool:
        section = _section(self.body, "Tasks")
        return any(re.match(r"^\s*[-*]\s+\S", line) for line in section.splitlines())


def _section(body: str, title: str) -> str:
    match = re.search(
        rf"^#+\s*{re.escape(title)}\b.*?$(.*?)(?=^#|\Z)",
        body,
        re.IGNORECASE | re.DOTALL | re.MULTILINE,
    )
    return match.group(1) if match else ""


def is_story_file(path: Path, backlog_dir: Path) -> bool:
    relative = path.relative_to(backlog_dir).parts
    return (
        path.suffix == ".md"
        and path.name.upper().startswith("US-")
        and not is_prompt_file(path)
        and "templates" not in relative
        and "prompts" not in relative
    )


def story_files(backlog_dir: Path) -> list[Path]:
    reject_symlink(backlog_dir, "backlog directory")
    if not backlog_dir.exists():
        return []
    files = sorted(p for p in backlog_dir.rglob("*.md") if is_story_file(p, backlog_dir))
    for path in files:
        reject_symlink(path, "story file")
    return files


def files_for_story(backlog_dir: Path, sid: str) -> list[Path]:
    """Existing files for a story ID, named `US-001.md` or `US-001-<title>.md`."""
    return [
        path
        for path in story_files(backlog_dir)
        if path.stem.upper() == sid or path.stem.upper().startswith(f"{sid}-")
    ]


def load_stories(backlog_dir: Path) -> list[Story]:
    return [Story.load(path) for path in story_files(backlog_dir)]


def split_stories(response: str) -> list[tuple[str, str]]:
    """Split a model response on `<!-- story: US-001 -->` markers.

    Text before the first marker (a preamble) is dropped, and code fences
    around a story are removed.
    """
    markers = list(STORY_MARKER.finditer(response))
    if len(markers) != len(STORY_MARKER_LIKE.findall(response)):
        raise ValueError("Malformed story marker; expected <!-- story: US-001 --> on its own line.")
    chunks = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(response)
        chunks.append((marker.group(1), _strip_fences(response[marker.end() : end])))
    return chunks


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
    if text.count("```") % 2 == 1 and text.rstrip().endswith("```"):
        text = text.rstrip()[:-3]
    return text.strip()


# ---------------------------------------------------------------------------
# Checks


@dataclass
class Check:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    coverage: dict[str, list[str]] = field(default_factory=dict)
    planned: dict[str, list[str]] = field(default_factory=dict)
    build_order: list[Story] = field(default_factory=list)
    stories: dict[str, Story] = field(default_factory=dict)


def check_backlog(
    requirements: dict[str, Requirement],
    story_map: StoryMap,
    stories: list[Story],
    backlog_dir: Path,
) -> Check:
    check = Check()

    def where(story: Story) -> str:
        try:
            return str(story.path.relative_to(backlog_dir))
        except ValueError:
            return str(story.path)

    # Story files: identity and required fields.
    for story in stories:
        if not story.meta:
            check.errors.append(
                f"{where(story)}: no frontmatter (expected the story template's --- block)."
            )
            continue
        if not story.id:
            check.errors.append(f"{where(story)}: missing or invalid `id`.")
            continue
        if not re.fullmatch(rf"{re.escape(story.id)}(?:-[^/]+)?\.md", story.path.name):
            check.errors.append(
                f"{where(story)}: filename does not match canonical frontmatter id {story.id}."
            )
            continue
        if story.id in check.stories:
            check.errors.append(
                f"{story.id}: duplicate ID in {where(story)} and {where(check.stories[story.id])}."
            )
            continue
        check.stories[story.id] = story

    for sid, story in check.stories.items():
        if not story.epic:
            check.errors.append(f"{sid}: missing or invalid `epic` (expected E01).")
        if not story.traces_to:
            check.errors.append(
                f"{sid}: `traces_to` is empty; every story must trace to a BRD requirement."
            )
        for req in story.traces_to:
            if req not in requirements:
                check.errors.append(f"{sid}: traces to {req}, which is not in the BRD.")
        for dep in story.depends_on:
            if dep == sid:
                check.errors.append(f"{sid}: depends on itself.")
            elif dep not in check.stories and dep not in story_map.stories:
                check.errors.append(
                    f"{sid}: depends on {dep}, which is not in the backlog or the PRD story map."
                )

        ref = story_map.stories.get(sid)
        if ref is None:
            check.warnings.append(f"{sid}: not in the PRD story map (added outside the PRD?).")
        else:
            if story.epic and ref.epic and story.epic != ref.epic:
                check.warnings.append(
                    f"{sid}: epic is {story.epic} but the PRD story map puts it in {ref.epic}."
                )
            dropped = [req for req in ref.traces_to if req not in story.traces_to]
            if dropped:
                check.warnings.append(
                    f"{sid}: drops {', '.join(dropped)}, which the PRD story map traces it to."
                )
        if not story.has_acceptance_criteria():
            check.warnings.append(f"{sid}: no Given/When/Then acceptance criteria.")
        if not story.has_tasks():
            check.warnings.append(f"{sid}: no tasks.")
        if story.estimate in {"", "XL"}:
            reason = "is XL; split it in the PRD story map" if story.estimate else "has no estimate"
            check.warnings.append(f"{sid}: {reason}.")
        for dep in story.depends_on:
            other = check.stories.get(dep)
            if other and priority_rank(other.priority) > priority_rank(story.priority):
                check.warnings.append(
                    f"{sid} ({story.priority or 'no priority'}) depends on {dep} "
                    f"({other.priority or 'no priority'}), which has a lower priority."
                )

    # PRD story map against story files.
    for sid in story_map.duplicates:
        check.errors.append(f"{sid}: listed more than once in the PRD story map.")
    for sid in story_map.unassigned:
        check.warnings.append(f"{sid}: in the PRD story map but not under an epic heading.")
    for sid in story_map.stories:
        if sid not in check.stories:
            check.warnings.append(f"{sid}: in the PRD story map but has no story file yet.")
    for req in story_map.non_goals:
        if req not in requirements:
            check.warnings.append(f"PRD Non-Goals mention {req}, which is not in the BRD.")

    # Requirement coverage.
    for req in requirements:
        check.coverage[req] = [sid for sid, s in check.stories.items() if req in s.traces_to]
        check.planned[req] = [
            sid
            for sid, ref in story_map.stories.items()
            if req in ref.traces_to and sid not in check.stories
        ]
        if check.coverage[req] or req in story_map.non_goals:
            continue
        if req.startswith("BR-") and not check.planned[req]:
            check.errors.append(
                f"{req}: no story covers it (add a story or list it under Non-Goals in the PRD)."
            )

    order, cycle = _build_order(check.stories)
    check.build_order = order
    if cycle:
        check.errors.append(f"Dependency cycle: {' -> '.join(cycle)}.")
    return check


def _build_order(stories: dict[str, Story]) -> tuple[list[Story], list[str]]:
    """Order stories so dependencies come first; ties go by priority, epic, ID."""
    deps = {
        sid: [d for d in s.depends_on if d in stories and d != sid] for sid, s in stories.items()
    }
    dependents: dict[str, list[str]] = {sid: [] for sid in stories}
    for sid, ds in deps.items():
        for dep in ds:
            dependents[dep].append(sid)
    remaining = {sid: len(ds) for sid, ds in deps.items()}

    def key(sid: str) -> tuple[int, str, str]:
        story = stories[sid]
        return (priority_rank(story.priority), story.epic or "E99", sid)

    ready = [key(sid) for sid, count in remaining.items() if count == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        sid = heapq.heappop(ready)[2]
        order.append(stories[sid])
        for dependent in dependents[sid]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0:
                heapq.heappush(ready, key(dependent))

    if len(order) == len(stories):
        return order, []
    stuck = {sid for sid, count in remaining.items() if count > 0}
    return order, _find_cycle(deps, stuck)


def _find_cycle(deps: dict[str, list[str]], nodes: set[str]) -> list[str]:
    for start in sorted(nodes):
        path, seen = [start], {start}
        node = start
        while True:
            node = next((d for d in sorted(deps[node]) if d in nodes), None)
            if node is None:
                break
            if node in seen:
                return path[path.index(node) :] + [node]
            path.append(node)
            seen.add(node)
    return sorted(nodes)
