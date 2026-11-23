"""Validate legal drafts against the exact BRD supplied to the prompt."""

from __future__ import annotations

import re
from pathlib import Path

from workflow_common import display_path, read_text, sha256

SECTIONS = (
    "Claim Relied On",
    "Citation",
    "Jurisdiction",
    "Main Legal Risk",
    "Decision Needed",
    "Evidence Cards",
)
CARD_ID = re.compile(r"C[1-9][0-9]*")
REFERENCE = re.compile(r"\[(C[1-9][0-9]*)\]")
DECLARATIVE_SECTIONS = ("Citation", "Jurisdiction")
CITATION_TOKEN = re.compile(
    r"(?:[A-Z][A-Za-z0-9./-]*\s*)?(?:Art|§|Section|Clause)\.?\s*[A-Za-z0-9./()-]+"
)
NAME_TOKEN = re.compile(r"[A-Z][A-Za-z]+|[A-Z]{2,}")


def strip_sentence_period(token: str) -> str:
    """Drop a sentence-ending full stop so it cannot split an otherwise equal token."""
    return token[:-1] if token.endswith(".") and not token.endswith("..") else token


def quote_tokens(quote: str) -> set[str]:
    """Every value a quote can support, extracted once and compared as complete tokens."""
    return {strip_sentence_period(token) for token in CITATION_TOKEN.findall(quote)} | {
        strip_sentence_period(token) for token in NAME_TOKEN.findall(quote)
    }


def validate_legal_brief(content: str, brd: Path, expected_sha256: str) -> None:
    """Reject unsourced claims, citations and jurisdictions before any output is written."""
    source = read_text(brd)
    if sha256(source.encode("utf-8")) != expected_sha256:
        raise SystemExit("BRD changed after prompt assembly; no legal brief was written")
    headings = list(re.finditer(r"(?m)^## ([^\n]+)$", content))
    if not headings or not re.fullmatch(
        r"# Legal Decision Brief: [^\n]+\n\nDraft for human review; not a legal conclusion\.\n\n",
        content[: headings[0].start()],
    ):
        raise SystemExit("Legal brief needs an exact draft title and disclaimer")
    if tuple(item.group(1) for item in headings) != SECTIONS:
        raise SystemExit("Legal brief missing or unexpected required section")
    bodies = {
        item.group(1): content[
            item.end() : headings[index + 1].start() if index + 1 < len(headings) else len(content)
        ].strip()
        for index, item in enumerate(headings)
    }
    if any(not bodies[name] for name in SECTIONS):
        raise SystemExit("Legal brief contains an empty required section")
    decision = "\n".join(bodies[name] for name in SECTIONS[:-1])
    if re.search(
        r"(?i)\b(?:approved|signed[- ]off|authorized|approval\s+(?:granted|confirmed|received|obtained))\b",
        decision,
    ):
        raise SystemExit("Legal brief draft cannot claim an approval or sign-off")
    cards_text = bodies["Evidence Cards"]
    cards = list(re.finditer(r"(?m)^### (C[1-9][0-9]*)$", cards_text))
    if not cards or cards_text[: cards[0].start()].strip():
        raise SystemExit("Legal brief needs numbered evidence cards")
    ids = [item.group(1) for item in cards]
    if len(set(ids)) != len(ids):
        raise SystemExit("Legal brief has duplicate evidence card IDs")
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
            raise SystemExit(f"Legal brief card {card.group(1)} needs Claim, Source and Quote")
        if fields[1][len("- Source: ") :] != source_path:
            raise SystemExit(f"Legal brief card {card.group(1)} cites an unexpected source")
        quote = fields[2][len("- Quote: ") :]
        if quote not in source_lines:
            raise SystemExit(f"Legal brief card {card.group(1)} quote is not in the BRD")
        quotes[card.group(1)] = quote
        claim = fields[0][len("- Claim: ") :]
        if re.search(
            r"(?i)\b(?:approved|signed[- ]off|authorized|approval\s+(?:granted|confirmed|received|obtained))\b",
            claim,
        ):
            raise SystemExit(
                f"Legal brief card {card.group(1)} claim cannot assert an approval or sign-off"
            )
    references: list[str] = []
    for name in SECTIONS[:-1]:
        body = bodies[name]
        if body == "Unknown.":
            continue
        if "Unknown" in body:
            raise SystemExit("Legal brief cannot mix Unknown with an assertion")
        for line in body.splitlines():
            if not line.strip():
                continue
            raw_refs = re.findall(r"\[C([^\]]*)\]", line)
            if any(not CARD_ID.fullmatch("C" + ref) for ref in raw_refs):
                raise SystemExit("Legal brief has malformed evidence card reference")
            refs = REFERENCE.findall(line)
            if not refs:
                raise SystemExit(f"Legal brief {name} line needs an existing claim card")
            if any(ref not in quotes for ref in refs):
                raise SystemExit(f"Legal brief {name} line needs an existing claim card")
            references.extend(refs)
            plain = REFERENCE.sub("", line)
            if name in DECLARATIVE_SECTIONS:
                declared = re.sub(r"[\s.]*$", "", plain).strip()
                if not declared:
                    raise SystemExit(f"Legal brief {name} line needs a declared value")
                parts = quote_tokens(declared)
                supported: set[str] = set()
                for ref in refs:
                    supported |= quote_tokens(quotes[ref])
                if not parts or not parts <= supported:
                    raise SystemExit(
                        f"Legal brief {name} value {declared!r} is not in a cited BRD quote"
                    )
                continue
            for token in re.findall(
                r"(?:[A-Z][A-Za-z0-9./-]*\s*)?(?:Art|§|Section|Clause)\.?\s*[A-Za-z0-9./()-]+(?![A-Za-z0-9./()-])|[A-Z]{2,}",
                plain,
            ):
                if not any(
                    strip_sentence_period(token) == strip_sentence_period(quote_token)
                    for ref in refs
                    for quote_token in re.findall(
                        r"(?:[A-Z][A-Za-z0-9./-]*\s*)?(?:Art|§|Section|Clause)\.?\s*[A-Za-z0-9./()-]+(?![A-Za-z0-9./()-])|[A-Z]{2,}(?![A-Za-z])",
                        quotes[ref],
                    )
                ):
                    raise SystemExit(
                        f"Legal brief citation or jurisdiction {token!r} is not in a cited BRD quote"
                    )
    if set(references) != set(ids):
        raise SystemExit("Legal brief has unreferenced evidence cards")
