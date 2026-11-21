#!/usr/bin/env python3
"""Migrate a review manifest from schema v1 to v2.

v1 stored feedback resolution inside the decision and a change's status on the
change record. v2 keeps decisions and change records immutable and records
resolution as events. This migration is deterministic and idempotent.

Exit status: 0 migrated or already current, 1 refused, 2 invalid input.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from gate_reviews import SCHEMA_VERSION, load_manifest
from workflow_common import display_path, project_path, reject_symlink, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--manifest", required=True, help="review/<product>.json")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    args = parser.parse_args()

    manifest = project_path(args.manifest)
    try:
        data = load_manifest(manifest)
    except ValueError as exc:
        print(f"Invalid manifest: {exc}", file=sys.stderr)
        return 2
    if not isinstance(data, dict):
        print("Invalid manifest: expected an object", file=sys.stderr)
        return 2
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        print(f"{display_path(manifest)} is already schema v{SCHEMA_VERSION}.")
        return 0
    if isinstance(version, bool) or version != 1:
        print(f"Refused: unsupported schema_version {version!r}", file=sys.stderr)
        return 1

    feedback_events = []
    change_events = []
    event_number = 0
    feedback_count = 0
    change_count = 0
    for decision in data.get("decisions", []):
        for comment in decision.get("feedback", []):
            if not isinstance(comment, dict):
                continue
            resolved = comment.get("status") == "resolved"
            comment.pop("status", None)
            resolution = comment.pop("resolution", None)
            if not resolved:
                continue
            event_number += 1
            feedback_count += 1
            feedback_events.append(
                {
                    "id": f"FE-{event_number:03d}",
                    "feedback_id": comment.get("id", ""),
                    "action": "resolve",
                    "text": resolution or "resolved before schema v2",
                    "at": decision.get("recorded_at"),
                    "by": "migrated-v1",
                    "evidence": "pre-v2; see git history",
                }
            )
    for change in data.get("changes", []):
        status = change.pop("status", None)
        resolved_at = change.pop("resolved_at", None)
        if status == "resolved":
            event_number += 1
            change_count += 1
            change_events.append(
                {
                    "id": f"CE-{event_number:03d}",
                    "change_id": change.get("id", ""),
                    "action": "resolve",
                    "text": "resolved before schema v2",
                    "at": resolved_at or change.get("raised_at"),
                    "by": "migrated-v1",
                    "evidence": "pre-v2; see git history",
                }
            )
    data["schema_version"] = SCHEMA_VERSION
    for key in ("feedback_events", "change_events", "questions", "question_answers"):
        data.setdefault(key, [])
    data["feedback_events"].extend(feedback_events)
    data["change_events"].extend(change_events)

    try:
        from gate_reviews import validate

        validate(data, manifest)
    except ValueError as exc:
        print(f"Refused: migrated manifest is invalid: {exc}", file=sys.stderr)
        return 1

    print(
        f"Migrated {display_path(manifest)}: {feedback_count} feedback resolution(s), "
        f"{change_count} change(s)."
    )
    if args.dry_run:
        print("Dry run; no file written.")
        return 0
    reject_symlink(manifest, "manifest")
    temporary = manifest.with_name(manifest.name + ".tmp")
    write_text(temporary, json.dumps(data, indent=2, sort_keys=True))
    os.replace(temporary, manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
