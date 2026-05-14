#!/usr/bin/env python3
"""Generate a phase-04 PRD from an approved BRD."""

from __future__ import annotations

import argparse

from workflow_common import (
    PROMPTS,
    ROOT,
    add_common_args,
    bundle_documents,
    compose_prompt,
    generate,
    project_path,
    slug_from_path,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brd", required=True, help="Path to the approved BRD.")
    parser.add_argument("--out", help="Output PRD path.")
    add_common_args(parser)
    args = parser.parse_args()

    brd = project_path(args.brd)
    context = bundle_documents("BRD", [brd])
    prompt = compose_prompt(
        PROMPTS / "04-generate-prd.md",
        ROOT / "04-prd" / "templates" / "prd-template.md",
        context,
    )
    default_out = ROOT / "04-prd" / f"{slug_from_path(brd)}-prd.md"
    output = project_path(args.out) if args.out else default_out
    if args.prompt_only:
        output = output.with_suffix(".prompt.md")
    generate(prompt, output, args.prompt_only, args.claude_bin)


if __name__ == "__main__":
    main()
