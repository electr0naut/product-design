#!/usr/bin/env python3
"""Generate a phase-03 BRD from the idea canvas and team analyses."""

from __future__ import annotations

import argparse

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
    add_common_args(parser)
    args = parser.parse_args()

    idea = project_path(args.idea)
    slug = slug_from_path(idea)
    analysis = project_path(args.analysis)
    expected_names = {f"{slug}-{role}-analysis.md" for role in ANALYSIS_ROLES}
    analyses = markdown_files(analysis, names=expected_names)
    if not analyses:
        raise SystemExit(
            f"No phase-02 analysis documents for '{slug}' in {display_path(analysis)}."
        )
    sources = [idea] + analyses
    print("Sources:")
    for source in sources:
        print(f"  {display_path(source)}")

    context = bundle_documents("BRD Inputs", sources)
    prompt = compose_prompt(
        PROMPTS / "03-generate-brd.md",
        ROOT / "03-brd" / "templates" / "brd-template.md",
        context,
    )
    default_out = ROOT / "03-brd" / f"{slug}-brd.md"
    output = project_path(args.out) if args.out else default_out
    if args.prompt_only:
        output = output.with_suffix(PROMPT_SUFFIX)
    exit_status([generate(prompt, output, args.prompt_only, args.claude_bin, args.force)])


if __name__ == "__main__":
    main()
