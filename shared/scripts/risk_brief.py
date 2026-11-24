"""Risk decision brief: validate provenance and decision-layer claims."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTIONS = (
    "Risk Categories",
    "Risk Models",
    "Risk Limits",
    "Risk Controls",
    "Risk Measurement",
    "Main Uncertainty",
    "Decision Needed",
    "Evidence Cards",
)


def split_sections(text: str) -> dict[str, str]:
    """Split markdown into sections by ## headings."""
    parts = re.split(r"(?m)^## ", text)
    bodies: dict[str, str] = {}
    for part in parts[1:]:
        name, _, body = part.partition("\n")
        bodies[name.strip()] = body.strip()
    return bodies


def validate(brief: str, brd: str, brd_path: str) -> None:
    """Validate risk brief against BRD."""
    bodies = split_sections(brief)
    missing = [name for name in SECTIONS if name not in bodies]
    if missing:
        raise SystemExit(f"Risk brief missing sections: {', '.join(missing)}")

    # Check for approval claims
    approval_pattern = re.compile(r"\b(approved|approved\.|approval|approved for)\b", re.IGNORECASE)
    for name in SECTIONS[:-1]:
        if approval_pattern.search(bodies[name]):
            raise SystemExit(f"Risk brief {name} cannot claim approval in a draft")

    # Check evidence cards structure
    cards_text = bodies["Evidence Cards"]
    cards = list(re.finditer(r"(?m)^### (C[1-9][0-9]*)$", cards_text))

    # Allow empty evidence cards if all decision layer fields are Unknown/none yet
    all_unknown_or_none = all(
        re.fullmatch(r"(?:Unknown|none yet)\.?", bodies[name].strip(), re.IGNORECASE)
        for name in SECTIONS[:-1]
    )
    if all_unknown_or_none:
        # When all fields are Unknown/none yet, Evidence Cards body must be empty
        if cards_text.strip():
            raise SystemExit(
                "Risk brief with all Unknown/none yet fields must have empty Evidence Cards"
            )
    elif not cards or cards_text[: cards[0].start()].strip():
        raise SystemExit("Risk brief needs numbered evidence cards")

    ids = [item.group(1) for item in cards]
    if len(set(ids)) != len(ids):
        raise SystemExit("Risk brief evidence card ids must be unique")

    # Parse evidence cards
    card_bodies: dict[str, str] = {}
    for idx, match in enumerate(cards):
        start = match.end()
        end = cards[idx + 1].start() if idx + 1 < len(cards) else len(cards_text)
        card_bodies[match.group(1)] = cards_text[start:end].strip()

    # Validate each card has Claim, Source, Quote
    for cid, body in card_bodies.items():
        fields = re.findall(r"(?m)^- (Claim|Source|Quote): (.*)$", body)
        field_names = [f[0] for f in fields]
        if field_names != ["Claim", "Source", "Quote"]:
            raise SystemExit(f"Risk brief {cid} needs Claim, Source, Quote in order")
        source = next(f[1] for f in fields if f[0] == "Source")
        if source != brd_path:
            raise SystemExit(f"Risk brief {cid} Source must be {brd_path}")
        quote = next(f[1] for f in fields if f[0] == "Quote")
        if quote not in brd:
            raise SystemExit(f"Risk brief {cid} Quote not found in BRD")

    # Validate decision layer citations
    for name in SECTIONS[:-1]:
        body = bodies[name]
        # Check for Unknown/none yet mixed with assertions
        for line in body.splitlines():
            line = line.strip()
            if not line:
                continue
            if re.fullmatch(r"(?:Unknown|none yet)\.?", line, re.IGNORECASE):
                continue
            if re.search(r"\b(Unknown|none yet)\b", line, re.IGNORECASE):
                raise SystemExit(f"Risk brief {name} cannot mix Unknown/none yet with assertions")
            # Check for card citations
            cites = re.findall(r"\[C[1-9][0-9]*\]", line)
            if not cites:
                raise SystemExit(f"Risk brief {name} line needs evidence card citation")
            # Check cited cards exist
            for cite in cites:
                cid = cite[1:-1]
                if cid not in card_bodies:
                    raise SystemExit(f"Risk brief cites {cid} but card not found")

    # Check for unquoted claims (lines with citations but no matching quote)
    for name in SECTIONS[:-1]:
        body = bodies[name]
        for line in body.splitlines():
            line = line.strip()
            if not line or re.fullmatch(r"(?:Unknown|none yet)\.?", line, re.IGNORECASE):
                continue
            cites = re.findall(r"\[(C[1-9][0-9]*)\]", line)
            for cid in cites:
                quote = re.search(r"(?m)^- Quote: (.*)$", card_bodies[cid])
                if quote:
                    quote_text = quote.group(1)
                    # Check that non-trivial content from the line appears in the quote
                    # (excluding citations and common words)
                    line_content = re.sub(r"\[C[1-9][0-9]*\]", "", line).strip()
                    # Extract meaningful words (not just citations or punctuation)
                    words = re.findall(r"\b[a-zA-Z]{3,}\b", line_content)
                    if words:
                        # At least one meaningful word should be in the quote
                        if not any(word.lower() in quote_text.lower() for word in words):
                            raise SystemExit(
                                f"Risk brief {name} cites {cid} but no content matches quote"
                            )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate risk decision brief")
    parser.add_argument("brief", type=Path, help="Path to risk brief")
    parser.add_argument("brd", type=Path, help="Path to BRD")
    parser.add_argument("--output", type=Path, help="Output path (optional)")
    args = parser.parse_args()

    brief = args.brief.read_text(encoding="utf-8")
    brd = args.brd.read_text(encoding="utf-8")
    brd_path = str(args.brd)

    validate(brief, brd, brd_path)

    if args.output:
        args.output.write_text(brief, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
