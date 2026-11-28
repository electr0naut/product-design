#!/usr/bin/env python3
"""Generate a phase-05 technical design from an approved PRD."""

from __future__ import annotations

import argparse

from gate_reviews import add_review_args, generation_receipt, maybe_enforce_gate, verify_bundle
from workflow_common import (
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    add_common_args,
    bundle_documents,
    check_draft_out,
    compose_prompt,
    draft_path,
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
    check_draft_out(output, draft=args.draft, explicit=args.out is not None)
    statuses = maybe_enforce_gate(
        args,
        slug_from_path(prd),
        "prd-to-design",
        [prd],
        output_product=slug_from_path(output),
        search_from=output,
    )
    output = draft_path(output) if args.draft else output
    context = bundle_documents("PRD", [prd])
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "05-technical-design.md",
        ROOT / "05-technical-design" / "architecture" / "template.md",
        context,
    )
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    snapshot = None if args.prompt_only else generation_receipt(statuses, output)
    exit_status(
        [
            generate(
                prompt,
                output,
                args.prompt_only,
                args.claude_bin,
                args.force,
                snapshot=snapshot,
            )
        ]
    )


if __name__ == "__main__":
    main()
