"""Validate technology/security drafts against the exact BRD supplied to the prompt."""

from __future__ import annotations

import re
from pathlib import Path

from workflow_common import display_path, read_text, sha256

SECTIONS = (
    "Build Options",
    "Custody/Keys",
    "Venue Connectivity",
    "Security Risks",
    "Hard Blockers",
    "Main Uncertainty",
    "Decision Needed",
    "Evidence Cards",
)
CARD_ID = re.compile(r"C[1-9][0-9]*")
REFERENCE = re.compile(r"\[(C[1-9][0-9]*)\]")


def validate_technology_security_brief(content: str, brd: Path, expected_sha256: str) -> None:
    """Reject unsourced claims and technical terms before any output is written."""
    source = read_text(brd)
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise SystemExit(
            "BRD changed after prompt assembly; no technology/security brief was written"
        )
    headings = list(re.finditer(r"(?m)^## ([^\n]+)$", content))
    if not headings or not re.fullmatch(
        r"# Technology and Security Decision Brief: [^\n]+\n\nDraft for human review; not an approval\.\n\n",
        content[: headings[0].start()],
    ):
        raise SystemExit("Technology/security brief needs an exact draft title and disclaimer")
    if tuple(item.group(1) for item in headings) != SECTIONS:
        raise SystemExit("Technology/security brief missing or unexpected required section")
    bodies = {
        item.group(1): content[
            item.end() : headings[index + 1].start() if index + 1 < len(headings) else len(content)
        ].strip()
        for index, item in enumerate(headings)
    }
    if any(not bodies[name] for name in SECTIONS):
        raise SystemExit("Technology/security brief contains an empty required section")
    decision = "\n".join(bodies[name] for name in SECTIONS[:-1])
    if re.search(
        r"(?i)\b(?:approved|signed[- ]off|authorized|approval\s+(?:granted|confirmed|received|obtained))\b",
        decision,
    ):
        raise SystemExit("Technology/security brief draft cannot claim an approval or sign-off")
    cards_text = bodies["Evidence Cards"]
    cards = list(re.finditer(r"(?m)^### (C[1-9][0-9]*)$", cards_text))
    if not cards or cards_text[: cards[0].start()].strip():
        raise SystemExit("Technology/security brief needs numbered evidence cards")
    ids = [item.group(1) for item in cards]
    if len(set(ids)) != len(ids):
        raise SystemExit("Technology/security brief has duplicate evidence card IDs")
    quotes: dict[str, str] = {}
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
            raise SystemExit(
                f"Technology/security brief card {card.group(1)} needs Claim, Source and Quote"
            )
        if fields[1][len("- Source: ") :] != source_path:
            raise SystemExit(
                f"Technology/security brief card {card.group(1)} cites an unexpected source"
            )
        quote = fields[2][len("- Quote: ") :]
        if quote not in source_lines:
            raise SystemExit(
                f"Technology/security brief card {card.group(1)} quote is not in the BRD"
            )
        quotes[card.group(1)] = quote
    references: list[str] = []
    for name in SECTIONS[:-1]:
        for line in bodies[name].splitlines():
            if not line.strip():
                continue
            raw_refs = re.findall(r"\[C([^\]]*)\]", line)
            if any(not CARD_ID.fullmatch("C" + ref) for ref in raw_refs):
                raise SystemExit("Technology/security brief has malformed evidence card reference")
            refs = REFERENCE.findall(line)
            unknown_value = re.fullmatch(r"Unknown\.?", line.strip())
            none_yet_value = re.fullmatch(r"none yet\.?", line.strip(), re.IGNORECASE)
            if not refs and unknown_value is None and none_yet_value is None:
                raise SystemExit(
                    f"Technology/security brief {name} line needs a claim card, Unknown, or 'none yet'"
                )
            if not refs:
                continue
            if any(ref not in quotes for ref in refs):
                raise SystemExit(
                    f"Technology/security brief {name} line needs an existing claim card"
                )
            references.extend(refs)
            if "Unknown" in line or "none yet" in line.lower():
                raise SystemExit(
                    "Technology/security brief cannot mix Unknown/none yet with an assertion"
                )
    if set(references) != set(ids):
        raise SystemExit("Technology/security brief has unreferenced evidence cards")
