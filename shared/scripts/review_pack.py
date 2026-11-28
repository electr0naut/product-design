#!/usr/bin/env python3
"""Write a review pack for one role: what to decide, what changed, what is open.

Markdown only; it records nothing. The pack is derived from the same evaluator as
`check_gate.py`, so it cannot disagree with the gate.
"""

from __future__ import annotations

import argparse
import datetime as dt

from gate_reviews import (
    change_state,
    evaluate_gate,
    latest,
    load_manifest,
    validate,
)
from workflow_common import display_path, project_path, write_text


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--manifest", required=True, help="review/<product>.json")
    parser.add_argument("--role", required=True, help="Role the pack is written for")
    parser.add_argument("--lane", help="Only this lane; default: every lane for the role")
    parser.add_argument("--out", help="Output path. Default: review-packs/<product>-<role>.md")
    args = parser.parse_args()

    manifest = project_path(args.manifest)
    try:
        data = validate(load_manifest(manifest), manifest)
    except ValueError as exc:
        print(f"Invalid review manifest: {exc}")
        return 2
    packs = []
    for gate in data["gates"]:
        for lane_id, policy in gate["lanes"].items():
            if args.role not in policy["roles"]:
                continue
            if args.lane and lane_id != args.lane:
                continue
            state = evaluate_gate(manifest, gate["id"], lane_id)["lanes"][lane_id]
            packs.append((gate["id"], lane_id, state))
    if not packs:
        print(f"No lane requires role '{args.role}'" + (f" in {args.lane}" if args.lane else ""))
        return 1

    out = (
        project_path(args.out)
        if args.out
        else manifest.parent.parent / "review-packs" / f"{data['product']}-{args.role}.md"
    )
    write_text(out, render(data, args.role, packs))
    print(f"Review pack: {display_path(out)}")
    return 0


def render(data: dict, role: str, packs: list[tuple[str, str, dict]]) -> str:
    today = dt.date.today()
    problem_ids = {q["id"] for q in data["questions"] if q["role"] == role}
    lines = [
        f"# Review Pack: {data['product']} — {role}",
        "",
        f"Generated on {today.isoformat()} from the review manifest. This pack records nothing;",
        "it is a reading aid. Approval binds to the artifact hashes below.",
        "",
        "## Decision requested",
        "",
    ]
    for gate, lane, state in packs:
        label = "READY" if state["ready"] else "BLOCKED"
        lines.append(f"### {gate} / {lane} — {label}")
        lines.append("")
        if state["reasons"]:
            lines.append("Blocking reasons:")
            lines += [f"- {reason}" for reason in state["reasons"]]
        else:
            lines.append("No blocking reasons.")
        lines.append("")
        lines.append("| Artifact | SHA-256 | Last reviewed by you |")
        lines.append("|----------|---------|----------------------|")
        record = latest(data["decisions"], gate=gate, lane=lane, role=role)
        for path, digest in state["artifact_sha256"].items():
            if record is None:
                seen = "not reviewed"
            elif record["artifact_sha256"].get(path) == digest:
                seen = "current"
            else:
                seen = "stale"
            lines.append(f"| `{path}` | `{digest}` | {seen} |")
        lines.append("")
        if record:
            lines.append(
                f"Your latest decision: **{record['decision']}** on {record['recorded_at']} "
                f"({record['reviewer']}); reviewed commit "
                f"`{record.get('source_commit') or 'unknown'}`."
            )
        else:
            lines.append("You have not recorded a decision for this lane.")
        other = [name for name in state["decisions"] if name != role]
        if other:
            lines.append("")
            lines.append("Other roles:")
            for name in other:
                item = state["decisions"][name]
                lines.append(
                    f"- {name}: {item['decision']} by {item['reviewer']} on {item['recorded_at']}"
                )
        if state.get("stale_roles"):
            lines.append("")
            lines.append(f"Stale approvals: {', '.join(state['stale_roles'])}")
        lines.append("")

    questions = [q for q in data["questions"] if q["id"] in problem_ids]
    lines += ["## Open questions for you", ""]
    if questions:
        for question in questions:
            answer = latest(data["question_answers"], question_id=question["id"])
            status = "answered, awaiting your reapproval" if answer else "unanswered"
            lines.append(
                f"- **{question['id']}** ({status}): {question['text']} "
                f"— source `{question['source']['artifact']}` §{question['source']['heading']}"
            )
    else:
        lines.append("None.")
    lines.append("")

    relevant = {(gate, lane) for gate, lane, _ in packs}
    affected_changes = [
        change
        for change in data["changes"]
        if any((ref["gate"], ref["lane"]) in relevant for ref in change["affected"])
    ]
    lines += ["## Changes affecting these lanes", ""]
    if affected_changes:
        for change in affected_changes:
            state, event = change_state(data, change["id"])
            detail = f" (resolved {event['at']})" if state == "resolved" and event else ""
            lines.append(f"- {change['id']}: {change['source']} — {state}{detail}")
    else:
        lines.append("None.")
    lines.append("")

    assumptions = {aid for _, _, state in packs for aid in state["assumptions"]}
    lines += ["## Assumptions", ""]
    rows = [a for a in data["assumptions"] if a["id"] in assumptions]
    if rows:
        for assumption in rows:
            expiry = dt.date.fromisoformat(assumption["review_by"])
            days = (expiry - today).days
            lines.append(
                f"- {assumption['id']}: {assumption['statement']} "
                f"(review by {assumption['review_by']}, {days} days)"
            )
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    raise SystemExit(main())
