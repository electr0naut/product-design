#!/usr/bin/env python3
"""Generate a phase-05 technical design from an approved PRD."""

from __future__ import annotations

import argparse

from gate_reviews import add_review_args, maybe_enforce_gate, verify_bundle
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
    add_review_args(parser)
    args = parser.parse_args()

    prd = project_path(args.prd)
    default_out = (
        ROOT / "05-technical-design" / "architecture" / f"{slug_from_path(prd)}-technical-design.md"
    )
    output = project_path(args.out) if args.out else default_out
    statuses = maybe_enforce_gate(
        args,
        slug_from_path(prd),
        "prd-to-design",
        [prd],
        output_product=slug_from_path(output),
        search_from=output,
    )
    context = bundle_documents("PRD", [prd])
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "05-technical-design.md",
        ROOT / "05-technical-design" / "architecture" / "template.md",
        context,
    )
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
