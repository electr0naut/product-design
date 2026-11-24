#!/usr/bin/env python3
"""Generate compliance decision brief from BRD."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "05-compliance-brief.md"
TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "03-brd"
    / "templates"
    / "compliance-brief-template.md"
)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate compliance decision brief")
    parser.add_argument("brd", type=Path, help="Path to BRD")
    parser.add_argument("output", type=Path, help="Output path")
    parser.add_argument(
        "--claude-bin", type=Path, default=Path("claude"), help="Path to claude binary"
    )
    args = parser.parse_args()

    brd = args.brd.read_text(encoding="utf-8")
    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    full_prompt = f"{prompt}\n\nBRD:\n{brd}\n\nTemplate:\n{template}"

    result = subprocess.run(
        [str(args.claude_bin), "-p", full_prompt],
        capture_output=True,
        text=True,
        check=True,
    )

    args.output.write_text(result.stdout, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
