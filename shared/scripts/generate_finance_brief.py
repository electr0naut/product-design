#!/usr/bin/env python3
"""Draft a finance decision brief from one reviewed BRD."""

from __future__ import annotations

import argparse

from finance_brief import validate_finance_brief
from gate_reviews import add_review_args, generation_receipt, maybe_enforce_gate, verify_bundle
from workflow_common import (
    PROMPT_SUFFIX,
    PROMPTS,
    ROOT,
    add_common_args,
    bundle_documents,
    canonical_path,
    compose_prompt,
    display_path,
    exit_status,
    generate,
    project_path,
    read_text,
    slug_from_path,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--brd", required=True, help="The named BRD input")
    parser.add_argument("--out", help="Visibly draft .draft.md output path")
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    brd = project_path(args.brd)
    slug = slug_from_path(brd)
    output = (
        project_path(args.out) if args.out else ROOT / "03-brd" / "finance" / f"{slug}.draft.md"
    )
    if not output.name.endswith(".draft.md"):
        parser.error("Finance briefs must be written to a .draft.md path")
    canonical = canonical_path(output)
    if slug_from_path(canonical) != slug:
        parser.error("Output product must match the BRD product")
    read_text(brd)
    statuses = maybe_enforce_gate(
        args,
        slug,
        "brd-to-prd",
        [brd],
        output_product=slug,
        search_from=canonical,
    )
    context = bundle_documents("BRD", [brd])
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "03-finance-brief.md",
        ROOT / "03-brd" / "templates" / "finance-brief-template.md",
        context,
    )
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    snapshot = generation_receipt(statuses, output)

    def validate(content: str) -> None:
        validate_finance_brief(content, brd, context.sources[0]["sha256"])

    print(f"Source: {display_path(brd)}")
    exit_status(
        [
            generate(
                prompt,
                output,
                args.prompt_only,
                args.claude_bin,
                args.force,
                snapshot=snapshot,
                validate=validate,
            )
        ]
    )


if __name__ == "__main__":
    main()
