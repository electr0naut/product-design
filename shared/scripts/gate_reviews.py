"""Read-only, lane-scoped stakeholder gate evaluation (manifest schema v2)."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

from workflow_common import ROOT, project_path, read_text, reject_symlink

SCHEMA_VERSION = 2
SKEW = dt.timedelta(minutes=5)
DECISIONS = ("approve", "request_changes", "not_applicable", "cannot_determine")
EVIDENCE_REF = re.compile(r"^(https?://\S+|[A-Za-z][A-Za-z0-9]*-\d+|\S+#\d+)$")


def unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(manifest: Path) -> dict:
    """Parse a manifest, rejecting duplicate keys and malformed JSON."""
    try:
        return json.loads(read_text(manifest), object_pairs_hook=unique_pairs)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {manifest}: {exc}") from exc


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
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"invalid timestamp: {value!r}") from exc
    if timestamp > dt.datetime.now(dt.UTC) + SKEW:
        raise ValueError(f"timestamp is in the future: {value}")
    return timestamp


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


def evidence_warning(evidence: str) -> str | None:
    """Free-text evidence is allowed but flagged, never silently trusted."""
    if EVIDENCE_REF.fullmatch(evidence):
        return None
    return f"evidence is free text, not a URL or ticket reference: {evidence!r}"


def check_order(
    records: list[dict],
    key_fields: tuple[str, ...],
    label: str,
    stamp_field: str = "at",
) -> None:
    latest_seen: dict[tuple, dt.datetime] = {}
    for record in records:
        key = tuple(record[field] for field in key_fields)
        at = parsed_timestamp(record[stamp_field])
        if key in latest_seen and at < latest_seen[key]:
            raise ValueError(f"{label} out of time order for {key}: {record['id']}")
        latest_seen[key] = at


def validate(data: object, manifest: Path) -> dict:
    """Reject ambiguous, stale or partial review records before computing status."""
    data = fields(
        data,
        {
            "schema_version",
            "product",
            "gates",
            "decisions",
            "feedback_events",
            "changes",
            "change_events",
            "assumptions",
            "questions",
            "question_answers",
        },
    )
    schema = data["schema_version"]
    if isinstance(schema, bool) or not isinstance(schema, int) or schema != SCHEMA_VERSION:
        raise ValueError(
            f"expected schema_version {SCHEMA_VERSION}; "
            "run shared/scripts/migrate_manifest.py for older manifests"
        )
    if manifest.parent.name != "review" or data["product"] != manifest.stem:
        raise ValueError("expected review/<product>.json matching the product field")

    gates: dict[str, dict] = {}
    for entry in items(data["gates"], "gates"):
        gate = fields(entry, {"id", "lanes"})
        gid = nonempty(gate["id"], "gate id")
        if gid in gates or not isinstance(gate["lanes"], dict) or not gate["lanes"]:
            raise ValueError(f"duplicate gate or missing lanes: {gid}")
        gates[gid] = gate["lanes"]
        for lane_id, lane in gate["lanes"].items():
            nonempty(lane_id, "lane id")
            policy = fields(lane, {"roles", "artifacts", "depends_on", "assumptions"}, {"epic"})
            if "epic" in policy and not isinstance(policy["epic"], bool):
                raise ValueError(f"{gid}/{lane_id} epic must be a boolean")
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

    graph = {
        (gid, lane_id): [scope(ref) for ref in policy["depends_on"]]
        for gid, lanes in gates.items()
        for lane_id, policy in lanes.items()
    }
    visiting: set[tuple[str, str]] = set()
    done: set[tuple[str, str]] = set()

    def walk(node: tuple[str, str]) -> None:
        if node in done:
            return
        if node in visiting:
            raise ValueError(f"dependency cycle at {node[0]}/{node[1]}")
        visiting.add(node)
        for upstream in graph[node]:
            walk(upstream)
        visiting.remove(node)
        done.add(node)

    for node in graph:
        walk(node)

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
    feedback_ids: dict[str, tuple[str, str]] = {}
    feedback_raised: dict[str, dt.datetime] = {}
    decisions: list[dict] = items(data["decisions"], "decisions")
    for entry in decisions:
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
            {"source_commit", "recorded_by", "attestation"},
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
        if "source_commit" in decision and not isinstance(decision["source_commit"], str):
            raise ValueError(f"source_commit must be a string: {did}")
        if "attestation" in decision and decision["attestation"] not in (
            "typed-name, unverified",
            "verified",
        ):
            raise ValueError(f"unknown attestation: {decision['attestation']}")
        if decision["decision"] not in DECISIONS:
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
            comment = fields(entry, {"id", "text"})
            fid = nonempty(comment["id"], "feedback id")
            if fid in feedback_ids:
                raise ValueError(f"duplicate feedback id: {fid}")
            feedback_ids[fid] = (gid, lane_id)
            feedback_raised[fid] = parsed_timestamp(decision["recorded_at"])
            nonempty(comment["text"], "feedback text")
    check_order(decisions, ("gate", "lane", "role"), "decision", "recorded_at")

    event_ids: set[str] = set()
    feedback_events: list[dict] = items(data["feedback_events"], "feedback_events")
    for entry in feedback_events:
        event = fields(entry, {"id", "feedback_id", "action", "text", "at", "by", "evidence"})
        eid = nonempty(event["id"], "feedback event id")
        if eid in event_ids:
            raise ValueError(f"duplicate feedback event: {eid}")
        event_ids.add(eid)
        if event["feedback_id"] not in feedback_ids:
            raise ValueError(f"unknown feedback id in event: {event['feedback_id']}")
        if event["action"] not in ("resolve", "reopen"):
            raise ValueError(f"unknown feedback action: {event['action']}")
        nonempty(event["text"], "feedback event text")
        nonempty(event["by"], "feedback event author")
        nonempty(event["evidence"], "feedback event evidence")
        at = parsed_timestamp(event["at"])
        if at < feedback_raised[event["feedback_id"]]:
            raise ValueError(f"feedback event predates its comment: {event['id']}")
    check_order(feedback_events, ("feedback_id",), "feedback event")

    change_ids: set[str] = set()
    change_raised: dict[str, dt.datetime] = {}
    changes: list[dict] = items(data["changes"], "changes")
    for entry in changes:
        change = fields(entry, {"id", "source", "raised_at", "effective_at", "affected"})
        cid = nonempty(change["id"], "change id")
        if cid in change_ids:
            raise ValueError(f"duplicate change: {cid}")
        change_ids.add(cid)
        nonempty(change["source"], "change source")
        day(change["effective_at"])
        change_raised[cid] = parsed_timestamp(change["raised_at"])
        affected = items(change["affected"], "affected scopes")
        if not affected or len({scope(ref) for ref in affected}) != len(affected):
            raise ValueError(f"change needs distinct affected scopes: {cid}")

    change_events: list[dict] = items(data["change_events"], "change_events")
    for entry in change_events:
        event = fields(entry, {"id", "change_id", "action", "text", "at", "by", "evidence"})
        eid = nonempty(event["id"], "change event id")
        if eid in event_ids:
            raise ValueError(f"duplicate event id: {eid}")
        event_ids.add(eid)
        if event["change_id"] not in change_ids:
            raise ValueError(f"unknown change id in event: {event['change_id']}")
        if event["action"] not in ("resolve", "reopen"):
            raise ValueError(f"unknown change action: {event['action']}")
        nonempty(event["text"], "change event text")
        nonempty(event["by"], "change event author")
        nonempty(event["evidence"], "change event evidence")
        at = parsed_timestamp(event["at"])
        if at < change_raised[event["change_id"]]:
            raise ValueError(f"change event predates its change: {event['id']}")
    check_order(change_events, ("change_id",), "change event")

    questions: list[dict] = items(data["questions"], "questions")
    question_ids: set[str] = set()
    for entry in questions:
        question = fields(entry, {"id", "gate", "lane", "role", "text", "source", "raised_at"})
        qid = nonempty(question["id"], "question id")
        if qid in question_ids:
            raise ValueError(f"duplicate question: {qid}")
        question_ids.add(qid)
        gid, lane_id = scope({"gate": question["gate"], "lane": question["lane"]})
        if question["role"] not in gates[gid][lane_id]["roles"]:
            raise ValueError(f"unknown question role at {gid}/{lane_id}: {question['role']}")
        nonempty(question["text"], "question text")
        source = fields(question["source"], {"artifact", "heading"})
        artifact = nonempty(source["artifact"], "question source artifact")
        if artifact not in gates[gid][lane_id]["artifacts"]:
            raise ValueError(f"question source is not a lane artifact: {artifact}")
        nonempty(source["heading"], "question source heading")
        parsed_timestamp(question["raised_at"])

    answers: list[dict] = items(data["question_answers"], "question_answers")
    for entry in answers:
        answer = fields(
            entry,
            {"id", "question_id", "text", "answered_by", "answered_at", "ai_assisted", "evidence"},
            {"model", "excerpt_sha256"},
        )
        aid = nonempty(answer["id"], "answer id")
        if aid in event_ids:
            raise ValueError(f"duplicate answer id: {aid}")
        event_ids.add(aid)
        if answer["question_id"] not in question_ids:
            raise ValueError(f"unknown question id in answer: {answer['question_id']}")
        nonempty(answer["text"], "answer text")
        nonempty(answer["answered_by"], "answer author")
        answered_at = parsed_timestamp(answer["answered_at"])
        question = next(q for q in questions if q["id"] == answer["question_id"])
        if answered_at < parsed_timestamp(question["raised_at"]):
            raise ValueError(f"answer predates its question: {aid}")
        nonempty(answer["evidence"], "answer evidence")
        if not isinstance(answer["ai_assisted"], bool):
            raise ValueError(f"ai_assisted must be a boolean: {aid}")
        if "excerpt_sha256" in answer:
            digests = items(answer["excerpt_sha256"], "excerpt hashes")
            if any(not isinstance(d, str) or not re.fullmatch(r"[0-9a-f]{64}", d) for d in digests):
                raise ValueError(f"invalid excerpt hash: {aid}")
    check_order(answers, ("question_id",), "question answer", "answered_at")
    return data


def latest(records: list[dict], **match: str) -> dict | None:
    found = [record for record in records if all(record.get(k) == v for k, v in match.items())]
    return found[-1] if found else None


def feedback_state(data: dict, feedback_id: str) -> str:
    event = latest(data["feedback_events"], feedback_id=feedback_id)
    return "open" if event is None or event["action"] == "reopen" else "resolved"


def change_state(data: dict, change_id: str) -> tuple[str, dict | None]:
    event = latest(data["change_events"], change_id=change_id)
    if event is None:
        return "open", None
    return ("open" if event["action"] == "reopen" else "resolved"), event


def evaluate_gate(manifest: Path, gate_id: str, lane: str | None = None) -> dict:
    """Return review readiness for a gate and optionally one swimlane."""
    data = validate(load_manifest(manifest), manifest)
    root = manifest.parent.parent
    gates = {gate["id"]: gate["lanes"] for gate in data["gates"]}
    if gate_id not in gates:
        raise ValueError(f"unknown gate: {gate_id} (known: {', '.join(sorted(gates))})")
    if lane is not None and lane not in gates[gate_id]:
        raise ValueError(
            f"unknown lane: {lane} in {gate_id} (known: {', '.join(sorted(gates[gate_id]))})"
        )
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
        reasons: list[str] = []
        for assumption_id in policy["assumptions"]:
            assumption = next(a for a in data["assumptions"] if a["id"] == assumption_id)
            if dt.date.fromisoformat(assumption["review_by"]) < dt.date.today():
                reasons.append(f"expired assumption: {assumption_id}")
        affected = [
            change
            for change in data["changes"]
            if {"gate": gid, "lane": lane_id} in change["affected"]
        ]
        for change in affected:
            state, _ = change_state(data, change["id"])
            if state == "open":
                reasons.append(f"open change: {change['id']}")
        lane_questions = [q for q in data["questions"] if q["gate"] == gid and q["lane"] == lane_id]
        for question in lane_questions:
            answer = latest(data["question_answers"], question_id=question["id"])
            if answer is None:
                reasons.append(f"unanswered question: {question['id']}")
                continue
            role_decision = latest(data["decisions"], gate=gid, lane=lane_id, role=question["role"])
            if role_decision is None or parsed_timestamp(
                role_decision["recorded_at"]
            ) <= parsed_timestamp(answer["answered_at"]):
                reasons.append(f"question needs reapproval: {question['id']}")
        for role in policy["roles"]:
            decisions = [
                d
                for d in data["decisions"]
                if d["gate"] == gid and d["lane"] == lane_id and d["role"] == role
            ]
            if not decisions:
                reasons.append(f"missing approval: {role}")
                continue
            decision = decisions[-1]
            if decision["decision"] != "approve":
                reasons.append(f"not approved: {role}")
            elif decision["artifact_sha256"] != expected:
                reasons.append(f"stale approval: {role}")
            if any(
                feedback_state(data, comment["id"]) == "open"
                for d in decisions
                for comment in d["feedback"]
            ):
                reasons.append(f"unresolved feedback: {role}")
            for change in affected:
                state, resolved = change_state(data, change["id"])
                if (
                    state == "resolved"
                    and resolved is not None
                    and parsed_timestamp(decision["recorded_at"])
                    <= parsed_timestamp(resolved["at"])
                ):
                    reasons.append(f"reapproval required after change: {change['id']} ({role})")
        for dependency in policy["depends_on"]:
            upstream = status(dependency["gate"], dependency["lane"])
            if not upstream["ready"]:
                reasons.append(f"blocked dependency: {dependency['gate']}/{dependency['lane']}")
        latest_by_role = {
            role: latest(data["decisions"], gate=gid, lane=lane_id, role=role)
            for role in policy["roles"]
        }
        cache[key] = {
            "ready": not reasons,
            "reasons": reasons,
            "required_roles": policy["roles"],
            "artifacts": policy["artifacts"],
            "artifact_sha256": expected,
            "epic": bool(policy.get("epic", False)),
            "assumptions": policy["assumptions"],
            "questions": [q["id"] for q in lane_questions],
            "changes": [c["id"] for c in affected],
            "decisions": {
                role: {
                    "id": d["id"],
                    "decision": d["decision"],
                    "reviewer": d["reviewer"],
                    "recorded_at": d["recorded_at"],
                    "evidence": d["evidence"],
                    "source_commit": d.get("source_commit", ""),
                }
                for role, d in latest_by_role.items()
                if d
            },
            "feedback": [
                {
                    "id": comment["id"],
                    "text": comment["text"],
                    "status": feedback_state(data, comment["id"]),
                }
                for d in data["decisions"]
                if d["gate"] == gid and d["lane"] == lane_id
                for comment in d["feedback"]
            ],
        }
        active.remove(key)
        return cache[key]

    statuses = {lane_id: status(gate_id, lane_id) for lane_id in selected}
    return {
        "gate": gate_id,
        "ready": all(s["ready"] for s in statuses.values()),
        "lanes": statuses,
    }


def portal_view(manifest: Path, role: str) -> dict:
    """Per-role read model: what is pending, what blocks it, what to answer."""
    data = validate(load_manifest(manifest), manifest)
    pending, blocked, context = [], [], []
    for gate in data["gates"]:
        report = evaluate_gate(manifest, gate["id"])
        for lane_id, state in report["lanes"].items():
            if role not in state["required_roles"]:
                context.append(
                    {
                        "gate": gate["id"],
                        "lane": lane_id,
                        "ready": state["ready"],
                        "reasons": state["reasons"],
                    }
                )
                continue
            decision = state["decisions"].get(role)
            entry = {
                "gate": gate["id"],
                "lane": lane_id,
                "ready": state["ready"],
                "reasons": state["reasons"],
                "artifacts": [
                    {"path": path, "sha256": state["artifact_sha256"][path]}
                    for path in state["artifacts"]
                ],
                "decision": decision,
                "other_roles": {
                    name: value for name, value in state["decisions"].items() if name != role
                },
                "questions": state["questions"],
            }
            if state["ready"]:
                context.append(entry)
            elif decision is None or decision["decision"] != "approve":
                pending.append(entry)
            else:
                blocked.append(entry)
    questions = [
        q
        for q in data["questions"]
        if q["role"] == role and latest(data["question_answers"], question_id=q["id"]) is None
    ]
    return {
        "schema_version": 1,
        "product": data["product"],
        "role": role,
        "generated_at": dt.datetime.now(dt.UTC).isoformat(),
        "pending_for_role": pending,
        "blocked_on_others": blocked,
        "context": context,
        "questions_for_role": questions,
    }


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
    output_product: str | None = None,
    search_from: Path | None = None,
    include_cross_cutting: bool = False,
) -> dict | None:
    """Block advancement if configured review scopes or sources are unapproved.

    Returns the per-lane status and manifest root, or None when draft-only.
    """
    if args.draft:
        print("DRAFT ONLY: review gate bypassed explicitly; not approved.", file=sys.stderr)
        return None
    if args.review_manifest is not None:
        manifest = project_path(str(args.review_manifest))
        if not manifest.exists():
            raise SystemExit(f"Review manifest not found: {manifest}")
    else:
        roots = [ROOT]
        for candidate in [sources[0] if sources else None, search_from]:
            if candidate is not None:
                roots.extend(candidate.resolve().parents)
        unique_roots = list(dict.fromkeys(roots))

        def find(name: str | None) -> Path | None:
            if not name:
                return None
            for base in unique_roots:
                candidate = base / "review" / f"{name}.json"
                if candidate.is_file():
                    return candidate
            return None

        manifest = find(output_product) or find(product)
        if manifest is None:
            print("DRAFT ONLY: no review manifest configured; not approved.", file=sys.stderr)
            return None
    try:
        data = validate(load_manifest(manifest), manifest)
    except ValueError as exc:
        raise SystemExit(f"Invalid review manifest {manifest}: {exc}") from exc
    expected_product = output_product or product
    if data["product"] != expected_product:
        raise SystemExit(
            f"Review manifest {manifest} configures product '{data['product']}', "
            f"not '{expected_product}'."
        )
    if partial:
        raise SystemExit(
            f"Review gate {gate_id} needs the complete input set; "
            "partial inputs are exploratory only (use --draft)."
        )
    if not lanes:
        try:
            report = evaluate_gate(manifest, gate_id)
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
        statuses = report["lanes"]
    else:
        available = {gate["id"]: gate["lanes"] for gate in data["gates"]}
        if gate_id not in available:
            raise SystemExit(
                f"Review manifest {manifest} has no gate '{gate_id}' "
                f"(known: {', '.join(sorted(available))})."
            )
        unknown = sorted(set(lanes) - set(available[gate_id]))
        if unknown:
            raise SystemExit(
                f"Review manifest {manifest} has no lane(s) {', '.join(unknown)} "
                f"in gate '{gate_id}' (known: {', '.join(sorted(available[gate_id]))})."
            )
        selected = set(lanes)
        if include_cross_cutting:
            selected |= {
                name for name, policy in available[gate_id].items() if not policy.get("epic", False)
            }
        statuses = {
            lane: evaluate_gate(manifest, gate_id, lane)["lanes"][lane] for lane in sorted(selected)
        }
    root = manifest.parent.parent
    covered = {artifact for state in statuses.values() for artifact in state["artifacts"]}
    for lane, state in statuses.items():
        for source in sources:
            reject_symlink(source, "reviewed input")
            try:
                relative = source.relative_to(root).as_posix()
            except ValueError as exc:
                raise SystemExit(
                    f"Review manifest does not cover input outside its product: {source}"
                ) from exc
            if relative not in covered:
                raise SystemExit(f"Review gate {gate_id} omits input: {relative}")
        if not state["ready"]:
            raise SystemExit(
                f"Review gate {gate_id}/{lane} blocked in {manifest}: {'; '.join(state['reasons'])}"
            )
    return {"root": str(root), "lanes": statuses}


def verify_bundle(context: object, report: dict | None) -> None:
    """Refuse if an input changed between the gate check and prompt assembly."""
    if not report:
        return
    root = Path(report["root"]).resolve()
    bundled = {}
    for item in getattr(context, "sources", []):
        raw = Path(item["path"])
        resolved = (raw if raw.is_absolute() else ROOT / raw).resolve()
        try:
            key = resolved.relative_to(root).as_posix()
        except ValueError:
            key = item["path"]
        bundled[key] = item["sha256"]
    for lane, state in report["lanes"].items():
        changed = [
            path
            for path, digest in bundled.items()
            if path in state["artifact_sha256"] and state["artifact_sha256"][path] != digest
        ]
        if changed:
            raise SystemExit(
                f"Reviewed input changed during generation for {lane}: "
                f"{', '.join(sorted(changed))}. Re-run the gate check."
            )
