#!/usr/bin/env python3
"""Copy a draft document or draft directory to its canonical path.

Promotion is deliberately dumb: it copies bytes and the accompanying provenance
sidecar, and nothing else. It never writes a review record, never records a
decision and never marks anything approved; review status only changes when the
owner records decisions against the promoted document.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

from workflow_common import (
    ROOT,
    canonical_path,
    display_path,
    is_draft_path,
    reject_symlink,
)


def sidecar(path: Path) -> Path:
    return path.with_suffix(".provenance.json")


def promoted_sidecar(source: Path, destination: Path) -> bytes | None:
    """Return rewritten sidecar bytes, keeping the historical status untouched."""
    origin = sidecar(source)
    if not origin.is_file():
        return None
    data = json.loads(origin.read_text(encoding="utf-8"))
    status = data.get("output_review_status")
    if isinstance(status, dict):
        try:
            status["artifact"] = destination.resolve().relative_to(ROOT).as_posix()
        except ValueError:
            status["artifact"] = str(destination)
    data["promoted_from"] = display_path(source)
    data["promoted_at"] = dt.datetime.now(dt.UTC).isoformat()
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_bytes(path: Path, payload: bytes) -> None:
    reject_symlink(path, "output")
    reject_symlink(path.parent, "output parent directory")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def promote_file(source: Path, force: bool) -> str:
    destination = canonical_path(source)
    if destination.exists() and not force:
        raise SystemExit(
            f"{display_path(destination)} already exists; promotion never overwrites "
            "reviewed words. Re-run with --force if you really mean to replace it."
        )
    payload = source.read_bytes()
    write_bytes(destination, payload)
    receipt = promoted_sidecar(source, destination)
    if receipt is not None:
        write_bytes(sidecar(destination), receipt)
    return f"Promoted {display_path(source)} to {display_path(destination)}."


def promote_directory(source: Path, force: bool) -> str:
    destination = canonical_path(source)
    files = sorted(p for p in source.rglob("*") if p.is_file())
    if not files:
        raise SystemExit(f"Nothing to promote: {display_path(source)} is empty.")
    collisions = [
        destination / p.relative_to(source)
        for p in files
        if (destination / p.relative_to(source)).exists()
    ]
    if collisions and not force:
        raise SystemExit(
            f"{display_path(collisions[0])} already exists; promotion never overwrites "
            "reviewed words. Re-run with --force if you really mean to replace it."
        )
    for item in files:
        target = destination / item.relative_to(source)
        if item.name.endswith(".provenance.json"):
            data = json.loads(item.read_text(encoding="utf-8"))
            status = data.get("output_review_status")
            if isinstance(status, dict):
                try:
                    status["artifact"] = target.resolve().relative_to(ROOT).as_posix()
                except ValueError:
                    status["artifact"] = str(target)
            write_bytes(target, (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8"))
            continue
        write_bytes(target, item.read_bytes())
    return f"Promoted {display_path(source)} to {display_path(destination)} ({len(files)} files)."


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("source", help="Draft file (x.draft.md) or draft directory (x.draft).")
    parser.add_argument("--force", action="store_true", help="Replace existing canonical output.")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ROOT / source
    reject_symlink(source, "draft output")
    if not source.exists():
        raise SystemExit(f"Missing draft output: {display_path(source)}")
    if not is_draft_path(source):
        raise SystemExit(
            f"Refusing {display_path(source)}: not a draft path. Promotion only accepts "
            "*.draft.md files and *.draft directories."
        )
    if source.is_dir():
        print(promote_directory(source, args.force))
    else:
        print(promote_file(source, args.force))
    print("Review status is unchanged: promotion never approves anything.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
