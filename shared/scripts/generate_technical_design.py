#!/usr/bin/env python3
"""Generate a phase-05 technical design from an approved PRD."""

from __future__ import annotations

import argparse

from workflow_common import (
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    add_common_args,
    bundle_documents,
    compose_prompt,
    exit_status,
    generate,
    project_path,
    slug_from_path,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prd", required=True, help="Path to the approved PRD.")
    parser.add_argument("--out", help="Output technical design path.")
    add_common_args(parser)
    args = parser.parse_args()

    prd = project_path(args.prd)
    context = bundle_documents("PRD", [prd])
    prompt = compose_prompt(
        PROMPTS / "05-technical-design.md",
        ROOT / "05-technical-design" / "architecture" / "template.md",
        context,
    )
    default_out = (
        ROOT
        / "05-technical-design"
        / "architecture"
        / f"{slug_from_path(prd)}-technical-design.md"
    )
    output = project_path(args.out) if args.out else default_out
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
