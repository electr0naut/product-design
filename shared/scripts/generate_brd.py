#!/usr/bin/env python3
"""Generate a phase-03 BRD from the idea canvas and team analyses."""

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
    display_path,
    exit_status,
    generate,
    markdown_files,
    project_path,
    slug_from_path,
)

ANALYSIS_ROLES = (
    "bizdev",
    "compliance",
    "finance",
    "legal",
    "operations",
    "product",
    "risk",
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--idea", required=True, help="Path to the completed idea canvas.")
    parser.add_argument("--analysis", default="02-analysis", help="Analysis directory or file.")
    parser.add_argument("--out", help="Output BRD path.")
    parser.add_argument(
        "--allow-partial-analysis",
        action="store_true",
        help="Allow exploratory BRD generation with fewer than seven analyses.",
    )
    add_common_args(parser)
    add_review_args(parser)
    args = parser.parse_args()

    idea = project_path(args.idea)
    slug = slug_from_path(idea)
    analysis = project_path(args.analysis)
    expected_names = {f"{slug}-{role}-analysis.md" for role in ANALYSIS_ROLES}
    analyses = markdown_files(analysis, names=expected_names)
    found = {p.name for p in analyses}
    duplicates = sorted(name for name in found if sum(p.name == name for p in analyses) > 1)
    if duplicates:
        raise SystemExit(f"Duplicate phase-02 analyses for '{slug}': {', '.join(duplicates)}.")
    missing = sorted(expected_names - found)
    if missing and not args.allow_partial_analysis:
        raise SystemExit(
            f"Missing phase-02 analyses for '{slug}': {', '.join(missing)}. "
            "Use --allow-partial-analysis for exploratory work."
        )
    if not analyses:
        raise SystemExit(
            f"No phase-02 analysis documents for '{slug}' in {display_path(analysis)}."
        )
    sources = [idea] + analyses
    default_out = ROOT / "03-brd" / f"{slug}-brd.md"
    output = project_path(args.out) if args.out else default_out
    statuses = maybe_enforce_gate(
        args,
        slug,
        "analysis-to-brd",
        sources,
        partial=bool(missing),
        output_product=slug_from_path(output),
        search_from=output,
    )
    print("Sources:")
    for source in sources:
        print(f"  {display_path(source)}")

    context = bundle_documents("BRD Inputs", sources)
    verify_bundle(context, statuses)
    prompt = compose_prompt(
        PROMPTS / "03-generate-brd.md",
        ROOT / "03-brd" / "templates" / "brd-template.md",
        context,
    )
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
