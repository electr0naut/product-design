#!/usr/bin/env python3
"""Generate all phase-02 team analyses from an idea canvas."""

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


ROLES = {
    "bizdev": ("02-analysis-bizdev.md", "business-development-template.md", "business-development"),
    "compliance": ("02-analysis-compliance.md", "compliance-template.md", "compliance"),
    "finance": ("02-analysis-finance.md", "finance-template.md", "finance"),
    "legal": ("02-analysis-legal.md", "legal-template.md", "legal"),
    "operations": ("02-analysis-operations.md", "operations-template.md", "operations"),
    "product": ("02-analysis-product.md", "product-template.md", "product"),
    "risk": ("02-analysis-risk.md", "risk-template.md", "risk"),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--idea", required=True, help="Path to the completed idea canvas.")
    parser.add_argument("--out-dir", default="02-analysis", help="Output directory.")
    parser.add_argument("--role", choices=sorted(ROLES), help="Generate one role only.")
    add_common_args(parser)
    args = parser.parse_args()

    idea = project_path(args.idea)
    slug = slug_from_path(idea)
    context = bundle_documents("Idea Canvas", [idea])
    roles = {args.role: ROLES[args.role]} if args.role else ROLES

    for role, (prompt_name, template_name, folder) in roles.items():
        prompt = compose_prompt(
            PROMPTS / prompt_name,
            ROOT / "02-analysis" / "templates" / template_name,
            context,
        )
        suffix = ".prompt.md" if args.prompt_only else ".md"
        output = project_path(args.out_dir) / folder / f"{slug}-{role}-analysis{suffix}"
        generate(prompt, output, args.prompt_only, args.claude_bin)


if __name__ == "__main__":
    main()
