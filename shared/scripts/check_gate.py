#!/usr/bin/env python3
"""Report which stakeholder swimlanes are ready to advance."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gate_reviews import evaluate_gate, portal_view


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path, help="review/<product>.json")
    parser.add_argument("--gate", help="Gate ID, e.g. design-to-backlog")
    parser.add_argument("--lane", help="Optional swimlane ID; omit to check the whole gate")
    parser.add_argument("--role", help="Emit the per-role portal view instead of a gate check")
    parser.add_argument(
        "--json", action="store_true", help="Machine-readable status for the review portal"
    )
    args = parser.parse_args()
    if args.role:
        if args.gate or args.lane:
            parser.error("--role cannot be combined with --gate or --lane")
        try:
            view = portal_view(args.manifest, args.role)
        except (ValueError, KeyError, TypeError, OSError, SystemExit) as exc:
            print(f"Invalid review manifest: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(view, indent=2, sort_keys=True))
        return 0
    if not args.gate:
        parser.error("--gate is required unless --role is used")
    try:
        report = evaluate_gate(args.manifest, args.gate, args.lane)
    except (ValueError, KeyError, TypeError, OSError, SystemExit) as exc:
        print(f"Invalid review manifest: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for lane, state in report["lanes"].items():
            print(f"{report['gate']}/{lane}: {'READY' if state['ready'] else 'BLOCKED'}")
            for reason in state["reasons"]:
                print(f"  - {reason}")
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
