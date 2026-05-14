#!/usr/bin/env python3
"""Generate implementation scaffold instructions from technical design."""

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
    parser.add_argument(
        "--technical-design",
        required=True,
        help="Path to the approved technical design.",
    )
    parser.add_argument("--out", help="Output implementation scaffold path.")
    add_common_args(parser)
    args = parser.parse_args()

    technical_design = project_path(args.technical_design)
    context = bundle_documents("Technical Design", [technical_design])
    prompt = compose_prompt(PROMPTS / "06-scaffold-code.md", None, context)
    default_out = (
        ROOT
        / "06-implementation"
        / f"{slug_from_path(technical_design)}-implementation-plan.md"
    )
    output = project_path(args.out) if args.out else default_out
    if args.prompt_only:
        output = output.with_suffix(".prompt.md")
    generate(prompt, output, args.prompt_only, args.claude_bin)


if __name__ == "__main__":
    main()
