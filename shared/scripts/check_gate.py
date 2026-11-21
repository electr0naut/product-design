#!/usr/bin/env python3
"""Report which stakeholder swimlanes are ready to advance."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from gate_reviews import artifact_status, evaluate_gate, load_manifest, portal_view, validate
from workflow_common import ROOT


def all_products(manifest_dir: Path, today: dt.date) -> list[dict]:
    reports = []
    for manifest in sorted(manifest_dir.glob("*.json")):
        if manifest.stem == "EXAMPLE":
            continue
        try:
            data = validate(load_manifest(manifest), manifest)
        except ValueError as exc:
            reports.append({"product": manifest.stem, "error": str(exc)})
            continue
        gates = {}
        for gate in data["gates"]:
            try:
                report = evaluate_gate(manifest, gate["id"], today=today)
            except (ValueError, KeyError, TypeError, OSError, SystemExit) as exc:
                gates[gate["id"]] = {"error": str(exc)}
                continue
            gates[gate["id"]] = {
                "ready": report["ready"],
                "lanes": {
                    lane: {
                        "ready": state["ready"],
                        "reasons": state["reasons"],
                        "stale_roles": state["stale_roles"],
                    }
                    for lane, state in report["lanes"].items()
                },
            }
        reports.append({"product": data["product"], "gates": gates})
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, help="review/<product>.json")
    parser.add_argument("--gate", help="Gate ID, e.g. design-to-backlog")
    parser.add_argument("--lane", help="Optional swimlane ID; omit to check the whole gate")
    parser.add_argument("--artifact", type=Path, help="Project the live review status of one file")
    parser.add_argument(
        "--warning-days",
        type=int,
        default=7,
        help="Non-blocking assumption warning lead time (default: 7)",
    )
    parser.add_argument("--role", help="Emit the per-role portal view instead of a gate check")
    parser.add_argument("--all", action="store_true", help="Report every product, gate and lane")
    parser.add_argument(
        "--today", help="Evaluate assumption expiry as of this ISO date (reproducible reports)"
    )
    parser.add_argument(
        "--json", action="store_true", help="Machine-readable status for the review portal"
    )
    args = parser.parse_args()
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        print(f"Invalid --today date: {args.today!r}", file=sys.stderr)
        return 2
    if args.artifact:
        if args.gate or args.lane or args.role or args.all:
            parser.error("--artifact cannot be combined with --gate, --lane, --role or --all")
        try:
            path = args.artifact if args.artifact.is_absolute() else ROOT / args.artifact
            manifest = (
                args.manifest
                if args.manifest is None or args.manifest.is_absolute()
                else Path.cwd() / args.manifest
            )
            report = artifact_status(manifest, path, today=today, warning_days=args.warning_days)
        except (ValueError, TypeError, KeyError, OSError, SystemExit) as exc:
            print(f"Invalid review artifact: {exc}", file=sys.stderr)
            return 2
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"{path}: {report['status'].upper()}")
            for scope in report["scopes"]:
                for reason in scope["reasons"]:
                    print(f"  {scope['gate']}/{scope['lane']}: {reason}")
            for warning in report["warnings"]:
                print(f"  Warning: {warning['assumption']} review by {warning['review_by']}")
        return 0 if report["status"] == "approved" else 1
    if args.all:
        manifest_dir = args.manifest.parent if args.manifest else ROOT / "review"
        products = all_products(manifest_dir, today)
        if args.json:
            print(
                json.dumps(
                    {"today": today.isoformat(), "products": products}, indent=2, sort_keys=True
                )
            )
        else:
            for product in products:
                if "error" in product:
                    print(f"{product['product']}: INVALID — {product['error']}")
                    continue
                for gate, report in product["gates"].items():
                    if "error" in report:
                        print(f"{product['product']}/{gate}: INVALID — {report['error']}")
                        continue
                    for lane, state in report["lanes"].items():
                        print(
                            f"{product['product']}/{gate}/{lane}: "
                            f"{'READY' if state['ready'] else 'BLOCKED'}"
                        )
                        for reason in state["reasons"]:
                            print(f"  - {reason}")
        return 2 if any("error" in product for product in products) else 0
    if args.role:
        if not args.manifest:
            parser.error("--manifest is required with --role")
        if args.gate or args.lane:
            parser.error("--role cannot be combined with --gate or --lane")
        try:
            view = portal_view(args.manifest, args.role)
        except (ValueError, KeyError, TypeError, OSError, SystemExit) as exc:
            print(f"Invalid review manifest: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(view, indent=2, sort_keys=True))
        return 0
    if not args.manifest or not args.gate:
        parser.error("--manifest and --gate are required unless --all or --role is used")
    try:
        report = evaluate_gate(args.manifest, args.gate, args.lane, today=today)
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
