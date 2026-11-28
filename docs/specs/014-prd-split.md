# Split PRD and Epic Isolation

## Problem

Every epic lane hashed the shared PRD, so editing E02 staled E01's approval, and
`generate_stories --epic E01` still bundled all of E02 — including content
nobody had approved.

## Scope

- `split_prd.py` converts a monolithic PRD into `core.md` (overview, NFRs, UX,
  release) and `epics/E01.md`, `epics/E02.md` (epic goal, story table, open
  questions). It preserves epic blocks, refuses duplicate IDs, non-contiguous
  epics and a second split.
- `parse_story_map_path` reads either a monolithic PRD or a split directory.
- `generate_stories.py --prd <dir> --epic E01` bundles `core.md`, `epics/E01.md`
  and the design only. The prompt cannot contain another epic's bytes.
- `validate_backlog.py --prd <dir>` reads the split files and records each hash
  in the backlog lock.
- Manifests can therefore declare epic lanes whose artifacts are the epic file,
  with `core.md`/design either per lane or in a cross-cutting lane.

## Invariants

- Editing one epic file does not stale another epic lane that does not declare
  it.
- Editing `core.md` stales every lane that declares it.
- The splitter is explicit; generation never rewrites reviewed PRD files.
- The technical design remains shared until it is split the same way; that
  limitation is stated rather than implied away.

## Acceptance criteria

- [x] Splitting preserves epic content and refuses to overwrite existing epics.
- [x] `generate_stories --epic E01` succeeds while E02 lacks approval and its
  prompt contains no E02 text.
- [x] Editing E02 leaves E01 ready and E02 blocked.
- [x] A directory without `core.md` and `epics/*.md` fails with a splitter hint.
