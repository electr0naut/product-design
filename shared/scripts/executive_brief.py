"""Validate the narrow, source-linked executive brief format before writing."""

from __future__ import annotations

import re
from pathlib import Path

from workflow_common import display_path, read_text, sha256

SECTIONS = (
    "Ask",
    "Recommendation",
    "Options",
    "Cost",
    "Client Evidence",
    "Main Risk",
    "Deadline",
    "Cost of Saying No",
    "Evidence Cards",
)
CARD_ID = re.compile(r"C[1-9][0-9]*")
REFERENCE = re.compile(r"\[(C[1-9][0-9]*)\]")


def validate_executive_brief(content: str, brd: Path, expected_sha256: str) -> None:
    """Reject structurally invalid or untraceable output, not merely bad prose."""
    source = read_text(brd)
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise SystemExit("BRD changed after prompt assembly; no executive brief was written")
    headings = list(re.finditer(r"(?m)^## ([^\n]+)$", content))
    if not headings or not re.fullmatch(
        r"# Executive Decision Brief: [^\n]+\n\nDraft for human review; not an approval\.\n\n",
        content[: headings[0].start()],
    ):
        raise SystemExit("Executive brief needs an exact draft title and disclaimer")
    if tuple(item.group(1) for item in headings) != SECTIONS:
        raise SystemExit("Executive brief missing or unexpected required section")
    bodies = {
        item.group(1): content[
            item.end() : headings[index + 1].start() if index + 1 < len(headings) else len(content)
        ].strip()
        for index, item in enumerate(headings)
    }
    if any(not bodies[name] for name in SECTIONS):
        raise SystemExit("Executive brief contains an empty required section")
    options = bodies["Options"].splitlines()
    if not 2 <= len(options) <= 3 or any(
        not line.startswith(f"- Option {number}: ") for number, line in enumerate(options, start=1)
    ):
        raise SystemExit("Executive brief needs two or three sequential options")
    decision = "\n".join(bodies[name] for name in SECTIONS[:-1])
    if re.search(r"(?i)\b(?:approved|signed[- ]off|authorized)\b", decision):
        raise SystemExit("Executive brief draft cannot claim an approval or sign-off")
    for name in SECTIONS[:-1]:
        for line in bodies[name].splitlines():
            if not line.strip():
                continue
            raw_refs = re.findall(r"\[C([^\]]*)\]", line)
            if any(not CARD_ID.fullmatch("C" + ref) for ref in raw_refs):
                raise SystemExit("Executive brief has malformed evidence card reference")
            unknown_value = re.fullmatch(r"(?:- Option [1-3]: )?Unknown\.?", line.strip())
            none_yet_value = re.fullmatch(
                r"(?:- Option [1-3]: )?none yet\.?", line.strip(), re.IGNORECASE
            )
            if not REFERENCE.search(line) and unknown_value is None and none_yet_value is None:
                raise SystemExit(
                    f"Executive brief {name} line needs a claim card, Unknown, or 'none yet'"
                )
    cards_text = bodies["Evidence Cards"]
    cards = list(re.finditer(r"(?m)^### (C[1-9][0-9]*)$", cards_text))
    if not cards or cards_text[: cards[0].start()].strip():
        raise SystemExit("Executive brief needs numbered evidence cards")
    ids = [item.group(1) for item in cards]
    if len(set(ids)) != len(ids):
        raise SystemExit("Executive brief has duplicate evidence card IDs")
    source_path = display_path(brd)
    source_lines = set(source.splitlines())
    for index, card in enumerate(cards):
        block = cards_text[
            card.end() : cards[index + 1].start() if index + 1 < len(cards) else len(cards_text)
        ]
        fields = [line for line in block.strip().splitlines() if line.strip()]
        if len(fields) != 3 or not all(
            line.startswith(f"- {field}: ") and line[len(field) + 4 :].strip()
            for line, field in zip(fields, ("Claim", "Source", "Quote"), strict=True)
        ):
            raise SystemExit(f"Executive brief card {card.group(1)} needs Claim, Source and Quote")
        if fields[1][len("- Source: ") :] != source_path:
            raise SystemExit(f"Executive brief card {card.group(1)} cites an unexpected source")
        quote = fields[2][len("- Quote: ") :]
        if quote not in source_lines:
            raise SystemExit(f"Executive brief card {card.group(1)} quote is not in the BRD")
    references = REFERENCE.findall(decision)
    if not references or set(references) != set(ids):
        raise SystemExit("Executive brief has missing or unreferenced evidence cards")
