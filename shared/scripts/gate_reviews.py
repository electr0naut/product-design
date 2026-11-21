"""Read-only, lane-scoped stakeholder gate evaluation."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

from workflow_common import ROOT, read_text, reject_symlink


def artifact_hash(root: Path, name: str) -> str:
    """Hash a regular, in-repository artifact without following symlinks."""
    if (
        not isinstance(name, str)
        or not name
        or Path(name).is_absolute()
        or ".." in Path(name).parts
    ):
        raise ValueError(f"unsafe artifact path: {name!r}")
    path = root / name
    try:
        reject_symlink(path, "artifact")
        if not path.is_file():
            raise ValueError(f"missing or nonregular artifact: {name}")
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except SystemExit as exc:
        raise ValueError(f"unsafe artifact path: {name}: {exc}") from exc
    except OSError as exc:
        raise ValueError(f"cannot read artifact: {name}: {exc}") from exc


def parsed_timestamp(value: str) -> dt.datetime:
    try:
        timestamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if timestamp.tzinfo is None:
            raise ValueError("timezone required")
        return timestamp
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc


def fields(value: object, required: set[str], optional: set[str] | None = None) -> dict:
    if (
        not isinstance(value, dict)
        or not required <= value.keys()
        or value.keys() - required - (optional or set())
    ):
        raise ValueError(f"invalid review record fields (expected {sorted(required)}): {value!r}")
    return value


def nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonempty string")
    return value


def items(value: object, label: str) -> list:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def day(value: object) -> dt.date:
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("expected ISO date")
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid date: {value!r}") from exc


def validate(data: object, manifest: Path) -> dict:
    """Reject ambiguous or partial review records before computing any status."""
    data = fields(
        data, {"schema_version", "product", "gates", "decisions", "changes", "assumptions"}
    )
    if (
        data["schema_version"] != 1
        or manifest.parent.name != "review"
        or data["product"] != manifest.stem
    ):
        raise ValueError("expected schema_version 1 and review/<product>.json")
    gates: dict[str, dict] = {}
    for entry in items(data["gates"], "gates"):
        gate = fields(entry, {"id", "lanes"})
        gid = nonempty(gate["id"], "gate id")
        if gid in gates or not isinstance(gate["lanes"], dict) or not gate["lanes"]:
            raise ValueError(f"duplicate gate or missing lanes: {gid}")
        gates[gid] = gate["lanes"]
        for lane_id, lane in gate["lanes"].items():
            nonempty(lane_id, "lane id")
            policy = fields(lane, {"roles", "artifacts", "depends_on", "assumptions"})
            roles = items(policy["roles"], "roles")
            artifacts = items(policy["artifacts"], "artifacts")
            if (
                not roles
                or not artifacts
                or len(set(roles)) != len(roles)
                or len(set(artifacts)) != len(artifacts)
            ):
                raise ValueError(f"{gid}/{lane_id} needs unique nonempty roles and artifacts")
            for role in roles:
                nonempty(role, "role")
            for artifact in artifacts:
                if (
                    not isinstance(artifact, str)
                    or not artifact
                    or Path(artifact).is_absolute()
                    or ".." in Path(artifact).parts
                ):
                    raise ValueError(f"unsafe artifact path: {artifact!r}")
            items(policy["depends_on"], "dependencies")
            items(policy["assumptions"], "assumptions")
    if not gates:
        raise ValueError("at least one gate is required")

    def scope(ref: object) -> tuple[str, str]:
        ref = fields(ref, {"gate", "lane"})
        key = (nonempty(ref["gate"], "gate"), nonempty(ref["lane"], "lane"))
        if key[0] not in gates or key[1] not in gates[key[0]]:
            raise ValueError(f"unknown gate/lane scope: {key}")
        return key

    for lanes in gates.values():
        for policy in lanes.values():
            for ref in policy["depends_on"]:
                scope(ref)

    assumptions: set[str] = set()
    for entry in items(data["assumptions"], "assumptions"):
        assumption = fields(entry, {"id", "statement", "source", "checked_at", "review_by"})
        aid = nonempty(assumption["id"], "assumption id")
        if aid in assumptions:
            raise ValueError(f"duplicate assumption: {aid}")
        assumptions.add(aid)
        nonempty(assumption["statement"], "assumption statement")
        nonempty(assumption["source"], "assumption source")
        if day(assumption["review_by"]) < day(assumption["checked_at"]):
            raise ValueError(f"review_by precedes checked_at: {aid}")
    for gid, lanes in gates.items():
        for lane_id, policy in lanes.items():
            ids = items(policy["assumptions"], "lane assumptions")
            if len(ids) != len(set(ids)) or not set(ids) <= assumptions:
                raise ValueError(f"unknown or repeated assumption at {gid}/{lane_id}")

    decision_ids: set[str] = set()
    feedback_ids: set[str] = set()
    for entry in items(data["decisions"], "decisions"):
        decision = fields(
            entry,
            {
                "id",
                "gate",
                "lane",
                "role",
                "reviewer",
                "decision",
                "recorded_at",
                "artifact_sha256",
                "evidence",
                "feedback",
            },
        )
        did = nonempty(decision["id"], "decision id")
        if did in decision_ids:
            raise ValueError(f"duplicate decision: {did}")
        decision_ids.add(did)
        gid, lane_id = scope({"gate": decision["gate"], "lane": decision["lane"]})
        if decision["role"] not in gates[gid][lane_id]["roles"]:
            raise ValueError(f"unknown role at {gid}/{lane_id}: {decision['role']}")
        nonempty(decision["reviewer"], "reviewer")
        nonempty(decision["evidence"], "review evidence")
        parsed_timestamp(decision["recorded_at"])
        if decision["decision"] not in (
            "approve",
            "request_changes",
            "not_applicable",
            "cannot_determine",
        ):
            raise ValueError(f"unknown decision: {decision['decision']}")
        digests = decision["artifact_sha256"]
        if not isinstance(digests, dict) or set(digests) != set(gates[gid][lane_id]["artifacts"]):
            raise ValueError(f"artifact hash keys mismatch at {gid}/{lane_id}")
        if any(
            not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
            for value in digests.values()
        ):
            raise ValueError(f"invalid artifact hash at {gid}/{lane_id}")
        for entry in items(decision["feedback"], "feedback"):
            comment = fields(entry, {"id", "text", "status"}, {"resolution"})
            fid = nonempty(comment["id"], "feedback id")
            if fid in feedback_ids:
                raise ValueError(f"duplicate feedback id: {fid}")
            feedback_ids.add(fid)
            nonempty(comment["text"], "feedback text")
            if comment["status"] not in ("open", "resolved"):
                raise ValueError(f"unknown feedback status: {fid}")
            if comment["status"] == "resolved":
                nonempty(comment.get("resolution"), "feedback resolution")

    change_ids: set[str] = set()
    for entry in items(data["changes"], "changes"):
        change = fields(
            entry,
            {"id", "source", "raised_at", "effective_at", "status", "affected"},
            {"resolved_at"},
        )
        cid = nonempty(change["id"], "change id")
        if cid in change_ids:
            raise ValueError(f"duplicate change: {cid}")
        change_ids.add(cid)
        nonempty(change["source"], "change source")
        day(change["effective_at"])
        raised = parsed_timestamp(change["raised_at"])
        if change["status"] not in ("open", "resolved"):
            raise ValueError(f"unknown change status: {cid}")
        if change["status"] == "resolved" and (
            "resolved_at" not in change or parsed_timestamp(change["resolved_at"]) < raised
        ):
            raise ValueError(f"resolved change requires resolved_at after raised_at: {cid}")
        affected = items(change["affected"], "affected scopes")
        if not affected or len({scope(ref) for ref in affected}) != len(affected):
            raise ValueError(f"change needs distinct affected scopes: {cid}")
    return data


def evaluate_gate(manifest: Path, gate_id: str, lane: str | None = None) -> dict:
    """Return review readiness for a gate and optionally one swimlane."""
    data = validate(json.loads(read_text(manifest)), manifest)
    root = manifest.parent.parent
    gates = {gate["id"]: gate["lanes"] for gate in data["gates"]}
    selected = [lane] if lane else list(gates[gate_id])
    cache: dict[tuple[str, str], dict] = {}
    active: set[tuple[str, str]] = set()

    def status(gid: str, lane_id: str) -> dict:
        key = (gid, lane_id)
        if key in cache:
            return cache[key]
        if key in active:
            raise ValueError(f"dependency cycle at {gid}/{lane_id}")
        active.add(key)
        policy = gates[gid][lane_id]
        expected = {path: artifact_hash(root, path) for path in policy["artifacts"]}
        reasons = []
        for assumption_id in policy["assumptions"]:
            assumption = next(a for a in data["assumptions"] if a["id"] == assumption_id)
            if dt.date.fromisoformat(assumption["review_by"]) < dt.date.today():
                reasons.append(f"expired assumption: {assumption_id}")
        changes = [
            change
            for change in data["changes"]
            if {"gate": gid, "lane": lane_id} in change["affected"]
        ]
        for change in changes:
            if change["status"] == "open":
                reasons.append(f"open change: {change['id']}")
        for role in policy["roles"]:
            decisions = [
                d
                for d in data["decisions"]
                if d["gate"] == gid and d["lane"] == lane_id and d["role"] == role
            ]
            if not decisions:
                reasons.append(f"missing approval: {role}")
                continue
            latest = decisions[-1]
            if latest["decision"] != "approve":
                reasons.append(f"not approved: {role}")
            elif latest["artifact_sha256"] != expected:
                reasons.append(f"stale approval: {role}")
            if any(item["status"] != "resolved" for d in decisions for item in d["feedback"]):
                reasons.append(f"unresolved feedback: {role}")
            for change in changes:
                if change["status"] == "resolved" and parsed_timestamp(
                    latest["recorded_at"]
                ) <= parsed_timestamp(change["resolved_at"]):
                    reasons.append(f"reapproval required after change: {change['id']} ({role})")
        for dependency in policy["depends_on"]:
            upstream = status(dependency["gate"], dependency["lane"])
            if not upstream["ready"]:
                reasons.append(f"blocked dependency: {dependency['gate']}/{dependency['lane']}")
        latest_by_role = {
            role: next(
                (
                    d
                    for d in reversed(data["decisions"])
                    if d["gate"] == gid and d["lane"] == lane_id and d["role"] == role
                ),
                None,
            )
            for role in policy["roles"]
        }
        cache[key] = {
            "ready": not reasons,
            "reasons": reasons,
            "required_roles": policy["roles"],
            "artifacts": policy["artifacts"],
            "assumptions": policy["assumptions"],
            "decisions": {
                role: {
                    "decision": d["decision"],
                    "reviewer": d["reviewer"],
                    "recorded_at": d["recorded_at"],
                    "evidence": d["evidence"],
                }
                for role, d in latest_by_role.items()
                if d
            },
            "feedback": [
                item
                for d in data["decisions"]
                if d["gate"] == gid and d["lane"] == lane_id
                for item in d["feedback"]
            ],
        }
        active.remove(key)
        return cache[key]

    statuses = {lane_id: status(gate_id, lane_id) for lane_id in selected}
    return {"gate": gate_id, "ready": all(s["ready"] for s in statuses.values()), "lanes": statuses}


def add_review_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--review-manifest", type=Path, help="Explicit review/<product>.json")
    parser.add_argument(
        "--draft", action="store_true", help="Explore without unlocking a review gate"
    )


def maybe_enforce_gate(
    args: argparse.Namespace,
    product: str,
    gate_id: str,
    sources: list[Path],
    lanes: list[str] | None = None,
    *,
    partial: bool = False,
) -> None:
    """Block advancement if configured review scopes or sources are unapproved."""
    manifest = args.review_manifest or ROOT / "review" / f"{product}.json"
    if args.draft:
        print("DRAFT ONLY: review gate bypassed explicitly; not approved.", file=sys.stderr)
        return
    if not manifest.exists() and args.review_manifest is None:
        print("DRAFT ONLY: no review manifest configured; not approved.", file=sys.stderr)
        return
    if partial:
        raise SystemExit(
            f"Review gate {gate_id} needs the complete input set; "
            "partial inputs are exploratory only (use --draft)."
        )
    if not lanes:
        report = evaluate_gate(manifest, gate_id)
        statuses = report["lanes"]
    else:
        statuses = {lane: evaluate_gate(manifest, gate_id, lane)["lanes"][lane] for lane in lanes}
    root = manifest.parent.parent
    for lane, state in statuses.items():
        for source in sources:
            reject_symlink(source, "reviewed input")
            try:
                relative = source.relative_to(root).as_posix()
            except ValueError as exc:
                raise SystemExit(
                    f"Review manifest does not cover input outside its product: {source}"
                ) from exc
            if relative not in state["artifacts"]:
                raise SystemExit(f"Review gate {gate_id}/{lane} omits input: {relative}")
        if not state["ready"]:
            raise SystemExit(f"Review gate {gate_id}/{lane} blocked: {'; '.join(state['reasons'])}")
