#!/usr/bin/env python3
"""Generate a phase-04 PRD from an approved BRD."""

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
    parser.add_argument("--brd", required=True, help="Path to the approved BRD.")
    parser.add_argument("--out", help="Output PRD path.")
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    brd = project_path(args.brd)
    default_out = ROOT / "04-prd" / f"{slug_from_path(brd)}-prd.md"
    output = project_path(args.out) if args.out else default_out
    statuses = maybe_enforce_gate(
        args,
        slug_from_path(brd),
        "brd-to-prd",
        [brd],
        output_product=slug_from_path(output),
        search_from=output,
    )
    context = bundle_documents("BRD", [brd])
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "04-generate-prd.md",
        ROOT / "04-prd" / "templates" / "prd-template.md",
        context,
    )
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
