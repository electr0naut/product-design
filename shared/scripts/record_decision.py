#!/usr/bin/env python3
"""Record a verified review packet as a decision in a v2 review manifest.

The packet is untrusted input. This command assigns IDs, re-hashes the reviewed
artifacts, refuses a stale approval, refuses out-of-order decisions, and marks
unverified identity explicitly. It never infers a decision from silence.

Exit status: 0 recorded (or verified with --verify), 1 refused, 2 invalid input.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

from gate_reviews import (
    DECISIONS,
    evidence_warning,
    fields,
    latest,
    load_manifest,
    nonempty,
    parsed_timestamp,
    validate,
)
from workflow_common import display_path, project_path, reject_symlink, write_text


def next_id(prefix: str, existing: list[str], width: int = 3) -> str:
    numbers = [int(value[len(prefix) :]) for value in existing if value.startswith(prefix)]
    return f"{prefix}{max(numbers, default=0) + 1:0{width}d}"


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--manifest", required=True, help="review/<product>.json")
    parser.add_argument(
        "--packet", required=True, help="Decision packet produced by the review page"
    )
    parser.add_argument("--evidence", help="Channel reference, e.g. message ID or URL")
    parser.add_argument("--verify", action="store_true", help="Check the packet without writing")
    parser.add_argument(
        "--accept-stale",
        action="store_true",
        help="Allow a non-approval packet whose artifacts changed since review",
    )
    args = parser.parse_args()

    manifest = project_path(args.manifest)
    try:
        data = validate(load_manifest(manifest), manifest)
        packet = json.loads(project_path(args.packet).read_text(encoding="utf-8"))
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid input: {exc}", file=sys.stderr)
        return 2

    try:
        record = fields(
            packet,
            {
                "schema_version",
                "product",
                "gate",
                "lane",
                "role",
                "decision",
                "reviewer",
                "artifact_sha256",
                "feedback",
                "created_at",
            },
            {"source_commit", "evidence"},
        )
    except ValueError as exc:
        print(f"Invalid packet: {exc}", file=sys.stderr)
        return 2
    if record["schema_version"] != 1 or record["product"] != data["product"]:
        print("Invalid packet: wrong schema_version or product", file=sys.stderr)
        return 2
    gates = {gate["id"]: gate["lanes"] for gate in data["gates"]}
    gate_id, lane_id = record["gate"], record["lane"]
    if gate_id not in gates or lane_id not in gates[gate_id]:
        print(f"Invalid packet: unknown scope {gate_id}/{lane_id}", file=sys.stderr)
        return 2
    policy = gates[gate_id][lane_id]
    if record["role"] not in policy["roles"]:
        print(
            f"Invalid packet: {record['role']} is not required at {gate_id}/{lane_id}",
            file=sys.stderr,
        )
        return 2
    if record["decision"] not in DECISIONS:
        print(f"Invalid packet: unknown decision {record['decision']!r}", file=sys.stderr)
        return 2
    try:
        nonempty(record["reviewer"], "reviewer")
        created = parsed_timestamp(record["created_at"])
    except ValueError as exc:
        print(f"Invalid packet: {exc}", file=sys.stderr)
        return 2
    evidence = args.evidence or record.get("evidence", "")
    try:
        nonempty(evidence, "evidence")
    except ValueError:
        print("Refused: --evidence or packet evidence is required", file=sys.stderr)
        return 1

    from gate_reviews import artifact_hash

    root = manifest.parent.parent
    expected = {path: artifact_hash(root, path) for path in policy["artifacts"]}
    hashes = record["artifact_sha256"]
    if not isinstance(hashes, dict) or set(hashes) != set(expected):
        print("Refused: packet artifact list does not match the lane", file=sys.stderr)
        return 1
    stale = sorted(path for path in expected if hashes[path] != expected[path])
    if stale:
        if record["decision"] == "approve":
            print(
                f"Refused: stale approval; changed after review: {', '.join(stale)}",
                file=sys.stderr,
            )
            return 1
        if not args.accept_stale:
            print(
                "Refused: artifacts changed since the packet was written "
                f"({', '.join(stale)}); use --accept-stale for a non-approval",
                file=sys.stderr,
            )
            return 1

    previous = latest(data["decisions"], gate=gate_id, lane=lane_id, role=record["role"])
    if previous is not None and created <= parsed_timestamp(previous["recorded_at"]):
        print(
            "Refused: packet predates that role's latest decision "
            f"({previous['id']} at {previous['recorded_at']})",
            file=sys.stderr,
        )
        return 1

    warning = evidence_warning(evidence)
    if warning:
        print(f"Warning: {warning}", file=sys.stderr)

    decision_ids = [d["id"] for d in data["decisions"]]
    feedback_ids = [c["id"] for d in data["decisions"] for c in d["feedback"]]
    decision_id = next_id("D-", decision_ids)
    feedback = []
    for comment in record["feedback"]:
        text = comment.get("text") if isinstance(comment, dict) else None
        try:
            nonempty(text, "feedback text")
        except ValueError as exc:
            print(f"Invalid packet: {exc}", file=sys.stderr)
            return 2
        fid = next_id("F-", feedback_ids)
        feedback_ids.append(fid)
        feedback.append({"id": fid, "text": text})

    stamp = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    decision = {
        "id": decision_id,
        "gate": gate_id,
        "lane": lane_id,
        "role": record["role"],
        "reviewer": record["reviewer"],
        "decision": record["decision"],
        "recorded_at": stamp,
        "artifact_sha256": expected,
        "evidence": evidence,
        "feedback": feedback,
        "source_commit": record.get("source_commit", ""),
        "recorded_by": "record_decision",
        "attestation": "typed-name, unverified",
    }
    print(
        f"{decision_id}: {record['decision']} by {record['reviewer']} "
        f"({record['role']}) for {gate_id}/{lane_id}"
    )
    for comment in feedback:
        print(f"  {comment['id']}: {comment['text']}")
    if args.verify:
        print("Verified only; no file written.")
        return 0

    data["decisions"].append(decision)
    reject_symlink(manifest, "manifest")
    temporary = manifest.with_name(manifest.name + ".tmp")
    write_text(temporary, json.dumps(data, indent=2, sort_keys=True))
    os.replace(temporary, manifest)
    print(f"Recorded in {display_path(manifest)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
